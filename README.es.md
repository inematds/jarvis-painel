# jarvis-painel — el panel de tu Jarvis

[![jarvis-painel](guia/assets/banner-es.jpg)](https://inematds.github.io/jarvis-painel/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

> Tus robots trabajan. Tú no lo ves. Una pantalla lo muestra todo y te da los buenos días.

## Qué es

El jarvis-painel es una pantalla de estilo ciencia ficción que reúne, en un solo lugar, todo lo que funciona automáticamente en tu
computadora: los timers de Linux, colas y archivos de registro. Sirve para quienes tienen robots, rutinas y colas trabajando y
no saben qué hizo cada uno ni qué está esperando por ti. Muestra quién terminó bien, quién falló y tu
lista de pendientes, y lee un resumen en voz alta en portugués. Solo necesitas Python 3 y un navegador; todo funciona
en tu máquina, sin clave ni servicio pago, y solo lee: los botones no ejecutan nada.

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/jarvis-painel/guia/es/**
Demostración en línea (modo ejemplo, sin tus datos): **https://inematds.github.io/jarvis-painel/**

## Lo que aparece en la pantalla

- **Núcleo central**: tres anillos que giran a distintas velocidades, una luz que pulsa, el nombre `JARVIS` y una línea de estado.
- **Inicio de ~3 s**: "Inicializando… Sistemas no ar. (Inicializando… Sistemas en marcha.) Bom dia (Buenos días), <nombre>."
- **Sistemas** (izquierda): cada timer, servicio y cola con un punto de estado (correcto, falló, funcionando, esperando) y la última acción.
- **Esperando você (Esperándote)** (derecha): lo que falló + los pendientes de tu archivo markdown + elementos detenidos en colas.
  Los botones **Aprovar (Aprobar)** y **Depois (Después)** solo los marcan en la pantalla (quedan guardados en el navegador). No ejecutan nada.
- **Parte superior**: reloj, fecha y el sello **Voz: ligada (Voz: activada)** (haz clic para desactivarla).
- **Barra de comandos**: **Bom dia (Buenos días) · Status (Estado) · O que espera (Qué está pendiente) · Modo foco (Modo concentración)** (teclas 1 a 4). El modo de concentración oscurece los paneles.
- **Voz** en portugués (`speechSynthesis` del navegador, elige una voz pt-BR si está disponible), una onda alrededor del núcleo
  mientras habla y el texto de la respuesta aparece escrito debajo.
- Funciona en el celular (sin desplazamiento lateral).

Un dato que no se pudo leer aparece como un elemento marcado **exemplo (ejemplo)**; nunca se inventa como si fuera real.

## El proceso, de principio a fin

Quién lo hace: 🧠 tú · ⚙️ script · 🤖 modelo de IA (opcional)

| # | Paso | Comando | Quién |
|---|---|---|---|
| 1 | Descargar el kit | `git clone https://github.com/inematds/jarvis-painel.git && cd jarvis-painel` | 🧠 |
| 2 | Indicar tu nombre, el archivo de pendientes y las colas | editar `config.json` | 🧠 |
| 3 | Leer la máquina (timers, fallas, pendientes, colas) | `python3 coletar.py` → `estado.json` | ⚙️ |
| 4 | Escribir el resumen de la mañana con reglas fijas | `python3 bom_dia.py` → `bom_dia.txt` | ⚙️ |
| 5 | (Opcional) hacer que el resumen suene más natural con el modelo local | `python3 bom_dia.py --ollama` | 🤖 |
| 6 | Abrir la pantalla | `python3 -m http.server 8000` y abrir `http://localhost:8000` | ⚙️ |
| 7 | Usar los atajos y marcar Aprovar/Depois (Aprobar/Después) | teclas 1–4 en el panel | 🧠 |
| 8 | (Opcional) actualizar automáticamente cada 5 min | línea de `crontab` de abajo | ⚙️ |
| 9 | Pedir una investigación de clientes que solo lea, o arreglar la pantalla | prompts en `prompts/es/` | 🤖 |

Necesitas Python 3.9+ y git (en Ubuntu: `sudo apt install git`).

```bash
git clone https://github.com/inematds/jarvis-painel.git
cd jarvis-painel
python3 coletar.py
python3 bom_dia.py
python3 -m http.server 8000
```

Después abre `http://localhost:8000` en el navegador y deja esa terminal abierta (Ctrl+C la detiene). Para actualizar
automáticamente (opcional), ejecuta `crontab -e` y pega la línea de abajo (funciona si el kit está en tu carpeta personal; cambia la
ruta si lo descargaste en otro lugar). `coletar.py` encuentra tus timers incluso cuando se ejecuta desde cron:

```
*/5 * * * * cd $HOME/jarvis-painel && python3 coletar.py && python3 bom_dia.py
```

La página vuelve a leer `estado.json` cada 60 segundos.

## Configurar (`config.json`)

Viene configurado para INEMA: pendientes en `~/projetos/wifi/pendencias.md` y dos colas JSON del proyecto wifi.
Cámbialo por el tuyo (`nano config.json`; si te equivocas en una coma, `coletar.py` indica la línea del error):

| Campo | Qué es |
|---|---|
| `nome` | cómo te llama Jarvis ("Bom dia, Nei." — "Buenos días, Nei.") |
| `pendencias.arquivo` | un archivo `.md` tuyo; cada línea `- **título**` o `### título` se convierte en un elemento, hasta la sección `## Resolvidas` |
| `fontes_extras` | colas (`"tipo": "fila_json"`, cuenta los elementos por `estado`) y registros (`"tipo": "log"`, muestra la última línea) |
| `ignorar` | timers y servicios que no deben aparecer (p. ej., `snap.*`) |
| `ollama` | dirección y modelo local para `bom_dia.py --ollama` |

Sin Linux con systemd (por ejemplo, en Mac), el panel muestra los sistemas como **exemplo (ejemplo)** y aun así lee los pendientes y las colas.
Para tomar una captura sin exponer tus pendientes: `python3 coletar.py --anonimo` reemplaza cada título por "Pendência N (data) (Pendiente N (fecha)".

## Qué lee (y qué nunca hace)

- Lee: `systemctl --user list-timers`, `systemctl --user show` (último resultado de cada servicio),
  `systemctl --user list-units --failed`, el archivo de pendientes y las fuentes extras de `config.json`.
- Nunca: inicia, detiene, reinicia, borra ni envía nada. Las pruebas comprueban que solo se ejecutan comandos de lectura.
- Aprovar/Depois (Aprobar/Después): solo se guardan en el `localStorage` del navegador (`jarvis-painel:marcas`).

## Prompts (`prompts/es/`)

- `jarvis-personalidade.md` — la personalidad de Jarvis (tranquilo, en portugués, no inventa números ni ejecuta nada).
- `pesquisa-clientes.md` — para Claude Code con navegador: «busca <rubro> en <ciudad>, abre los 3 primeros sitios,
  crea una tabla con nombre, sitio, teléfono y algo que el sitio hace mal; solo lee, no contactes a nadie ni rellenes formularios».
- `conserta-tela.md` — pega el error y pide que lo arregle.

Versiones en inglés y español en `prompts/en/` y `prompts/es/`.

## Conversar por voz con un modelo local

El panel funciona por sí solo. Para conversar por voz con un modelo que funciona en tu GPU, usa el kit hermano
**[jarvis-local](https://inematds.github.io/jarvis-local/guia/)** y pega `prompts/jarvis-personalidade.md` como instrucción.

## Pruebas

```bash
python3 -m unittest discover tests
```

(o `python3 -m pytest -q`, si tienes pytest)

Se ejecutan sin red: recopilación con salidas simuladas de `systemctl`, elemento ilegible que se convierte en "exemplo (ejemplo)", pendientes en markdown,
colas, modo anónimo y `bom_dia.py` sin Ollama.

## Licencia

MIT. Contenido abierto de [INEMA.CLUB](https://inema.club).
