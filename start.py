
import subprocess
import sys
import os
import platform
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND_DIR = ROOT / "src" / "backend"
FRONTEND_DIR = ROOT / "src" / "frontend"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def log(prefix: str, msg: str, color: str = RESET) -> None:
    print(f"{color}[{prefix}]{RESET} {msg}")


def check_python_version() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 11):
        log("ERROR", f"Python >= 3.11 required, got {major}.{minor}", RED)
        sys.exit(1)
    log("Python", f"OK — {major}.{minor}", GREEN)


def check_node() -> None:
    node = shutil.which("node")
    if not node:
        log("ERROR", "Node.js not found. Please install Node.js >= 18.", RED)
        sys.exit(1)
    result = subprocess.run(["node", "--version"], capture_output=True, text=True)
    log("Node", f"OK — {result.stdout.strip()}", GREEN)


def check_env() -> None:
    use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper()
    if use_vertex == "TRUE":
        creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        project = os.environ.get("VERTEX_AI_PROJECT_ID")
        if not creds or not project:
            log("WARN", "GOOGLE_GENAI_USE_VERTEXAI=TRUE but GOOGLE_APPLICATION_CREDENTIALS or VERTEX_AI_PROJECT_ID missing", YELLOW)
    else:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            log("WARN", "GOOGLE_API_KEY not set. Backend ADK calls may fail.", YELLOW)
        else:
            log("Env", "GOOGLE_API_KEY found (dev mode)", GREEN)


def start_backend() -> subprocess.Popen:
    log("Backend", f"Starting FastAPI on http://localhost:8000 …", CYAN)
    env = os.environ.copy()
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"]
    return subprocess.Popen(cmd, cwd=str(BACKEND_DIR), env=env)


def start_frontend() -> subprocess.Popen:
    log("Frontend", f"Starting Next.js on http://localhost:3000 …", CYAN)
    npm = "npm.cmd" if platform.system() == "Windows" else "npm"
    return subprocess.Popen([npm, "run", "dev"], cwd=str(FRONTEND_DIR))


def main() -> None:
    print(f"\n{GREEN}🐨 Koala — 启动中…{RESET}\n")

    check_python_version()
    check_node()
    check_env()

    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        example = BACKEND_DIR / ".env.example"
        if example.exists():
            log("WARN", f".env not found in {BACKEND_DIR}. Copy .env.example and fill in values.", YELLOW)

    backend = start_backend()
    frontend = start_frontend()

    log("Ready", "Both services started. Press Ctrl+C to stop.", GREEN)
    print(f"\n  {CYAN}后端:{RESET} http://localhost:8000")
    print(f"  {CYAN}前端:{RESET} http://localhost:3000\n")

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        log("Shutdown", "Stopping services…", YELLOW)
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
        log("Shutdown", "Done.", GREEN)


if __name__ == "__main__":
    main()
