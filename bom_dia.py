#!/usr/bin/env python3
"""bom_dia.py — escreve o resumo da manhã a partir do estado.json.

1) Por regra fixa (sem IA): o que os robôs fizeram desde ontem, o que espera você
   e a 1 coisa a fazer primeiro.
2) Opcional (--ollama): se houver Ollama rodando NESTA máquina, pede ao modelo local
   para deixar o texto mais natural. Se o Ollama não responder, fica o texto da regra.

Uso:
    python3 bom_dia.py                    # grava bom_dia.txt e mostra na tela
    python3 bom_dia.py --ollama           # tenta melhorar com o modelo local do config.json
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def _quando(texto: str | None) -> datetime | None:
    if not texto:
        return None
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        return None


def resumo_por_regra(estado: dict, agora: datetime | None = None) -> str:
    nome = estado.get("nome") or "você"
    sistemas = estado.get("sistemas", [])
    esperando = estado.get("esperando", [])
    agora = agora or datetime.now().astimezone()
    desde = agora - timedelta(hours=24)

    recentes = [s for s in sistemas if (q := _quando(s.get("ultima"))) and q >= desde]
    ok = [s for s in recentes if s.get("estado") == "ok"]
    falhas = [s for s in sistemas if s.get("estado") == "falhou"]
    hora = agora.hour
    saudacao = "Bom dia" if hora < 12 else ("Boa tarde" if hora < 18 else "Boa noite")

    def n(qtd: int, um: str, varios: str) -> str:
        return f"{qtd} {um if qtd == 1 else varios}"

    linhas = [f"{saudacao}, {nome}."]
    if sistemas:
        linhas.append(f"No painel: {n(len(sistemas), 'sistema', 'sistemas')}, "
                      f"{n(sum(1 for s in sistemas if s.get('estado') == 'ok'), 'ok', 'ok')} e {len(falhas)} com falha.")
    if recentes:
        linhas.append(f"Nas últimas 24 horas, {n(len(recentes), 'robô trabalhou', 'robôs trabalharam')} e "
                      f"{n(len(ok), 'terminou bem', 'terminaram bem')}.")
    else:
        linhas.append("Não vi nenhum robô trabalhando nas últimas 24 horas.")
    if falhas:
        nomes = ", ".join(s["nome"] for s in falhas[:3])
        linhas.append(f"Com falha: {nomes}" + (f" e mais {len(falhas) - 3}." if len(falhas) > 3 else "."))

    falhas_esp = [e for e in esperando if e.get("tipo") == "falha"]
    pend = [e for e in esperando if e.get("tipo") == "pendencia"]
    filas = [e for e in esperando if e.get("tipo") == "fila"]
    if esperando:
        partes = [p for p in (n(len(falhas_esp), "falha", "falhas") if falhas_esp else "",
                              n(len(pend), "pendência", "pendências") if pend else "",
                              n(len(filas), "fila", "filas") if filas else "") if p]
        lista = partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " e " + partes[-1]
        linhas.append(f"Esperando você: {n(len(esperando), 'item', 'itens')} ({lista}).")
    else:
        linhas.append("Nada esperando você. Dia livre para criar.")

    if falhas_esp:
        primeiro = f"olhar por que {falhas_esp[0]['titulo'].removesuffix(' falhou')} falhou"
    elif pend:
        primeiro = pend[0]["titulo"]
    else:
        primeiro = "escolher o projeto do dia"
    linhas.append(f"A primeira coisa a fazer: {primeiro}.")
    if estado.get("resumo", {}).get("exemplos"):
        linhas.append(f"Atenção: {estado['resumo']['exemplos']} itens são exemplos, porque não deu para ler a fonte.")
    return " ".join(linhas)


def melhorar_com_ollama(texto: str, url: str, modelo: str, prompt_extra: str = "", timeout: float = 60) -> str | None:
    """Pede ao Ollama LOCAL para reescrever. Devolve None se não houver Ollama ou der erro."""
    pedido = (prompt_extra + "\n\n" if prompt_extra else "") + (
        "Reescreva o resumo abaixo em português do Brasil, em até 5 frases curtas, tom calmo de assistente pessoal. "
        "Não invente nada: mantenha todos os números e nomes exatamente como estão.\n\nResumo:\n" + texto)
    corpo = json.dumps({"model": modelo, "prompt": pedido, "stream": False, "think": False}).encode()
    req = urllib.request.Request(url.rstrip("/") + "/api/generate", data=corpo, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode()).get("response", "").strip()
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None
    return resp or None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Resumo da manhã a partir do estado.json.")
    ap.add_argument("--estado", default=str(AQUI / "estado.json"))
    ap.add_argument("--config", default=str(AQUI / "config.json"))
    ap.add_argument("--saida", default=str(AQUI / "bom_dia.txt"))
    ap.add_argument("--ollama", action="store_true", help="melhorar o texto com o modelo local (opcional)")
    a = ap.parse_args(argv)

    caminho = Path(a.estado)
    if not caminho.exists():
        print("Falta o estado.json. Rode antes: python3 coletar.py", file=sys.stderr)
        return 1
    estado = json.loads(caminho.read_text(encoding="utf-8"))
    texto = resumo_por_regra(estado)
    fonte = "regra"
    if a.ollama:
        cfg = json.loads(Path(a.config).read_text(encoding="utf-8")) if Path(a.config).exists() else {}
        oc = cfg.get("ollama", {})
        pers = AQUI / "prompts" / "jarvis-personalidade.md"
        melhor = melhorar_com_ollama(texto, oc.get("url", "http://localhost:11434"), oc.get("modelo", "qwen3.5:9b"),
                                     pers.read_text(encoding="utf-8") if pers.exists() else "",
                                     timeout=float(oc.get("timeout", 180)))
        if melhor:
            texto, fonte = melhor, "ollama"
        else:
            print("(Ollama não respondeu: fica o texto da regra)", file=sys.stderr)
    Path(a.saida).write_text(texto + "\n", encoding="utf-8")
    print(f"[{fonte}] {texto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
