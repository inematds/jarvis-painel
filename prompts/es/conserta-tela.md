Aquí está el texto que vas a pegar en el modelo: traduce también el contenido de los bloques de código. Ejemplo de ciudad: usa una ciudad del idioma (en: Austin; es: Bogotá). En la personalidad, el idioma de las respuestas pasa a ser el de esta traducción. Archivo Markdown. Conserva el formato Markdown, los bloques de código ``` idénticos (traduce solo los comentarios), los enlaces y las tablas.

# Arregla la pantalla (pega el error)

Si el panel se abrió en blanco, se quedó bloqueado o mostró un error, abre Claude Code (o Codex) en la carpeta `jarvis-painel`
y pega esto, reemplazando la parte del error:

```
El panel de Jarvis (index.html + estado.json, en esta carpeta) no está funcionando.
Lo que aparece: <describe lo que ves en la pantalla>
El error (cópialo de la consola del navegador, tecla F12 → Console, o del terminal):
<pega el error aquí>
Descubre la causa, corrige solo lo necesario y explícame en 3 líneas qué cambió.
No borres estado.json ni config.json. Después ejecuta: python3 -m pytest -q
