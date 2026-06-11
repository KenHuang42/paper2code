# Paper2Code

Convert research papers, technical documents, or plain-text descriptions into runnable PyTorch or TensorFlow code through a structured, verifiable pipeline.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

Paper2Code is a multi-agent pipeline that transforms any source material — PDF papers, Markdown specs, web pages, or even a rough idea — into a complete, runnable deep learning codebase.

The pipeline is built around a compiler-style **Intermediate Representation (IR)** and an **adversarial debate loop** between a code generator and a critic agent. This ensures architectural accuracy, tensor shape consistency, and execution correctness.

### Core Pipeline

```
Source Material
      ↓
[Phase 1] Ingestion → source.md
      ↓
[Phase 2] IR Construction → ir.json (structured spec)
      ↓
[Phase 3] Module Planning → plan.md (dependency graph)
      ↓
[Phase 4] Generate & Critique (Debate Loop)
      │   Generator writes code → Critic reviews → Iterate
      ↓
[Phase 5] AST Patching → patches.json (targeted fixes)
      ↓
[Phase 6] Execution & Verify → Smoke test in sandbox
      ↓
Runnable Code in src/
```

---

## Features

- **Universal Input**: Accepts PDFs, Markdown, HTML, plain text, URLs, or chat descriptions.
- **Structured IR**: A compiler-style intermediate representation eliminates hallucination by decoupling understanding from generation.
- **Adversarial Debate**: Isolated generator and critic subagents review code for correctness before it ever runs.
- **AST-Level Patching**: Targeted, minimal code fixes preserve reviewed code while fixing only problematic sections.
- **Sandbox Execution**: Automatic dependency detection, temporary venv creation, and smoke testing with structured error reporting.
- **Hard Limits**: Debate rounds ≤ 3, execution retries ≤ 2 — prevents infinite loops while allowing iterative refinement.

---

## Project Structure

```
.
├── SKILL.md                     # Skill definition & full workflow specification
├── LICENSE                      # MIT License
├── README.md                    # This file
├── README.zh.md                 # 中文文档
├── requirements.txt             # Python dependencies
├── references/
│   ├── ir-schema.md             # IR JSON schema definition
│   ├── patch-schema.md          # AST patch JSON format
│   └── code-patterns.md         # PyTorch & TensorFlow idiomatic patterns
└── scripts/
    ├── extract_paper.py         # PDF text extraction (PyMuPDF)
    ├── ast_patch.py             # Apply structured AST-level patches
    └── run_code.py              # Sandbox execution with auto dependency install
```

---

## Quick Start

### Installation

```bash
pip install PyMuPDF
```

Or install all dependencies at once:

```bash
pip install -r requirements.txt
```

### Use as an OpenCode Skill

Copy this repository into your OpenCode skills directory (e.g., `~/.agents/skills/paper2code/`). OpenCode will automatically load the `SKILL.md` definition.

Trigger phrases include:
- "paper to code"
- "implement this paper"
- "reproduce this paper"
- "复现论文"
- "论文转代码"
- "build this model"

### Use Scripts Standalone

```bash
# Extract a PDF to structured markdown
python scripts/extract_paper.py paper.pdf --output source.md

# Apply AST patches to generated code
python scripts/ast_patch.py --code-dir ./src --patches patches.json

# Run smoke test in a sandboxed environment
python scripts/run_code.py --code-dir ./src --timeout 120
```

---

## How It Works

### Phase 1: Ingest Source Material

Any input — PDF, Markdown, pasted text, URL, or multiple files — is normalized into a single `source.md`.

### Phase 2: Build Structured IR

From `source.md`, the pipeline extracts a structured JSON (`ir.json`) capturing:
- Task type (classification, generation, detection, etc.)
- Framework (PyTorch or TensorFlow)
- Model architecture (layers, dimensions, connections)
- Data pipeline (dataset, preprocessing, augmentation)
- Training configuration (optimizer, learning rate, epochs)
- Evaluation metrics
- File plan (module-to-file mapping)

If the source material is vague, the pipeline fills in what it can and asks the user for missing critical fields (e.g., input dimensions, loss function).

### Phase 3: Plan Code Modules

A dependency graph is built from the IR's `files` field. The generation order follows:

```
utils → model → data → train → eval
```

### Phase 4: Generate & Critique (Debate Loop)

Isolated subagents are launched for the generator and critic roles:

1. **Generator** writes complete code to `src/` based on IR and plan.
2. **Critic** reviews the code against the IR spec, checking tensor shapes, imports, forward pass logic, loss function, training loop correctness, device handling, and evaluation metrics.
3. If the critic rejects the code, issues are passed back to the generator for revision.

This loop runs up to 3 rounds. The separation of contexts ensures genuine adversarial review.

### Phase 5: Apply AST Patches

Critic issues are converted into structured JSON patches (`patches.json`) and applied via `scripts/ast_patch.py`. Supported actions:

- `add_import` — insert import statements
- `insert_after` / `insert_before` — line-level insertion
- `replace_line` — single line replacement
- `replace_function` — AST-level function replacement (immune to line drift)
- `delete_lines` — remove line ranges

### Phase 6: Execute & Verify

`scripts/run_code.py` performs a smoke test:
1. Scans imports to detect dependencies
2. Creates a temporary virtual environment
3. Installs required packages automatically
4. Runs a smoke test (1 batch or 1 epoch)
5. Captures stdout, stderr, and traceback
6. Outputs structured JSON results

If execution fails, the pipeline reflects on the error, generates patches, and retries (up to 2 times).

---

## Intermediate Representation (IR)

The IR is the central artifact of the pipeline. See [`references/ir-schema.md`](references/ir-schema.md) for the full schema and examples (Transformer, ResNet).

Key fields:
- `components.model` — architecture, submodules, loss, input/output shapes
- `components.data` — dataset, preprocessing, dataloader config
- `components.training` — optimizer, learning rate schedule, epochs
- `components.evaluation` — metrics, test loop
- `files` — module-to-file mapping
- `dependencies` — required pip packages

---

## Code Patterns

See [`references/code-patterns.md`](references/code-patterns.md) for idiomatic PyTorch and TensorFlow patterns used during generation, including:

- Model definition (nn.Module / keras.Model)
- Training and evaluation loops
- Dataset & DataLoader / tf.data
- Multi-head attention and Transformer blocks
- Positional encoding
- Learning rate schedulers
- Mixed precision training
- Device handling

---

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

For major changes, please open an issue first to discuss what you would like to change.

---

## Citation

If you use this project in your research or work, please consider citing it:

```bibtex
@software{paper2code,
  title = {Paper2Code: Convert Documents and Ideas to Runnable Deep Learning Code},
  year = {2026},
  url = {https://github.com/KenHuang42/paper2code},
  license = {MIT}
}
```

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgments

- Inspired by compiler design principles: structured IR, AST transformation, and iterative refinement.
- Built for the OpenCode agent ecosystem, but designed as a universal skill usable by any AI agent or human developer.
