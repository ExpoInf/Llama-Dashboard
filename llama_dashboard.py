#!/usr/bin/env python3
"""
Llama.cpp dashboard TUI.

Usage:
  python llama_dashboard.py run            # start the dashboard
  python llama_dashboard.py add <model_path> [--name NAME]  # add a model to the list

The dashboard shows the list of configured models and lets you start/stop them.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from textual.app import App
from textual.widgets import DataTable, Header, Footer, Button, Input
from textual.reactive import reactive
from textual import events

CONFIG_FILE = Path.home() / ".llama_dashboard.json"
DEFAULT_PORT = 9276

# Load or init config
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
else:
    CONFIG = {"models": []}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, indent=2)

# Helper to save config

def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, indent=2)

# Find next available port for a new model

def next_port():
    used = {m.get("port") for m in CONFIG["models"] if m.get("port")}
    port = DEFAULT_PORT
    while port in used:
        port += 1
    return port

# Start a model

def start_model(idx: int):
    model = CONFIG["models"][idx]
    if model.get("pid"):
        return  # already running
    cmd = ["./main", "-m", str(model["path"]), "-p", str(model["port"])]
    # Assume llama.cpp binary is in current dir or PATH
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    model["pid"] = proc.pid
    save_config()

# Stop a model

def stop_model(idx: int):
    model = CONFIG["models"][idx]
    pid = model.get("pid")
    if not pid:
        return
    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        pass
    model["pid"] = None
    save_config()

class Dashboard(App):
    CSS_PATH = None
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "add", "Add model"),
        ("s", "start", "Start selected"),
        ("t", "stop", "Stop selected"),
    ]
    selected: reactive[int | None] = reactive(None)

    def compose(self):
        yield Header(show_clock=True)
        yield DataTable(id="table")
        yield Footer()

    async def on_mount(self):
        table = self.query_one("#table", DataTable)
        table.add_columns("Name", "Path", "Port", "Status")
        self.refresh_table()
        table.cursor_type = "row"
        table.focus()

    def refresh_table(self):
        table = self.query_one("#table", DataTable)
        table.clear()
        for idx, m in enumerate(CONFIG["models"]):
            status = "Running" if m.get("pid") else "Stopped"
            table.add_row(m["name"], str(m["path"]), str(m.get("port", "")), status)

    async def action_quit(self):
        await self.shutdown()

    async def action_add(self):
        # Prompt user for path via Input
        await self.push_screen(AddScreen(self))

    async def action_start(self):
        table = self.query_one("#table", DataTable)
        if table.cursor_row is None:
            return
        idx = table.cursor_row
        start_model(idx)
        self.refresh_table()

    async def action_stop(self):
        table = self.query_one("#table", DataTable)
        if table.cursor_row is None:
            return
        idx = table.cursor_row
        stop_model(idx)
        self.refresh_table()

class AddScreen(events.Screen):
    def __init__(self, parent: Dashboard):
        super().__init__()
        self.parent = parent

    async def on_mount(self):
        self.input = Input(placeholder="Path to .gguf model")
        self.name_input = Input(placeholder="Optional model name")
        self.button = Button("Add", variant="primary")
        await self.view.dock(self.input, edge="top")
        await self.view.dock(self.name_input, edge="top")
        await self.view.dock(self.button, edge="top")
        await self.button.focus()

    async def on_button_pressed(self, event: Button.Pressed):
        path = self.input.value.strip()
        if not path:
            return
        name = self.name_input.value.strip() or Path(path).stem
        model = {
            "name": name,
            "path": path,
            "port": next_port(),
            "pid": None,
        }
        CONFIG["models"].append(model)
        save_config()
        self.parent.refresh_table()
        await self.app.pop_screen()


def main():
    parser = argparse.ArgumentParser(description="Llama.cpp dashboard")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="Run the dashboard UI")
    addp = sub.add_parser("add", help="Add a model via CLI")
    addp.add_argument("path", help="Path to .gguf model file")
    addp.add_argument("--name", help="Optional friendly name")
    args = parser.parse_args()

    if args.cmd == "run":
        Dashboard().run()
    elif args.cmd == "add":
        name = args.name or Path(args.path).stem
        model = {
            "name": name,
            "path": args.path,
            "port": next_port(),
            "pid": None,
        }
        CONFIG["models"].append(model)
        save_config()
        print(f"Added model {name} at port {model['port']}")

if __name__ == "__main__":
    main()
