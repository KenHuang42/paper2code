"""
run_code.py - Sandbox execution of generated code with dependency management.

Creates a temporary virtual environment, installs dependencies, runs a smoke test,
and captures structured output.

Usage:
    python run_code.py --code-dir ./src --timeout 120
    python run_code.py --code-dir ./src --timeout 120 --entry train.py

Output: JSON result to stdout with keys:
  - success: bool
  - exit_code: int
  - stdout: str
  - stderr: str
  - error_type: str or null
  - error_summary: str or null
  - dependencies: list of detected packages
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import shutil


STDLIB_MODULES = {
    "abc", "argparse", "ast", "asyncio", "base64", "binascii", "builtins",
    "calendar", "collections", "concurrent", "configparser", "contextlib",
    "copy", "csv", "ctypes", "dataclasses", "datetime", "decimal", "difflib",
    "email", "enum", "errno", "fnmatch", "functools", "gc", "getpass", "glob",
    "gzip", "hashlib", "heapq", "hmac", "html", "http", "importlib", "inspect",
    "io", "itertools", "json", "keyword", "logging", "lzma", "math", "mimetypes",
    "multiprocessing", "numbers", "operator", "os", "pathlib", "pickle", "platform",
    "pprint", "queue", "random", "re", "shutil", "signal", "socket", "sqlite3",
    "ssl", "string", "struct", "subprocess", "sys", "tempfile", "textwrap",
    "threading", "time", "timeit", "token", "tokenize", "traceback", "types",
    "typing", "unittest", "urllib", "uuid", "warnings", "weakref", "xml", "zipfile",
}

PACKAGE_MAP = {
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "PIL": "Pillow",
    "yaml": "pyyaml",
    "np": "numpy",
    "pd": "pandas",
    "plt": "matplotlib",
    "sns": "seaborn",
    "tqdm": "tqdm",
    "transformers": "transformers",
    "datasets": "datasets",
    "wandb": "wandb",
    "tensorboard": "tensorboard",
    "torchvision": "torchvision",
    "torchaudio": "torchaudio",
    "torchtext": "torchtext",
    "torch": "torch",
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "keras": "keras",
    "fitz": "PyMuPDF",
    "sacrebleu": "sacrebleu",
}


def detect_dependencies(code_dir):
    imports = set()
    for root, dirs, files in os.walk(code_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            for match in re.finditer(r"^\s*import\s+(\w+)", content, re.MULTILINE):
                imports.add(match.group(1))
            for match in re.finditer(r"^\s*from\s+(\w+)", content, re.MULTILINE):
                imports.add(match.group(1))

    deps = set()
    for imp in imports:
        if imp in STDLIB_MODULES:
            continue
        pkg = PACKAGE_MAP.get(imp, imp)
        deps.add(pkg)

    return sorted(deps)


def find_entry_point(code_dir, entry=None):
    if entry:
        path = os.path.join(code_dir, entry)
        if os.path.exists(path):
            return path
        return None

    candidates = ["train.py", "main.py", "run.py", "test.py"]
    for c in candidates:
        path = os.path.join(code_dir, c)
        if os.path.exists(path):
            return path

    for fname in os.listdir(code_dir):
        if fname.endswith(".py"):
            return os.path.join(code_dir, fname)

    return None


def create_smoke_test(code_dir, entry_point):
    with open(entry_point, "r", encoding="utf-8") as f:
        content = f.read()

    if "if __name__" in content:
        return entry_point, False

    smoke_path = os.path.join(code_dir, "_smoke_test.py")
    smoke_code = f"""import sys
import os
sys.path.insert(0, os.path.dirname("{entry_point}"))

try:
    exec(open("{entry_point}").read())
except SystemExit:
    pass
except Exception as e:
    print(f"SMOKE_TEST_ERROR: {{type(e).__name__}}: {{e}}", file=sys.stderr)
    raise
"""
    with open(smoke_path, "w", encoding="utf-8") as f:
        f.write(smoke_code)

    return smoke_path, True


def run_in_venv(code_dir, entry_point, dependencies, timeout):
    venv_dir = tempfile.mkdtemp(prefix="paper2code_venv_")

    try:
        print(f"[run] Creating venv: {venv_dir}", file=sys.stderr)
        result = subprocess.run(
            [sys.executable, "-m", "venv", venv_dir],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return {"success": False, "error_type": "VenvError", "error_summary": result.stderr}

        if sys.platform == "win32":
            pip_path = os.path.join(venv_dir, "Scripts", "pip")
            python_path = os.path.join(venv_dir, "Scripts", "python")
        else:
            pip_path = os.path.join(venv_dir, "bin", "pip")
            python_path = os.path.join(venv_dir, "bin", "python")

        if dependencies:
            print(f"[run] Installing deps: {dependencies}", file=sys.stderr)
            result = subprocess.run(
                [pip_path, "install"] + dependencies,
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                return {
                    "success": False,
                    "error_type": "InstallError",
                    "error_summary": result.stderr[-2000:],
                    "dependencies": dependencies,
                }

        print(f"[run] Executing: {entry_point}", file=sys.stderr)
        result = subprocess.run(
            [python_path, entry_point],
            capture_output=True, text=True, timeout=timeout,
            cwd=code_dir,
            env={**os.environ, "PYTHONPATH": code_dir}
        )

        output = {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[-5000:],
            "stderr": result.stderr[-5000:],
            "dependencies": dependencies,
        }

        if result.returncode != 0:
            stderr = result.stderr
            error_match = re.search(r"(\w+Error):\s*(.+?)(?:\n|$)", stderr)
            if error_match:
                output["error_type"] = error_match.group(1)
                output["error_summary"] = error_match.group(2).strip()
            else:
                output["error_type"] = "UnknownError"
                output["error_summary"] = stderr[-500:].strip()

        return output

    except subprocess.TimeoutExpired:
        return {"success": False, "error_type": "Timeout", "error_summary": f"Execution timed out after {timeout}s"}
    finally:
        shutil.rmtree(venv_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Run generated code in a sandbox")
    parser.add_argument("--code-dir", required=True, help="Directory containing source files")
    parser.add_argument("--timeout", type=int, default=120, help="Execution timeout in seconds")
    parser.add_argument("--entry", default=None, help="Entry point file (default: auto-detect)")
    parser.add_argument("--skip-venv", action="store_true", help="Skip venv creation (use current env)")
    args = parser.parse_args()

    if not os.path.isdir(args.code_dir):
        print(json.dumps({"success": False, "error_type": "FileError", "error_summary": f"Directory not found: {args.code_dir}"}))
        sys.exit(1)

    dependencies = detect_dependencies(args.code_dir)
    print(f"[run] Detected dependencies: {dependencies}", file=sys.stderr)

    entry_point = find_entry_point(args.code_dir, args.entry)
    if not entry_point:
        print(json.dumps({"success": False, "error_type": "FileError", "error_summary": "No entry point found"}))
        sys.exit(1)

    print(f"[run] Entry point: {entry_point}", file=sys.stderr)

    smoke_entry, is_temp = create_smoke_test(args.code_dir, entry_point)

    try:
        if args.skip_venv:
            result = subprocess.run(
                [sys.executable, smoke_entry],
                capture_output=True, text=True, timeout=args.timeout,
                cwd=args.code_dir
            )
            output = {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout[-5000:],
                "stderr": result.stderr[-5000:],
                "dependencies": dependencies,
            }
        else:
            output = run_in_venv(args.code_dir, smoke_entry, dependencies, args.timeout)
    except subprocess.TimeoutExpired:
        output = {"success": False, "error_type": "Timeout", "error_summary": f"Timed out after {args.timeout}s"}
    finally:
        if is_temp and os.path.exists(smoke_entry):
            os.remove(smoke_entry)

    print(json.dumps(output, indent=2))
    sys.exit(0 if output.get("success") else 1)


if __name__ == "__main__":
    main()
