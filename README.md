# Llama.cpp Dashboard

A lightweight terminal UI to start and stop multiple `llama.cpp` models on port `9276` (or the next free port).

## Features
- List configured models with status.
- Start / stop individual models.
- Add models via command line or via the UI.
- Persist configuration in `~/.llama_dashboard.json`.
- Simple to extend: add more command‑line options or UI actions.

## Installation
```bash
pip install -r requirements.txt
# Ensure the llama.cpp binary (e.g. `main`) is in the current directory or in $PATH
```

## Usage
```bash
# Add a model from the command line
python llama_dashboard.py add /path/to/model.gguf --name MyModel

# Start the dashboard UI
python llama_dashboard.py run
```

Inside the UI:
- `a` – add a new model via prompt.
- `s` – start the selected model.
- `t` – stop the selected model.
- `q` – quit.

## Extending
- To change the default port, edit `DEFAULT_PORT` in `llama_dashboard.py`.
- To add more UI actions, edit the `BINDINGS` list in the `Dashboard` class.
- To integrate with GitHub, you can push this repository after creating one.

---

Feel free to contribute or open issues.
