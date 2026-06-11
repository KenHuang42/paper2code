# AGENTS.md — Paper2Code Project Context

This file contains background, structure, and conventions for AI agents working on this project.

## Project Overview

Paper2Code is a universal skill for converting research papers, technical documents, or plain-text descriptions into runnable PyTorch or TensorFlow code.

It uses a 6-phase pipeline:
1. Source ingestion
2. IR (Intermediate Representation) construction
3. Module planning
4. Generate & critique (debate loop)
5. AST patching
6. Execution verification

## Directory Structure

```
PaperCode/
├── SKILL.md              — Skill definition and workflow specification
├── LICENSE               — MIT License
├── README.md             — English documentation
├── README.zh.md          — Chinese documentation
├── requirements.txt      — Python dependencies
├── .gitignore            — Python standard ignore rules
├── AGENTS.md             — This file
├── references/
│   ├── ir-schema.md      — IR JSON schema with examples
│   ├── patch-schema.md   — AST patch JSON format
│   └── code-patterns.md  — PyTorch & TensorFlow idioms
└── scripts/
    ├── extract_paper.py  — PDF extraction
    ├── ast_patch.py      — AST patch application
    └── run_code.py       — Sandbox execution
```

## Coding Conventions

- **Python version**: 3.8+
- **Style**: PEP 8 compliant, no external formatter required
- **Dependencies**: Minimize external dependencies. Only `PyMuPDF` is required for PDF extraction. Everything else uses the Python standard library.
- **Error handling**: Print structured messages to stderr; use `sys.exit(1)` on fatal errors.
- **File I/O**: Always use `encoding="utf-8"` for text files.
- **Line numbers**: All line numbers in patches are **1-indexed**.

## Build & Run

No build step required. The project is a collection of Python scripts and Markdown reference files.

### Quick test
```bash
python scripts/extract_paper.py --help
python scripts/ast_patch.py --help
python scripts/run_code.py --help
```

### Install dependencies
```bash
pip install -r requirements.txt
```

## Key Design Decisions

- **IR-first**: All phases work from the structured IR, not raw source text. This reduces hallucination.
- **Isolated debate**: Generator and critic are separate subagents with separate contexts.
- **AST patching**: Preserves reviewed code; only fixes problematic sections.
- **Sandbox execution**: Uses temporary venvs to avoid polluting the host environment.
- **Hard limits**: `debate_round ≤ 3`, `execution_retries < 2` to prevent infinite loops.

## When Modifying This Project

- If you change `references/ir-schema.md`, ensure all examples remain valid.
- If you change `references/patch-schema.md`, ensure `scripts/ast_patch.py` supports all documented actions.
- If you change `scripts/ast_patch.py`, verify 1-indexed line numbers and JSON escaping rules.
- If you change `scripts/run_code.py`, ensure the `PACKAGE_MAP` covers common aliases.
- Always update `README.md` and `README.zh.md` if user-facing behavior changes.
- Keep this file updated if project structure or conventions change.
