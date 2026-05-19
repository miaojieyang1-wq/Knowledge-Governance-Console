# -*- coding: utf-8 -*-
"""Windows executable launcher for the Knowledge Governance Console."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8501
STARTUP_TIMEOUT_SECONDS = 30


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
    return config


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
    preferred_port = int(config.get("launch_port", str(DEFAULT_PORT)) or DEFAULT_PORT)
    port = choose_port(host, preferred_port)
    python_exe = root / "streamlit-ai-app-py-requirements-txt" / ".venv" / "Scripts" / "python.exe"
    app_file = root / "app.py"

    if not app_file.exists():
        print(f"[ERROR] Cannot find app.py in: {root}")
        input("Press Enter to exit...")
        return 1
    if not python_exe.exists():
        print("[ERROR] Cannot find project Python runtime:")
        print(str(python_exe))
        input("Press Enter to exit...")
        return 1

    url = f"http://{host}:{port}"
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
        if wait_for_port(host, port, STARTUP_TIMEOUT_SECONDS):
            webbrowser.open(url)
        else:
            print(f"[WARN] Server did not respond within {STARTUP_TIMEOUT_SECONDS} seconds.")
            print("If Streamlit is still starting, open the URL manually later.")
        return process.wait()
    except KeyboardInterrupt:
        print("\nConsole stopped.")
        process.terminate()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
