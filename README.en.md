# jarvis-painel — your Jarvis dashboard

[![jarvis-painel](guia/assets/banner-en.jpg)](https://inematds.github.io/jarvis-painel/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

> Your robots are working. You can’t see what they’re doing. One screen shows everything and says good morning.

## What it is

jarvis-painel is a science fiction style dashboard that brings together everything running automatically on your computer: Linux timers, queues, and log files. It’s for people who have robots, routines, and queues running but don’t know what each one did or what is waiting for them. It shows what finished successfully, what failed, and your to do list, then reads a summary aloud in English. It only needs Python 3 and a browser; everything runs on your machine, with no keys or paid services, and it only reads data: the buttons don’t run anything.

## 📖 User guide

Complete guide (landing page + step by step): **https://inematds.github.io/jarvis-painel/guia/en/**
Live demo (example mode, without your data): **https://inematds.github.io/jarvis-painel/**

## What appears on screen

- **Central core**: three rings rotating at different speeds, pulsing light, the name `JARVIS`, and a status line.
- **Startup, ~3 s**: "Inicializando… Sistemas no ar." (“Initializing… Systems online.”) "Bom dia" (“Good morning”), <name>.
- **Systems** (left): each timer, service, and queue with a status dot (ok, failed, running, waiting) and the last action.
- **"Esperando você" (“Waiting for you”)** (right): what failed + items from your markdown file + items stopped in queues.
  The **"Aprovar" (“Approve”)** and **"Depois" (“Later”)** buttons only mark items on screen (saved in your browser). Nothing is run.
- **Top bar**: clock, date, and the **"Voz: ligada" (“Voice: on”)** badge (click to turn it off).
- **Command bar**: **"Bom dia" (“Good morning”) · "Status" (“Status”) · "O que espera" (“What’s waiting”) · "Modo foco" (“Focus mode”)** (keys 1 to 4). Focus mode dims the panels.
- **Voice** in English (the browser’s `speechSynthesis`, which chooses an English voice if available), a wave around the core while it speaks, and the response text typed below.
- Works on mobile (no horizontal scrolling).

Data that couldn’t be read becomes an item marked **"exemplo" (“example”)**, never made up as if it were real.

## The process, start to finish

Who does what: 🧠 you · ⚙️ script · 🤖 AI model (optional)

| # | Step | Command | Who |
|---|---|---|---|
| 1 | Download the kit | `git clone https://github.com/inematds/jarvis-painel.git && cd jarvis-painel` | 🧠 |
| 2 | Enter your name, to do list file, and queues | edit `config.json` | 🧠 |
| 3 | Read the machine (timers, failures, to do list, queues) | `python3 coletar.py` → `estado.json` | ⚙️ |
| 4 | Write the morning summary using fixed rules | `python3 bom_dia.py` → `bom_dia.txt` | ⚙️ |
| 5 | (Optional) Make the summary sound more natural with the local model | `python3 bom_dia.py --ollama` | 🤖 |
| 6 | Open the dashboard | `python3 -m http.server 8000` and open `http://localhost:8000` | ⚙️ |
| 7 | Use the shortcuts and mark items "Aprovar" (“Approve”)/"Depois" (“Later”) | keys 1–4 in the dashboard | 🧠 |
| 8 | (Optional) Update automatically every 5 min | `crontab` line below | ⚙️ |
| 9 | Ask for read only customer research, or fix the dashboard | prompts in `prompts/en/` | 🤖 |

You need Python 3.9+ and git (on Ubuntu: `sudo apt install git`).

```bash
git clone https://github.com/inematds/jarvis-painel.git
cd jarvis-painel
python3 coletar.py
python3 bom_dia.py
python3 -m http.server 8000
```

Then open `http://localhost:8000` in your browser and leave that terminal open (Ctrl+C stops it). To update
automatically (optional), run `crontab -e` and paste the line below (this works if the kit is in your home folder; change the
path if you downloaded it somewhere else). `coletar.py` finds your timers even when it runs through cron:

```
*/5 * * * * cd $HOME/jarvis-painel && python3 coletar.py && python3 bom_dia.py
```

The page reloads `estado.json` every 60 seconds.

## Configure (`config.json`)

It comes set up for INEMA: to do list at `~/projetos/wifi/pendencias.md` and two JSON queues from the wifi project.
Replace them with your own (`nano config.json`; if you miss a comma, `coletar.py` tells you the line with the error):

| Field | What it is |
|---|---|
| `nome` | what Jarvis calls you ("Good morning, Nei.") |
| `pendencias.arquivo` | one of your `.md` files; each line `- **title**` or `### title` becomes an item, up to the `## Resolvidas` section |
| `fontes_extras` | queues (`"tipo": "fila_json"`, counts items by `estado`) and logs (`"tipo": "log"`, shows the last line) |
| `ignorar` | timers and services that shouldn’t appear (e.g., `snap.*`) |
| `ollama` | local address and model for `bom_dia.py --ollama` |

Without Linux with systemd (for example, on a Mac), the dashboard shows systems as **"exemplo" (“example”)** and still reads the to do list and queues.
To take a screenshot without exposing your to do list: `python3 coletar.py --anonimo` replaces each title with **"Pendência N (data)" (“Pending item N (date)”)**.

## What it reads (and what it never does)

- Reads: `systemctl --user list-timers`, `systemctl --user show` (last result for each service),
  `systemctl --user list-units --failed`, the to do list file, and the extra sources in `config.json`.
- Never: starts, stops, restarts, deletes, or sends anything. Tests check that only read commands are called.
- "Aprovar" (“Approve”)/"Depois" (“Later”): only save to the browser’s `localStorage` (`jarvis-painel:marcas`).

## Prompts (`prompts/`)

- `jarvis-personalidade.md` — Jarvis’s personality (calm, in English, doesn’t make up numbers or run anything).
- `pesquisa-clientes.md` — for Claude Code with a browser: "search for <industry> in <city>, open the first 3 websites, make a table with name, website, phone number, and one thing the website does poorly; only read, don’t contact anyone or fill out forms."
- `conserta-tela.md` — paste the error and ask for a fix.

English and Spanish versions are in `prompts/en/` and `prompts/es/`.

## Talk by voice with a local model

The dashboard works on its own. To talk by voice with a model running on your GPU, use the sibling kit
**[jarvis-local](https://inematds.github.io/jarvis-local/guia/)** and paste `prompts/jarvis-personalidade.md` as the instructions.

## Tests

```bash
python3 -m unittest discover tests
```

(or `python3 -m pytest -q`, if you have pytest)

They run offline: data collection with simulated `systemctl` output, unreadable items that become "exemplo" (“example”), markdown to do lists,
queues, anonymous mode, and `bom_dia.py` without Ollama.

## License

MIT. Open content from [INEMA.CLUB](https://inema.club).
