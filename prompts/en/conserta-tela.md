# Fix the screen (paste the error)

If the panel opened to a blank screen, froze, or showed an error, open Claude Code (or Codex) in the `jarvis-painel` folder
and paste this, replacing the error section:

```
The Jarvis panel (index.html + estado.json, in this folder) isn't working.
What appears: <describe what you see on screen>
The error (copy it from the browser console, F12 → Console, or the terminal):
<paste the error here>
Find the cause, fix only what's necessary, and explain in 3 lines what changed.
Don't delete estado.json or config.json. Then run: python3 -m pytest -q
