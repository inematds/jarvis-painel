# jarvis-painel — el panel de tu Jarvis

[![jarvis-painel](guia/assets/banner-es.jpg)](https://inematds.github.io/jarvis-painel/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

> Tus robots trabajan. Tú no lo ves. Una pantalla lo muestra todo y te da los buenos días.

## Qué es

El jarvis-painel es una pantalla de estilo de ciencia ficción que reúne en un solo lugar todo lo que funciona por su cuenta en tu computadora: los temporizadores de Linux, las colas y los archivos de registro. Es para quienes tienen robots, rutinas y colas trabajando y no saben qué hizo cada uno ni qué está esperando por ti. Muestra qué terminó bien, qué falló y tu lista de pendientes, y lee un resumen en voz alta en portugués. Solo necesitas Python 3 y un navegador; todo funciona en tu máquina, sin clave ni servicio de pago, y solo lee: los botones no ejecutan nada.

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/jarvis-painel/guia/es/**  
Demostración en línea (modo de ejemplo, sin tus datos): **https://inematds.github.io/jarvis-painel/**

## Lo que aparece en la pantalla

- **Núcleo central**: tres anillos que giran a distintas velocidades, luz pulsante, el nombre `JARVIS` y una línea de estado.
- **Inicio de ~3 s**: "Inicializando… Sistemas no ar. (Inicializando… Sistemas en línea.) Bom dia (Buenos días), <nombre>."
- **Sistemas** (izquierda): cada temporizador, servicio y cola con un punto de estado (correcto, falló, en ejecución, en espera) y la última acción.
- **Esperando você (Esperándote)** (derecha): lo que falló + las pendientes de tu archivo markdown + los elementos detenidos en las colas.
  Los botones **Aprovar (Aprobar)** y **Depois (Después)** solo marcan en la pantalla (se guardan en el navegador). No ejecutan nada.
- **Parte superior**: reloj, fecha y el sello **Voz: ligada (Voz: activada)** (haz clic para desactivarla).
- **Barra de comandos**: **Bom dia (Buenos días) · Status (Estado) · O que espera (Qué está pendiente) · Modo foco (Modo concentración)** (teclas 1 a 4). El modo concentración oscurece los paneles.
- **Voz** en portugués (`speechSynthesis` del navegador; elige una voz pt-BR si hay una), una onda alrededor del núcleo mientras habla y el texto de la respuesta aparece escrito debajo.
- Funciona en el celular (sin desplazamiento lateral).

Los datos que no se pudieron leer aparecen marcados como **exemplo (ejemplo)**; nunca se inventan como si fueran reales.

## El proceso, de principio a fin

Quién lo hace: 🧠 tú · ⚙️ script · 🤖 modelo de IA (opcional)

| # | Paso | Comando | Quién |
|---|---|---|---|
| 1 | Descargar el kit | `git clone https://github.com/inematds/jarvis-painel.git && cd jarvis-painel` | 🧠 |
| 2 | Indicar tu nombre, el archivo de pendientes y las colas | editar `config.json` | 🧠 |
| 3 | Leer la máquina (temporizadores, fallas, pendientes, colas) | `python3 coletar.py` → `estado.json` | ⚙️ |
| 4 | Escribir el resumen de la mañana siguiendo una regla fija | `python3 bom_dia.py` → `bom_dia.txt` | ⚙️ |
| 5 | (Opcional) hacer que el resumen suene más natural con el modelo local | `python3 bom_dia.py --ollama` | 🤖 |
| 6 | Abrir la pantalla | `python3 -m http.server 8000` y abrir `http://localhost:8000` | ⚙️ |
| 7 | Usar los atajos y marcar Aprovar/Depois | teclas 1–4 en el panel | 🧠 |
| 8 | (Opcional) actualizar automáticamente cada 5 min | línea de `crontab` de abajo | ⚙️ |
| 9 | Pedir una búsqueda de clientes solo de lectura o corregir la pantalla | prompts en `prompts/es/` | 🤖 |

```bash
git clone https://github.com/inematds/jarvis-painel.git
cd jarvis-painel
python3 coletar.py
python3 bom_dia.py
python3 -m http.server 8000
```

Después abre `http://localhost:8000` en el navegador. Para actualizar automáticamente (opcional), ejecuta `crontab -e` y pega
la línea de abajo, cambiando la ruta por la carpeta donde lo descargaste:

```
*/5 * * * * cd $HOME/jarvis-painel && python3 coletar.py && python3 bom_dia.py
```

La página vuelve a leer `estado.json` cada 60 segundos.

## Configurar (`config.json`)

Viene configurado para INEMA: pendientes en `~/projetos/wifi/pendencias.md` y dos colas JSON del proyecto wifi.
Cámbialo por el tuyo:

| Campo | Qué es |
|---|---|
| `nome` | cómo te llama Jarvis ("Bom dia, Nei." (Buenos días, Nei.)) |
| `pendencias.arquivo` | un archivo `.md` tuyo; cada línea `- **título**` o `### título` se convierte en un elemento, hasta la sección `## Resolvidas` |
| `fontes_extras` | colas (`"tipo": "fila_json"`, cuenta los elementos por `estado`) y registros (`"tipo": "log"`, muestra la última línea) |
| `ignorar` | temporizadores y servicios que no deben aparecer (p. ej., `snap.*`) |
| `ollama` | dirección y modelo local para `bom_dia.py --ollama` |

Sin Linux con systemd (por ejemplo, en Mac), el panel muestra los sistemas como **exemplo (ejemplo)** y sigue leyendo las pendientes y las colas.
Para tomar una captura de pantalla sin exponer tus pendientes: `python3 coletar.py --anonimo` cambia cada título por "Pendência N (data) (Pendiente N (fecha))".

## Lo que lee (y lo que nunca hace)

- Lee: `systemctl --user list-timers`, `systemctl --user show` (último resultado de cada servicio),
  `systemctl --user list-units --failed`, el archivo de pendientes y las fuentes adicionales de `config.json`.
- Nunca: inicia, detiene, reinicia, borra ni envía nada. Las pruebas verifican que solo se llamen comandos de lectura.
- Aprovar/Depois (Aprobar/Después): solo guardan marcas en el `localStorage` del navegador (`jarvis-painel:marcas`).

## Prompts (`prompts/`)

- `jarvis-personalidade.md` — la personalidad de Jarvis (tranquilo, en portugués, no inventa números, no ejecuta nada).
- `pesquisa-clientes.md` — para Claude Code con navegador: "busca <sector> en <ciudad>, abre los 3 primeros sitios,
  crea una tabla con nombre, sitio, teléfono y algo que el sitio hace mal; solo lee, no contactes a nadie ni llenes formularios".
- `conserta-tela.md` — pega el error y pide que lo corrija.

Versiones en inglés y español en `prompts/en/` y `prompts/es/`.

## Conversar por voz con un modelo local

El panel funciona por sí solo. Para conversar por voz con un modelo que funciona en tu GPU, usa el kit hermano
**[jarvis-local](https://inematds.github.io/jarvis-local/guia/)** y pega `prompts/jarvis-personalidade.md` como instrucción.

## Pruebas

```bash
python3 -m pytest -q
```

Funcionan sin conexión: recopilación con resultados simulados de `systemctl`, elemento ilegible que aparece como "exemplo (ejemplo)", pendientes en markdown,
colas, modo anónimo y `bom_dia.py` sin Ollama.

## Licencia

MIT. Contenido abierto de [INEMA.CLUB](https://inema.club).
