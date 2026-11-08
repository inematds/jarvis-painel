# Conserta a tela (cole o erro)

Se o painel abriu em branco, travou ou mostrou erro, abra o Claude Code (ou o Codex) na pasta `jarvis-painel`
e cole isto, trocando a parte do erro:

```
O painel do Jarvis (index.html + estado.json, nesta pasta) não está funcionando.
O que aparece: <descreva o que você vê na tela>
O erro (copie do console do navegador, tecla F12 → Console, ou do terminal):
<cole o erro aqui>
Descubra a causa, corrija só o necessário e me explique em 3 linhas o que mudou.
Não apague o estado.json nem o config.json. Depois rode: python3 -m pytest -q
```
