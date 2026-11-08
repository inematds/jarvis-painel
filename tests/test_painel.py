"""Testes sem rede: rodam com `python3 -m pytest -q` (ou `python3 -m unittest`)."""
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bom_dia  # noqa: E402
import coletar  # noqa: E402

TIMERS = json.dumps([
    {"next": 1794134227000000, "left": 0, "last": 1794133927000000, "passed": 0,
     "unit": "relatorio.timer", "activates": "relatorio.service"},
    {"next": 1794134227000000, "left": 0, "last": 1794133927000000, "passed": 0,
     "unit": "backup.timer", "activates": "backup.service"},
    {"next": 1794134227000000, "left": 0, "last": None, "passed": None,
     "unit": "novo.timer", "activates": "novo.service"},
    {"next": 1794134227000000, "left": 0, "last": 0, "passed": 0,
     "unit": "snap.lixo.timer", "activates": "snap.lixo.service"},
])

SHOW = """Id=relatorio.service
Description=Relatório da manhã
Result=success
ExecMainStatus=0
ExecMainStartTimestamp=@1794133927
ExecMainExitTimestamp=@1794133990
ActiveState=inactive

Id=backup.service
Description=Cópia de segurança
Result=exit-code
ExecMainStatus=1
ExecMainStartTimestamp=@1794133927
ExecMainExitTimestamp=@1794133999
ActiveState=failed

Id=novo.service
Description=Nunca rodou
Result=success
ExecMainStatus=0
ExecMainStartTimestamp=
ExecMainExitTimestamp=
ActiveState=inactive

Id=orfao.service
Description=Serviço sem timer
Result=exit-code
ExecMainStatus=2
ExecMainStartTimestamp=@1794133000
ExecMainExitTimestamp=@1794133001
ActiveState=failed
"""

FALHAS = json.dumps([
    {"unit": "backup.service", "load": "loaded", "active": "failed", "sub": "failed", "description": "Cópia de segurança"},
    {"unit": "orfao.service", "load": "loaded", "active": "failed", "sub": "failed", "description": "Serviço sem timer"},
    {"unit": "run-u1.scope", "load": "loaded", "active": "failed", "sub": "failed", "description": "transitório"},
])


def falso_systemctl(cmd):
    """Simula as saídas do systemctl. Só aceita os comandos de LEITURA que o coletar usa."""
    assert cmd[0] == "systemctl" and "--user" in cmd
    proibidos = {"start", "stop", "restart", "enable", "disable", "kill", "reset-failed", "mask"}
    assert not proibidos & set(cmd), f"comando que muda a máquina: {cmd}"
    if "list-timers" in cmd:
        return TIMERS
    if "show" in cmd:
        return SHOW
    if "--failed" in cmd:
        return FALHAS
    return None


class TesteColeta(unittest.TestCase):
    def test_coleta_com_systemctl_simulado(self):
        cfg = {"ignorar": ["snap.*", "*.scope"]}
        estado = coletar.montar_estado(cfg, executar=falso_systemctl)
        nomes = {s["nome"]: s for s in estado["sistemas"]}
        self.assertEqual(set(nomes), {"relatorio", "backup", "novo", "orfao"})  # snap.* e .scope ignorados
        self.assertEqual(nomes["relatorio"]["estado"], "ok")
        self.assertEqual(nomes["backup"]["estado"], "falhou")
        self.assertEqual(nomes["novo"]["estado"], "aguardando")
        self.assertTrue(nomes["relatorio"]["ultima"].startswith("2026-"))
        falhas = [e for e in estado["esperando"] if e["tipo"] == "falha"]
        self.assertEqual(sorted(e["titulo"] for e in falhas), ["backup falhou", "orfao falhou"])  # sem duplicar
        self.assertEqual(nomes["orfao"]["estado"], "falhou")
        self.assertEqual(estado["resumo"]["timers"], 3)
        self.assertEqual(estado["resumo"]["servicos_sem_timer"], 1)
        # a mesma contagem de falhas no resumo e em "Esperando você"
        self.assertEqual(estado["resumo"]["falhou"], len(falhas))
        self.assertEqual(estado["resumo"]["exemplos"], 0)

    def test_sem_systemctl_vira_exemplo(self):
        estado = coletar.montar_estado({}, executar=lambda cmd: None)
        self.assertTrue(estado["sistemas"])
        self.assertTrue(all(s["exemplo"] for s in estado["sistemas"]))
        self.assertTrue(any("timers" in a for a in estado["avisos"]))

    def test_item_ilegivel_vira_exemplo(self):
        with tempfile.TemporaryDirectory() as d:
            ruim = Path(d) / "fila.json"
            ruim.write_text("{isto não é json", encoding="utf-8")
            cfg = {
                "pendencias": {"arquivo": str(Path(d) / "nao-existe.md")},
                "fontes_extras": [
                    {"nome": "fila-quebrada", "tipo": "fila_json", "caminho": str(ruim)},
                    {"nome": "log-sumiu", "tipo": "log", "caminho": str(Path(d) / "sumiu.log")},
                ],
            }
            estado = coletar.montar_estado(cfg, executar=falso_systemctl)
        extras = {s["nome"]: s for s in estado["sistemas"] if s["origem"] != "systemd"}
        self.assertTrue(extras["fila-quebrada"]["exemplo"])
        self.assertTrue(extras["log-sumiu"]["exemplo"])
        self.assertIn("exemplo", extras["fila-quebrada"]["descricao"])
        pend = [e for e in estado["esperando"] if e["tipo"] == "pendencia"]
        self.assertEqual(len(pend), 1)
        self.assertTrue(pend[0]["exemplo"])
        self.assertTrue(pend[0]["titulo"].startswith("exemplo"))
        self.assertEqual(estado["resumo"]["exemplos"], 3)

    def test_pendencias_markdown(self):
        md = """# Pendências
- **08/11/2026 — Responder o cliente.** detalhe longo
  - [ ] subitem não conta
## Abertas
- **07/11/2026 · Trocar a senha do roteador.**
- linha sem negrito não conta
### 2026-10-10 — Ideia guardada
## Resolvidas
- **01/10/2026 — já feito.**
"""
        itens = coletar.ler_pendencias(md)
        self.assertEqual([i["titulo"] for i in itens], [
            "08/11/2026 — Responder o cliente", "07/11/2026 · Trocar a senha do roteador",
            "2026-10-10 — Ideia guardada"])
        self.assertEqual(itens[0]["data"], "08/11/2026")

    def test_fila_json_conta_estados(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "fila.json"
            f.write_text(json.dumps([{"estado": "feito"}, {"estado": "pendente"}, {"estado": "pendente"}]))
            cfg = {"fontes_extras": [{"nome": "videos", "tipo": "fila_json", "caminho": str(f)}]}
            estado = coletar.montar_estado(cfg, executar=falso_systemctl)
        fila = [e for e in estado["esperando"] if e["tipo"] == "fila"]
        self.assertEqual(fila[0]["titulo"], "2 na fila videos")

    def test_anonimo_esconde_texto(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.md"
            p.write_text("- **08/11/2026 — Segredo do cliente X.**\n", encoding="utf-8")
            estado = coletar.montar_estado({"pendencias": {"arquivo": str(p)}}, executar=falso_systemctl, anonimo=True)
        pend = [e for e in estado["esperando"] if e["tipo"] == "pendencia"]
        self.assertEqual(pend[0]["titulo"], "Pendência 1 (08/11/2026)")
        self.assertNotIn("Segredo", json.dumps(estado, ensure_ascii=False))


class TesteBomDia(unittest.TestCase):
    def estado(self):
        return coletar.montar_estado({}, executar=falso_systemctl) | {"nome": "Ana"}

    def test_bom_dia_por_regra(self):
        agora = datetime.fromtimestamp(1794134000).astimezone().replace(hour=8)
        texto = bom_dia.resumo_por_regra(self.estado(), agora=agora)
        self.assertTrue(texto.startswith("Bom dia, Ana."))
        self.assertIn("backup", texto)
        self.assertIn("A primeira coisa a fazer: olhar por que backup falhou.", texto)

    def test_bom_dia_sem_ollama(self):
        # porta 9 (discard) em 127.0.0.1: recusa na hora, nenhuma rede externa
        self.assertIsNone(bom_dia.melhorar_com_ollama("oi", "http://127.0.0.1:9", "x", timeout=2))
        with tempfile.TemporaryDirectory() as d:
            e = Path(d) / "estado.json"
            e.write_text(json.dumps(self.estado()), encoding="utf-8")
            cfg = Path(d) / "config.json"
            cfg.write_text(json.dumps({"ollama": {"url": "http://127.0.0.1:9", "modelo": "x"}}))
            saida = Path(d) / "bom_dia.txt"
            rc = bom_dia.main(["--estado", str(e), "--config", str(cfg), "--saida", str(saida), "--ollama"])
            self.assertEqual(rc, 0)
            self.assertIn("Ana", saida.read_text(encoding="utf-8"))

    def test_bom_dia_sem_estado(self):
        self.assertEqual(bom_dia.main(["--estado", "/nao/existe.json"]), 1)


if __name__ == "__main__":
    unittest.main()
