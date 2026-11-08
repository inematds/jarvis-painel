#!/usr/bin/env python3
"""coletar.py — monta o estado.json do painel do Jarvis.

Só LÊ a máquina: timers do systemd do usuário, o último resultado de cada serviço,
serviços que falharam, um arquivo de pendências em markdown e fontes extras (filas JSON
e arquivos de log) listadas no config.json. Nada é executado, pausado, apagado ou enviado.

Dado que não deu para ler vira um item marcado como "exemplo" (exemplo: true),
nunca um dado inventado como se fosse real.

Uso:
    python3 coletar.py                     # lê config.json, grava estado.json
    python3 coletar.py --config outro.json --saida estado.json
    python3 coletar.py --anonimo           # troca o texto das pendências por "Pendência N" (para print público)
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
VERSAO = "1.0.0"

PROPS = "Id,Description,Result,ExecMainStatus,ExecMainStartTimestamp,ExecMainExitTimestamp,ActiveState"


# ---------------------------------------------------------------- utilidades

def rodar(cmd: list[str]) -> str | None:
    """Roda um comando SÓ DE LEITURA e devolve a saída (None se falhar)."""
    if not shutil.which(cmd[0]):
        return None
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0 and not r.stdout.strip():
        return None
    return r.stdout


def iso(ts: float | None) -> str | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def expandir(caminho: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(caminho)))


def ignorado(nome: str, padroes: list[str]) -> bool:
    return any(fnmatch.fnmatch(nome, p) for p in padroes)


# ---------------------------------------------------------------- systemd

def ler_timers(saida_json: str | None) -> list[dict]:
    """Converte `systemctl --user list-timers --all --output=json` em lista simples."""
    if not saida_json:
        return []
    try:
        dados = json.loads(saida_json)
    except json.JSONDecodeError:
        return []
    timers = []
    for t in dados:
        unidade = t.get("unit") or ""
        servico = t.get("activates") or unidade.replace(".timer", ".service")
        prox = t.get("next") or 0
        ult = t.get("last") or 0
        timers.append({
            "timer": unidade,
            "servico": servico,
            "proxima": prox / 1_000_000 if prox else None,
            "ultima": ult / 1_000_000 if ult else None,
        })
    return timers


def ler_show(saida: str | None) -> dict[str, dict]:
    """Converte a saída de `systemctl --user show A B ... -p ...` (blocos separados por linha vazia)."""
    blocos: dict[str, dict] = {}
    if not saida:
        return blocos
    atual: dict = {}
    for linha in saida.splitlines() + [""]:
        if not linha.strip():
            if atual.get("Id"):
                blocos[atual["Id"]] = atual
            atual = {}
            continue
        if "=" in linha:
            k, v = linha.split("=", 1)
            atual[k] = v
    return blocos


def _ts(valor: str | None) -> float | None:
    if valor and valor.startswith("@"):
        try:
            n = float(valor[1:])
            return n or None
        except ValueError:
            return None
    return None


def estado_do_servico(info: dict | None) -> str:
    """ok | falhou | rodando | aguardando"""
    if not info:
        return "aguardando"
    ativo = info.get("ActiveState", "")
    if ativo == "failed":
        return "falhou"
    if ativo in ("active", "activating", "reloading"):
        return "rodando"
    if not _ts(info.get("ExecMainExitTimestamp")) and not _ts(info.get("ExecMainStartTimestamp")):
        return "aguardando"
    if info.get("Result", "success") != "success" or info.get("ExecMainStatus", "0") not in ("0", ""):
        return "falhou"
    return "ok"


def ler_falhas(saida_json: str | None) -> list[dict]:
    if not saida_json:
        return []
    try:
        dados = json.loads(saida_json)
    except json.JSONDecodeError:
        return []
    return [{"unidade": u.get("unit", ""), "descricao": u.get("description", "")} for u in dados]


def coletar_systemd(cfg: dict, executar=rodar) -> tuple[list[dict], list[dict], list[str]]:
    """Devolve (sistemas, falhas, avisos)."""
    avisos: list[str] = []
    ign = cfg.get("ignorar", [])
    timers = [t for t in ler_timers(executar(["systemctl", "--user", "list-timers", "--all", "--no-pager", "--output=json"]))
              if not ignorado(t["timer"], ign) and not ignorado(t["servico"], ign)]
    if not timers:
        avisos.append("Não consegui ler os timers (systemctl --user). Mostrando exemplos.")
        return [], [], avisos

    falhas = [f for f in ler_falhas(executar(["systemctl", "--user", "list-units", "--failed", "--no-pager", "--output=json"]))
              if f["unidade"].endswith(".service") and not ignorado(f["unidade"], ign)]
    servicos = [t["servico"] for t in timers]
    # serviço que falhou mas não tem timer também entra na lista de sistemas (uma contagem só de falhas)
    soltos = [f["unidade"] for f in falhas if f["unidade"] not in servicos]
    show = ler_show(executar(["systemctl", "--user", "show", *servicos, *soltos, "--timestamp=unix", "-p", PROPS, "--no-pager"]))
    sistemas = []
    for t in [*timers, *({"servico": u, "ultima": None, "proxima": None, "solto": True} for u in soltos)]:
        info = show.get(t["servico"])
        fim = _ts(info.get("ExecMainExitTimestamp")) if info else None
        sistemas.append({
            "nome": t["servico"].removesuffix(".service"),
            "descricao": (info or {}).get("Description", ""),
            "estado": "falhou" if t.get("solto") else estado_do_servico(info),
            "ultima": iso(fim or t["ultima"]),
            "proxima": iso(t["proxima"]),
            "origem": "systemd",
            "timer": not t.get("solto"),
            "exemplo": False,
        })

    return sistemas, falhas, avisos


# ---------------------------------------------------------------- pendências

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_DATA = re.compile(r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})")


def ler_pendencias(texto: str, parar_em: str = "Resolvidas", limite: int = 50) -> list[dict]:
    """Itens de primeiro nível (`- **título** ...` ou `### título`) até a seção `## <parar_em>`."""
    itens = []
    for linha in texto.splitlines():
        if re.match(r"^##\s", linha) and parar_em.lower() in linha.lower():
            break
        titulo = None
        if linha.startswith("- "):
            m = _BOLD.search(linha)
            if m:
                titulo = m.group(1)
        elif linha.startswith("### "):
            titulo = linha[4:]
        if not titulo:
            continue
        titulo = titulo.strip().rstrip(".")
        if not titulo or "[x]" in linha[:8]:
            continue
        m = _DATA.search(titulo)
        itens.append({"titulo": titulo, "data": m.group(1) if m else None})
        if len(itens) >= limite:
            break
    return itens


# ---------------------------------------------------------------- fontes extras

def ler_fila_json(caminho: Path, campo: str = "estado", esperando: list[str] | None = None) -> dict:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if isinstance(dados, dict):
        dados = dados.get("itens") or dados.get("fila") or []
    if not isinstance(dados, list):
        raise ValueError("fila não é uma lista")
    cont = Counter(str(x.get(campo, "?")) for x in dados if isinstance(x, dict))
    esp = esperando or ["pendente"]
    return {"contagem": dict(cont), "esperando": sum(cont.get(e, 0) for e in esp), "total": len(dados)}


def ler_log(caminho: Path) -> dict:
    with caminho.open("rb") as f:
        f.seek(0, 2)
        tam = f.tell()
        f.seek(max(0, tam - 4096))
        fim = f.read().decode("utf-8", "replace").strip().splitlines()
    return {"ultima_linha": (fim[-1] if fim else "")[:200], "quando": iso(caminho.stat().st_mtime)}


def coletar_extras(fontes: list[dict]) -> tuple[list[dict], list[str]]:
    sistemas, avisos = [], []
    for f in fontes:
        nome = f.get("nome") or f.get("caminho", "?")
        tipo = f.get("tipo", "log")
        caminho = expandir(f.get("caminho", ""))
        try:
            if tipo == "fila_json":
                r = ler_fila_json(caminho, f.get("campo", "estado"), f.get("esperando"))
                partes = ", ".join(f"{v} {k}" for k, v in sorted(r["contagem"].items()))
                sistemas.append({
                    "nome": nome, "descricao": f"fila: {partes}", "estado": "falhou" if r["contagem"].get("erro") else "ok",
                    "ultima": iso(caminho.stat().st_mtime), "proxima": None, "origem": "fila",
                    "na_fila": r["esperando"], "exemplo": False,
                })
            else:
                r = ler_log(caminho)
                erro = bool(re.search(r"\b(erro|error|falhou|failed|traceback)\b", r["ultima_linha"], re.I))
                sistemas.append({
                    "nome": nome, "descricao": r["ultima_linha"], "estado": "falhou" if erro else "ok",
                    "ultima": r["quando"], "proxima": None, "origem": "log", "exemplo": False,
                })
        except (OSError, ValueError, json.JSONDecodeError) as e:
            avisos.append(f"Não consegui ler {nome} ({type(e).__name__}). Virou exemplo.")
            sistemas.append({
                "nome": nome, "descricao": "exemplo — não deu para ler este arquivo", "estado": "aguardando",
                "ultima": None, "proxima": None, "origem": tipo, "exemplo": True,
            })
    return sistemas, avisos


# ---------------------------------------------------------------- exemplos

def exemplos_sistemas() -> list[dict]:
    agora = time.time()
    return [
        {"nome": "robo-relatorio", "descricao": "exemplo — relatório da manhã", "estado": "ok",
         "ultima": iso(agora - 3600), "proxima": iso(agora + 82800), "origem": "exemplo", "exemplo": True},
        {"nome": "robo-backup", "descricao": "exemplo — cópia de segurança", "estado": "falhou",
         "ultima": iso(agora - 7200), "proxima": iso(agora + 79200), "origem": "exemplo", "exemplo": True},
        {"nome": "robo-fila-videos", "descricao": "exemplo — fila de vídeos", "estado": "aguardando",
         "ultima": None, "proxima": iso(agora + 1800), "origem": "exemplo", "exemplo": True},
    ]


# ---------------------------------------------------------------- montagem

def montar_estado(cfg: dict, executar=rodar, anonimo: bool = False) -> dict:
    avisos: list[str] = []
    sistemas, _falhas, av = coletar_systemd(cfg, executar)
    avisos += av
    extras, av = coletar_extras(cfg.get("fontes_extras", []))
    avisos += av
    if not sistemas:
        sistemas = exemplos_sistemas()
    sistemas += extras

    esperando = []
    # 1) tudo que falhou (timers, serviços sem timer, filas e logs com erro) — a mesma contagem do resumo
    for s in sistemas:
        if s["estado"] == "falhou":
            esperando.append({"id": "falha:" + s["nome"], "titulo": f"{s['nome']} falhou", "detalhe": s["descricao"][:160],
                              "origem": s["origem"], "tipo": "falha", "exemplo": s["exemplo"]})
    # 2) pendências do markdown
    pend_cfg = cfg.get("pendencias") or {}
    if pend_cfg.get("arquivo"):
        caminho = expandir(pend_cfg["arquivo"])
        try:
            itens = ler_pendencias(caminho.read_text(encoding="utf-8"), pend_cfg.get("parar_em", "Resolvidas"),
                                   int(pend_cfg.get("limite", 50)))
            for i, it in enumerate(itens, 1):
                titulo = f"Pendência {i}" + (f" ({it['data']})" if it["data"] else "") if anonimo else it["titulo"][:140]
                esperando.append({"id": "pend:" + hashlib.sha1(it["titulo"].encode()).hexdigest()[:10], "titulo": titulo, "detalhe": "",
                                  "origem": "pendencias", "tipo": "pendencia", "exemplo": False})
        except (OSError, UnicodeDecodeError) as e:
            avisos.append(f"Não consegui ler as pendências em {caminho} ({type(e).__name__}). Virou exemplo.")
            esperando.append({"id": "pend:exemplo", "titulo": "exemplo — responder o orçamento do cliente",
                              "detalhe": "", "origem": "exemplo", "tipo": "pendencia", "exemplo": True})
    # 3) itens parados em filas
    for s in sistemas:
        if s.get("na_fila"):
            esperando.append({"id": "fila:" + s["nome"], "titulo": f"{s['na_fila']} na fila {s['nome']}",
                              "detalhe": s["descricao"], "origem": "fila", "tipo": "fila", "exemplo": False})

    cont = Counter(s["estado"] for s in sistemas)
    return {
        "versao": VERSAO,
        "gerado_em": iso(time.time()),
        "nome": cfg.get("nome", "você"),
        "assistente": cfg.get("assistente", "JARVIS"),
        "maquina": platform.node(),
        "resumo": {
            "sistemas": len(sistemas),
            "timers": sum(1 for s in sistemas if s.get("timer")),
            "servicos_sem_timer": sum(1 for s in sistemas if s["origem"] == "systemd" and not s.get("timer")),
            "fontes_extras": sum(1 for s in sistemas if s["origem"] in ("fila", "log", "fila_json")),
            "ok": cont.get("ok", 0), "falhou": cont.get("falhou", 0),
            "rodando": cont.get("rodando", 0), "aguardando": cont.get("aguardando", 0),
            "esperando": len(esperando),
            "exemplos": sum(1 for s in sistemas if s["exemplo"]) + sum(1 for e in esperando if e["exemplo"]),
        },
        "sistemas": sistemas,
        "esperando": esperando,
        "avisos": avisos,
    }


def carregar_config(caminho: Path) -> dict:
    if not caminho.exists():
        print(f"(sem {caminho.name}: usando padrão vazio)", file=sys.stderr)
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Monta o estado.json do painel (só leitura).")
    ap.add_argument("--config", default=str(AQUI / "config.json"))
    ap.add_argument("--saida", default=str(AQUI / "estado.json"))
    ap.add_argument("--anonimo", action="store_true", help="troca o texto das pendências por 'Pendência N'")
    a = ap.parse_args(argv)
    estado = montar_estado(carregar_config(Path(a.config)), anonimo=a.anonimo)
    Path(a.saida).write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    r = estado["resumo"]
    print(f"estado.json: {r['sistemas']} sistemas ({r['timers']} timers) · {r['ok']} ok · {r['falhou']} falharam · "
          f"{r['esperando']} esperando você · {r['exemplos']} exemplos")
    for av in estado["avisos"]:
        print("aviso:", av)
    return 0


if __name__ == "__main__":
    sys.exit(main())
