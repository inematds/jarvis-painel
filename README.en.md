# jarvis-painel — your Jarvis dashboard

[![jarvis-painel](guia/assets/banner-en.jpg)](https://inematds.github.io/jarvis-painel/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

> Your bots are working. You can’t see them. One screen shows everything and says good morning.

## What it is

jarvis-painel is a sci-fi-style dashboard that brings together everything running automatically on your computer in
one place: Linux timers, queues, and log files. It’s for people with bots, routines, and queues running who don’t
know what each one has done or what’s waiting for them. It shows what finished successfully, what failed, and your
to-do list, then reads a summary aloud in English. It only needs Python 3 and a browser; everything runs on
your machine, with no key or paid service, and it only reads: the buttons don’t run anything.

## 📖 User guide

Full guide (landing page + walkthrough): **https://inematds.github.io/jarvis-painel/guia/en/**
Live demo (example mode, with no real data): **https://inematds.github.io/jarvis-painel/**

## What appears on screen

- **Central core**: three rings spinning at different speeds, pulsing light, the name `JARVIS`, and a status line.
- **~3-second startup**: "Initializing… Systems online. Good morning, <name>."
- **Systems** (left): each timer, service, and queue with a status dot (ok, failed, running, waiting) and its last action.
- **Waiting for you** (right): what failed + items from your markdown file + items stopped in queues.
  **Approve** and **Later** buttons only mark items on screen (saved in the browser). Nothing is executed.
- **Top bar**: clock, date, and the **Voice: on** badge (click to turn it off).
- **Command bar**: **Good morning · Status · What’s waiting · Focus mode** (keys 1 to 4). Focus mode dims the panels.
- **Voice** in English (`speechSynthesis` in the browser, chooses an English voice if available), a wave around the core
  while it speaks, and the response text appearing below.
- Works on mobile (no horizontal scrolling).

Any data that can’t be read becomes an item marked **example**, never made up as if it were real.

## The process, start to finish

Who does what: 🧠 you · ⚙️ script · 🤖 AI model (optional)

| # | Step | Command | Who |
|---|---|---|---|
| 1 | Download the kit | `git clone https://github.com/inematds/jarvis-painel.git && cd jarvis-painel` | 🧠 |
| 2 | Enter your name, to-do file, and queues | edit `config.json` | 🧠 |
| 3 | Read the machine (timers, failures, to-dos, queues) | `python3 coletar.py` → `estado.json` | ⚙️ |
| 4 | Write the morning summary using fixed rules | `python3 bom_dia.py` → `bom_dia.txt` | ⚙️ |
| 5 | (Optional) Make the summary sound more natural with the local model | `python3 bom_dia.py --ollama` | 🤖 |
| 6 | Open the dashboard | `python3 -m http.server 8000` and open `http://localhost:8000` | ⚙️ |
| 7 | Use shortcuts and mark items as Approve/Later | keys 1–4 on the dashboard | 🧠 |
| 8 | (Optional) Refresh automatically every 5 min | `crontab` line below | ⚙️ |
| 9 | Ask for read-only customer research or fix the dashboard | prompts in `prompts/en/` | 🤖 |

```bash
git clone https://github.com/inematds/jarvis-painel.git
cd jarvis-painel
python3 coletar.py
python3 bom_dia.py
python3 -m http.server 8000
```

Then open `http://localhost:8000` in your browser. To refresh automatically (optional), run `crontab -e` and paste
the line below, replacing the path with the folder where you downloaded it:

```
*/5 * * * * cd $HOME/jarvis-painel && python3 coletar.py && python3 bom_dia.py
```

The page rereads `estado.json` every 60 seconds.

## Configure (`config.json`)

It comes configured for INEMA: to-dos in `~/projetos/wifi/pendencias.md` and two JSON queues from the wifi project.
Replace them with your own:

| Field | What it is |
|---|---|
| `nome` | what Jarvis calls you ("Good morning, Nei.") |
| `pendencias.arquivo` | one of your `.md` files; each line `- **title**` or `### title` becomes an item, up to the `## Resolvidas` section |
| `fontes_extras` | queues (`"tipo": "fila_json"`, counts items by `estado`) and logs (`"tipo": "log"`, shows the last line) |
| `ignorar` | timers and services that shouldn’t appear (e.g., `snap.*`) |
| `ollama` | local address and model for `bom_dia.py --ollama` |

Without Linux with systemd (for example, on a Mac), the dashboard shows systems as **example** and still reads to-dos and queues.
To take a screenshot without exposing your to-dos: `python3 coletar.py --anonimo` replaces each title with "Pendência N (date)".

## What it reads (and what it never does)

- Reads: `systemctl --user list-timers`, `systemctl --user show` (last result for each service),
  `systemctl --user list-units --failed`, the to-do file, and extra sources from `config.json`.
- Never: starts, stops, restarts, deletes, or sends anything. Tests check that only read commands are called.
- Approve/Later: only save to the browser’s `localStorage` (`jarvis-painel:marcas`).

## Prompts (`prompts/en/`)

- `jarvis-personalidade.md` — Jarvis’s personality (calm, in English, doesn’t make up numbers or execute anything).
- `pesquisa-clientes.md` — for Claude Code with a browser: “search for <industry> in <city>, open the first 3 websites,
  make a table with name, website, phone, and one thing the website does poorly; only read, don’t contact anyone or fill out forms.”
- `conserta-tela.md` — paste the error and ask for a fix.

English and Spanish versions are in `prompts/en/` and `prompts/es/`.

## Talk by voice with a local model

The dashboard works on its own. To talk by voice with a model running on your GPU, use the sibling kit
**[jarvis-local](https://inematds.github.io/jarvis-local/guia/)** and paste `prompts/jarvis-personalidade.md` as the instruction.

## Tests

```bash
python3 -m pytest -q
```

They run without a network connection: collection with simulated `systemctl` output, unreadable items marked as "example", markdown to-dos,
queues, anonymous mode, and `bom_dia.py` without Ollama.

## License

MIT. Open content from [INEMA.CLUB](https://inema.club).
