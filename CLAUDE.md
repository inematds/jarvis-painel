# CLAUDE.md — jarvis-painel

Painel HUD (index.html) que mostra timers, serviços, filas e pendências da máquina e fala em pt-BR.

## Regras do projeto
- Só leitura: `coletar.py` chama apenas `systemctl --user list-timers|show|list-units --failed` e lê arquivos.
  Nunca adicionar comando que inicie, pare, apague ou envie algo. Aprovar/Depois só gravam no localStorage.
- Dado que não deu para ler vira item com `"exemplo": true` — nunca inventar dado como real.
- Sem dependências fora da stdlib (Python) e sem build (index.html self-contained).
- `estado.json` e `bom_dia.txt` têm dados reais da máquina: ficam no `.gitignore`. Print público = `coletar.py --anonimo`.
- Testes sem rede: `python3 -m pytest -q`. Mudou o fluxo → atualizar "O processo, do início ao fim" no README (PT/EN/ES).
- Guia em `guia/` (PT) + `guia/en/` + `guia/es/`; comandos dentro de `<pre>` iguais byte a byte nos três idiomas.
- Commits: autor `inematds <inematds@gmail.com>`.

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule
at the TOP of the ## Lessons section below, so it never happens again.

## Lessons
- `resumo.falhou` e "Esperando você" têm de contar as MESMAS falhas (timers + serviços sem timer + filas com erro); antes o núcleo dizia 5 e a lista 10. (08/11/2026)
- `id` de pendência é hash do título: id com o texto vazava o título no modo `--anonimo`. (08/11/2026)
- `backdrop-filter`/`filter: blur` nos painéis derrubava o canvas para 25–35 fps em 1920 px; brilho dos anéis com traço largo translúcido, sem `shadowBlur`. (08/11/2026)
