import os
import platform
import subprocess
from pathlib import Path

def executable_path(root):
    suffix = ".exe" if os.name == "nt" else ""
    return Path(root) / "cpp" / f"inventory_engine{suffix}"

def ensure_engine(root):
    root = Path(root)
    source = root / "cpp" / "inventory_engine.cpp"
    exe = executable_path(root)
    if exe.exists() and exe.stat().st_mtime >= source.stat().st_mtime:
        return True, "C++ engine is ready."
    compiler = "g++"
    try:
        result = subprocess.run(
            [compiler, "-std=c++17", "-O2", str(source), "-o", str(exe)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0 and exe.exists():
            return True, "C++ engine compiled successfully."
        return False, result.stderr.strip() or "C++ compilation failed."
    except FileNotFoundError:
        return False, "g++ was not found. Install a C++ compiler and follow README.md."
    except Exception as exc:
        return False, str(exc)

def run_engine(root, command, csv_path, argument=""):
    exe = executable_path(root)
    if not exe.exists():
        return ""
    args = [str(exe), command, str(csv_path)]
    if argument != "":
        args.append(str(argument))
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return ""
        return result.stdout
    except Exception:
        return ""
