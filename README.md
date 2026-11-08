# jarvis-painel — o painel do seu Jarvis

[![jarvis-painel](guia/assets/banner.jpg)](https://inematds.github.io/jarvis-painel/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

> Seus robôs trabalham. Você não vê. Uma tela mostra tudo e fala bom dia.

## O que é

O jarvis-painel é uma tela no estilo ficção científica que junta, num lugar só, tudo o que roda sozinho no seu
computador: os timers do Linux, filas e arquivos de log. Serve para quem tem robôs, rotinas e filas trabalhando e
não sabe o que cada um fez nem o que está esperando por você. Ele mostra quem terminou bem, quem falhou e a sua
lista de pendências, e lê um resumo em voz alta em português. Precisa só de Python 3 e de um navegador; tudo roda
na sua máquina, sem chave e sem serviço pago, e ele só lê: nada é executado pelos botões.

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/jarvis-painel/guia/**
Demonstração no ar (modo exemplo, sem os seus dados): **https://inematds.github.io/jarvis-painel/**

## O que aparece na tela

- **Núcleo central**: três anéis girando em velocidades diferentes, luz pulsando, o nome `JARVIS` e uma linha de status.
- **Partida de ~3 s**: "Inicializando… Sistemas no ar. Bom dia, <nome>."
- **Sistemas** (esquerda): cada timer, serviço e fila com ponto de status (ok, falhou, rodando, aguardando) e a última ação.
- **Esperando você** (direita): o que falhou + as pendências do seu arquivo markdown + itens parados em filas.
  Botões **Aprovar** e **Depois** só marcam na tela (ficam guardados no navegador). Nada é executado.
- **Topo**: relógio, data e o selo **Voz: ligada** (clique para desligar).
- **Barra de comando**: **Bom dia · Status · O que espera · Modo foco** (teclas 1 a 4). O foco escurece os painéis.
- **Voz** em português (`speechSynthesis` do navegador, escolhe uma voz pt-BR se houver), uma onda em volta do núcleo
  enquanto fala e o texto da resposta digitado embaixo.
- Funciona no celular (sem rolagem lateral).

Dado que não deu para ler vira um item marcado **exemplo**, nunca inventado como se fosse real.

## O processo, do início ao fim

Quem faz: 🧠 você · ⚙️ script · 🤖 modelo de IA (opcional)

| # | Passo | Comando | Quem |
|---|---|---|---|
| 1 | Baixar o kit | `git clone https://github.com/inematds/jarvis-painel.git && cd jarvis-painel` | 🧠 |
| 2 | Dizer o seu nome, o arquivo de pendências e as filas | editar `config.json` | 🧠 |
| 3 | Ler a máquina (timers, falhas, pendências, filas) | `python3 coletar.py` → `estado.json` | ⚙️ |
| 4 | Escrever o resumo da manhã por regra fixa | `python3 bom_dia.py` → `bom_dia.txt` | ⚙️ |
| 5 | (Opcional) deixar o resumo mais natural com o modelo local | `python3 bom_dia.py --ollama` | 🤖 |
| 6 | Abrir a tela | `python3 -m http.server 8000` e abrir `http://localhost:8000` | ⚙️ |
| 7 | Usar os atalhos e marcar Aprovar/Depois | teclas 1–4 no painel | 🧠 |
| 8 | (Opcional) atualizar sozinho a cada 5 min | linha do `crontab` abaixo | ⚙️ |
| 9 | Pedir uma pesquisa de clientes só lendo, ou consertar a tela | prompts em `prompts/` | 🤖 |

Precisa de Python 3.9+ e do git (no Ubuntu: `sudo apt install git`).

```bash
git clone https://github.com/inematds/jarvis-painel.git
cd jarvis-painel
python3 coletar.py
python3 bom_dia.py
python3 -m http.server 8000
```

Depois abra `http://localhost:8000` no navegador e deixe esse terminal aberto (Ctrl+C desliga). Para atualizar
sozinho (opcional), rode `crontab -e` e cole a linha abaixo (vale se o kit está na sua pasta pessoal; troque o
caminho se baixou em outro lugar). O `coletar.py` acha os seus timers mesmo rodando pelo cron:

```
*/5 * * * * cd $HOME/jarvis-painel && python3 coletar.py && python3 bom_dia.py
```

A página relê o `estado.json` a cada 60 segundos.

## Configurar (`config.json`)

Vem configurado para o INEMA: pendências em `~/projetos/wifi/pendencias.md` e duas filas JSON do projeto wifi.
Troque pelo seu (`nano config.json`; se errar uma vírgula, o `coletar.py` diz a linha do erro):

| Campo | O que é |
|---|---|
| `nome` | como o Jarvis chama você ("Bom dia, Nei.") |
| `pendencias.arquivo` | um arquivo `.md` seu; cada linha `- **título**` ou `### título` vira um item, até a seção `## Resolvidas` |
| `fontes_extras` | filas (`"tipo": "fila_json"`, conta os itens por `estado`) e logs (`"tipo": "log"`, mostra a última linha) |
| `ignorar` | timers e serviços que não devem aparecer (ex.: `snap.*`) |
| `ollama` | endereço e modelo local para o `bom_dia.py --ollama` |

Sem Linux com systemd (por exemplo, no Mac), o painel mostra os sistemas como **exemplo** e ainda lê as pendências e as filas.
Para tirar print sem expor as suas pendências: `python3 coletar.py --anonimo` troca cada título por "Pendência N (data)".

## O que ele lê (e o que nunca faz)

- Lê: `systemctl --user list-timers`, `systemctl --user show` (último resultado de cada serviço),
  `systemctl --user list-units --failed`, o arquivo de pendências e as fontes extras do `config.json`.
- Nunca: inicia, para, reinicia, apaga ou envia nada. Os testes conferem que só comandos de leitura são chamados.
- Aprovar/Depois: só gravam no `localStorage` do navegador (`jarvis-painel:marcas`).

## Prompts (`prompts/`)

- `jarvis-personalidade.md` — a personalidade do Jarvis (calmo, em português, não inventa número, não executa nada).
- `pesquisa-clientes.md` — para o Claude Code com navegador: "procure <ramo> em <cidade>, abra os 3 primeiros sites,
  tabela com nome, site, telefone e uma coisa que o site faz mal; só leia, não contate ninguém, não preencha formulário".
- `conserta-tela.md` — cole o erro e peça o conserto.

Versões em inglês e espanhol em `prompts/en/` e `prompts/es/`.

## Conversar por voz com um modelo local

O painel funciona sozinho. Para conversar por voz com um modelo que roda na sua GPU, use o kit irmão
**[jarvis-local](https://inematds.github.io/jarvis-local/guia/)** e cole o `prompts/jarvis-personalidade.md` como instrução.

## Testes

```bash
python3 -m unittest discover tests
```

(ou `python3 -m pytest -q`, se tiver o pytest)

Rodam sem rede: coleta com saídas do `systemctl` simuladas, item ilegível que vira "exemplo", pendências em markdown,
filas, modo anônimo e o `bom_dia.py` sem Ollama.

## Licença

MIT. Conteúdo aberto do [INEMA.CLUB](https://inema.club).
