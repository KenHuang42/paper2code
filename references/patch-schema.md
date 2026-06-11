# Patch Schema Definition

This document defines the JSON format for `patches.json`, used by `scripts/ast_patch.py` to apply targeted code modifications.

## Top-Level Structure

```json
[
  {"file": "model.py", "action": "add_import", "code": "import torch.nn.functional as F"},
  {"file": "model.py", "action": "insert_after", "line": 42, "code": "x = x.view(x.size(0), -1)"},
  {"file": "model.py", "action": "replace_line", "line": 50, "code": "x = F.relu(x)"},
  {"file": "model.py", "action": "replace_function", "function": "forward", "code": "def forward(self, x):\n    ..."},
  {"file": "train.py", "action": "delete_lines", "start_line": 30, "end_line": 32}
]
```

The root is a JSON array of patch objects. Patches are applied **in array order**.

## Patch Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | Yes | Target filename relative to `--code-dir` (e.g., `model.py`). |
| `action` | string | Yes | One of the supported actions listed below. |
| `code` | string | Yes for `add_import`, `insert_after`, `insert_before`, `replace_line`, `replace_function` | Source code to insert or replace. Newlines must be escaped as `\n`. |
| `line` | integer | Yes for `insert_after`, `insert_before`, `replace_line` | **1-indexed** line number in the target file. |
| `function` | string | Yes for `replace_function` | Name of the function to replace (used by AST matcher, not line-based). |
| `start_line` | integer | Yes for `delete_lines` | **1-indexed** first line to delete. |
| `end_line` | integer | Yes for `delete_lines` | **1-indexed** last line to delete (inclusive). |

## Supported Actions

### `add_import`
Insert a new import statement at the top of the file, after existing imports but before other code.

```json
{"file": "model.py", "action": "add_import", "code": "import torch.nn.functional as F"}
```

- If the import already exists, the patch is a no-op (no duplicate).
- The `code` field should be a single import statement.

### `insert_after`
Insert `code` after the specified line.

```json
{"file": "model.py", "action": "insert_after", "line": 42, "code": "x = x.view(x.size(0), -1)"}
```

- `line` is **1-indexed**.
- Multi-line `code` is allowed; each line is inserted sequentially.

### `insert_before`
Insert `code` before the specified line.

```json
{"file": "model.py", "action": "insert_before", "line": 42, "code": "# Flatten before linear"}
```

- `line` is **1-indexed**.
- Existing content at `line` shifts down.

### `replace_line`
Replace the entire content of the specified line with `code`.

```json
{"file": "model.py", "action": "replace_line", "line": 50, "code": "x = F.relu(x)"}
```

- `line` is **1-indexed**.
- Multi-line `code` is allowed; the original single line is replaced by multiple lines.

### `replace_function`
Replace an entire function definition by matching its name via AST.

```json
{"file": "model.py", "action": "replace_function", "function": "forward", "code": "def forward(self, x):\n    ..."}
```

- The `function` field is the exact function name to match.
- The AST patcher finds the function body and replaces it with the new `code`.
- **Line numbers are ignored** — the patcher uses AST node matching, so line drift from previous patches does not affect this action.
- If multiple functions share the same name in the file, the **first match** is replaced.

### `delete_lines`
Delete a range of lines (inclusive).

```json
{"file": "train.py", "action": "delete_lines", "start_line": 30, "end_line": 32}
```

- `start_line` and `end_line` are **1-indexed** and inclusive.
- If `start_line > end_line`, the patch is invalid and the patcher should reject it.

## Execution Order Rules

1. **Patches are applied in the order they appear in the JSON array**.
2. **Line-based actions (`insert_after`, `insert_before`, `replace_line`, `delete_lines`) on the same file** should be sorted by **descending line number** (highest line first) to avoid line-number drift. It is the responsibility of the patch producer to sort them.
3. **AST-based actions (`replace_function`) do not depend on line numbers**, so they can be applied safely alongside line-based actions regardless of order.
4. **If a patch fails** (e.g., line number out of range, file not found, invalid JSON), the patcher should:
   - Report the failing patch
   - Stop applying further patches to the same file (to avoid cascading errors)
   - Continue with other files if possible
   - Exit with a non-zero status code

## JSON Escaping

The `code` field must be valid JSON string:
- Newlines must be escaped as `\n`
- Double quotes must be escaped as `\"`
- Backslashes must be escaped as `\\`

Example:
```json
{"file": "model.py", "action": "replace_function", "function": "forward", "code": "def forward(self, x):\n    x = self.encoder(x)\n    x = torch.relu(x)\n    return self.decoder(x)"}
```

## Validation Checklist

Before writing `patches.json`, verify:
- [ ] Every object has a valid `action` value.
- [ ] Required fields (`line`, `code`, `function`, `start_line`, `end_line`) are present for the chosen action.
- [ ] `line` values are 1-indexed and within the file's current line count.
- [ ] For multi-patch operations on the same file, patches are sorted by descending `line` number.
- [ ] All `code` strings are properly JSON-escaped.

(End of file)
