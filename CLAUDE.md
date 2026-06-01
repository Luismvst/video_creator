# VideoZero — agent instructions (GSD)

Este repositorio usa **Get Shit Done (GSD)**. Contexto vivo del producto y del trabajo:

- **Proyecto:** [.planning/PROJECT.md](.planning/PROJECT.md)
- **Requisitos v1:** [.planning/REQUIREMENTS.md](.planning/REQUIREMENTS.md)
- **Roadmap:** [.planning/ROADMAP.md](.planning/ROADMAP.md)
- **Estado:** [.planning/STATE.md](.planning/STATE.md)
- **Config GSD:** [.planning/config.json](.planning/config.json)
- **Especificación de producto:** [docs/VIDEOZERO-MASTER.md](docs/VIDEOZERO-MASTER.md)

**Uso típico = CLI** (sesión guiada en consola): `python -m app.cli_session [letra.txt] [-o informe.md]`. Es el camino principal y soportado; API y frontend son opcionales (ver `README.md`). La capa de **prompting de dirección F6** (biblia visual estructurada + prompt por capas + tuning por proveedor — `visual_bible.py`, `prompt_compile.py`) está implementada y cubierta por tests.

Siguiente: pulir prompting de dirección (DIRQ-03/04/07 restantes) o conectar render real (`--run` + `FAL_KEY`).

No implementar código fuera del alcance de la fase activa; respetar **Out of Scope** en `PROJECT.md`.
