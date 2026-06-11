"""
ast_patch.py - Apply structured AST-level patches to Python source files.

Supports:
  - add_import: Add an import statement at the top of the file
  - insert_before: Insert code before a specific line number
  - insert_after: Insert code after a specific line number
  - replace_function: Replace an entire function body
  - replace_line: Replace a specific line

Usage:
    python ast_patch.py --code-dir ./src --patches patches.json

Patches JSON format:
[
  {"file": "model.py", "action": "add_import", "code": "import torch.nn.functional as F"},
  {"file": "model.py", "action": "insert_after", "line": 42, "code": "x = x.view(x.size(0), -1)"},
  {"file": "model.py", "action": "insert_before", "line": 42, "code": "# fix shape"},
  {"file": "model.py", "action": "replace_function", "function": "forward", "code": "def forward(self, x):\\n    return x"},
  {"file": "model.py", "action": "replace_line", "line": 42, "code": "x = self.flatten(x)"}
]
"""

import argparse
import json
import os
import re
import sys


def find_function_range(lines, func_name):
    pattern = re.compile(r"^(\s*)def\s+" + re.escape(func_name) + r"\s*\(")
    start = None
    indent = None

    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            start = i
            indent = len(m.group(1))
            break

    if start is None:
        return None, None

    end = start + 1
    while end < len(lines):
        line = lines[end]
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            end += 1
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= indent and stripped != "":
            if not stripped.startswith("@"):
                break
        end += 1

    return start, end


def apply_add_import(lines, patch):
    code = patch["code"]
    import_section_end = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            import_section_end = i + 1
        elif stripped and not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''") and import_section_end > 0:
            break

    lines.insert(import_section_end, code if code.endswith("\n") else code + "\n")
    return lines


def apply_insert_before(lines, patch):
    line_num = patch["line"]
    code = patch["code"]
    idx = line_num - 1
    if idx < 0:
        idx = 0
    if idx > len(lines):
        idx = len(lines)

    code_lines = [l + "\n" for l in code.split("\n")]
    for j, cl in enumerate(code_lines):
        lines.insert(idx + j, cl)
    return lines


def apply_insert_after(lines, patch):
    line_num = patch["line"]
    code = patch["code"]
    idx = line_num
    if idx < 0:
        idx = 0
    if idx > len(lines):
        idx = len(lines)

    code_lines = [l + "\n" for l in code.split("\n")]
    for j, cl in enumerate(code_lines):
        lines.insert(idx + j, cl)
    return lines


def apply_replace_function(lines, patch):
    func_name = patch["function"]
    code = patch["code"]
    start, end = find_function_range(lines, func_name)

    if start is None:
        print(f"  [WARN] Function '{func_name}' not found, skipping")
        return lines

    code_lines = [l + "\n" for l in code.split("\n")]
    lines[start:end] = code_lines
    return lines


def apply_replace_line(lines, patch):
    line_num = patch["line"]
    code = patch["code"]
    idx = line_num - 1
    if idx < 0 or idx >= len(lines):
        print(f"  [WARN] Line {line_num} out of range, skipping")
        return lines
    lines[idx] = code if code.endswith("\n") else code + "\n"
    return lines


def apply_patch_to_file(filepath, patches_for_file):
    if not os.path.exists(filepath):
        print(f"  [ERROR] File not found: {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    patches_for_file.sort(key=lambda p: {
        "add_import": 0,
        "replace_function": 1,
        "replace_line": 2,
        "insert_before": 3,
        "insert_after": 4,
    }.get(p["action"], 99))

    for patch in patches_for_file:
        action = patch.get("action")
        print(f"  [PATCH] {action}", end="")
        if "line" in patch:
            print(f" (line {patch['line']})", end="")
        if "function" in patch:
            print(f" (function: {patch['function']})", end="")
        print()

        if action == "add_import":
            lines = apply_add_import(lines, patch)
        elif action == "insert_before":
            lines = apply_insert_before(lines, patch)
        elif action == "insert_after":
            lines = apply_insert_after(lines, patch)
        elif action == "replace_function":
            lines = apply_replace_function(lines, patch)
        elif action == "replace_line":
            lines = apply_replace_line(lines, patch)
        else:
            print(f"  [WARN] Unknown action: {action}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return True


def main():
    parser = argparse.ArgumentParser(description="Apply AST-level patches to Python files")
    parser.add_argument("--code-dir", required=True, help="Directory containing source files")
    parser.add_argument("--patches", required=True, help="Path to patches JSON file")
    args = parser.parse_args()

    if not os.path.exists(args.patches):
        print(f"Error: Patches file not found: {args.patches}")
        sys.exit(1)

    with open(args.patches, "r", encoding="utf-8") as f:
        patches = json.load(f)

    patches_by_file = {}
    for patch in patches:
        filename = patch["file"]
        if filename not in patches_by_file:
            patches_by_file[filename] = []
        patches_by_file[filename].append(patch)

    total = 0
    success = 0
    for filename, file_patches in patches_by_file.items():
        filepath = os.path.join(args.code_dir, filename)
        print(f"[PATCH] Processing: {filename} ({len(file_patches)} patches)")
        total += len(file_patches)
        if apply_patch_to_file(filepath, file_patches):
            success += len(file_patches)

    print(f"\n[DONE] Applied {success}/{total} patches")


if __name__ == "__main__":
    main()
