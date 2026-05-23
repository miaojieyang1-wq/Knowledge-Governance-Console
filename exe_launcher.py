# -*- coding: utf-8 -*-
"""Windows executable launcher for the Knowledge Governance Console."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import webbrowser
import os
from datetime import datetime
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8501
DEFAULT_STARTUP_TIMEOUT_SECONDS = 30
ERROR_EXIT_DELAY_SECONDS = 12
CONFIG_ENV_KEYS = {
    "launch_host": "KG_LAUNCH_HOST",
    "launch_port": "KG_LAUNCH_PORT",
    "launch_timeout_seconds": "KG_LAUNCH_TIMEOUT_SECONDS",
}


def write_log(root: Path, message: str) -> None:
    log_path = root / "launcher.log"
    timestamp = datetime.now().isoformat(timespec="seconds")
    try:
        with log_path.open("a", encoding="utf-8", newline="\n") as file_obj:
            file_obj.write(f"[{timestamp}] {message}\n")
    except OSError:
        pass


def show_error(root: Path, message: str) -> None:
    print(f"[ERROR] {message}")
    write_log(root, f"ERROR {message}")
    print(f"This window will close in {ERROR_EXIT_DELAY_SECONDS} seconds.")
    time.sleep(ERROR_EXIT_DELAY_SECONDS)


def find_project_root() -> Path:
    current = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
    candidates = [current, current.parent]
    for candidate in candidates:
        if (candidate / "app.py").exists():
            return candidate
    return current


def read_simple_config(root: Path) -> dict[str, str]:
    config_path = root / "config.yaml"
    config: dict[str, str] = {}
    if not config_path.exists():
        return config
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        config[key.strip()] = value.strip().strip("\"'")
    config.update({key: os.environ[env_key] for key, env_key in CONFIG_ENV_KEYS.items() if os.environ.get(env_key)})
    return config


def parse_config_int(config: dict[str, str], key: str, default: int) -> int:
    raw_value = config.get(key, str(default)) or str(default)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer config value for {key}: {raw_value}") from exc


def is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_socket.bind((host, port))
        except OSError:
            return False
    return True


def choose_port(host: str, preferred_port: int) -> int:
    for port in range(preferred_port, preferred_port + 50):
        if is_port_available(host, port):
            return port
    raise RuntimeError(f"No available local port found from {preferred_port} to {preferred_port + 49}.")


def wait_for_port(host: str, port: int, timeout_seconds: int) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(0.5)
            if client_socket.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.5)
    return False


def main() -> int:
    root = find_project_root()
    config = read_simple_config(root)
    host = config.get("launch_host", DEFAULT_HOST)
    try:
        preferred_port = parse_config_int(config, "launch_port", DEFAULT_PORT)
        startup_timeout = parse_config_int(config, "launch_timeout_seconds", DEFAULT_STARTUP_TIMEOUT_SECONDS)
        port = choose_port(host, preferred_port)
    except (RuntimeError, ValueError) as exc:
        show_error(root, str(exc))
        return 1
    python_exe = root / "streamlit-ai-app-py-requirements-txt" / ".venv" / "Scripts" / "python.exe"
    app_file = root / "app.py"

    if not app_file.exists():
        show_error(root, f"Cannot find app.py in: {root}")
        return 1
    if not python_exe.exists():
        show_error(root, f"Cannot find project Python runtime: {python_exe}")
        return 1

    url = f"http://{host}:{port}"
    write_log(root, f"Starting server at {url}")
    print("Starting Knowledge Governance Console...")
    print(f"URL: {url}")
    if port != preferred_port:
        print(f"Preferred port {preferred_port} is busy; using {port} instead.")
    print("Keep this window open while using the console.")
    print("Press Ctrl+C in this window to stop the server.")
    print()

    command = [
        str(python_exe),
        "-m",
        "streamlit",
        "run",
        str(app_file),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        "false",
        "--browser.gatherUsageStats",
        "false",
    ]
    process = subprocess.Popen(command, cwd=root)
    try:
        if wait_for_port(host, port, startup_timeout):
            webbrowser.open(url)
            write_log(root, f"Server ready at {url}")
        else:
            print(f"[WARN] Server did not respond within {startup_timeout} seconds.")
            print("If Streamlit is still starting, open the URL manually later.")
            write_log(root, f"WARN server not ready after {startup_timeout} seconds")
        return process.wait()
    except KeyboardInterrupt:
        print("\nConsole stopped.")
        write_log(root, "Console stopped by user")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
