---
name: paper2code
description: >
  Convert research papers, technical documents, or plain-text descriptions into runnable
  PyTorch or TensorFlow code via structured IR, multi-agent debate, and AST-level patching.
  Use when the user provides a paper (PDF, Markdown, HTML, or pasted text), a technical
  spec, a design document, or even a high-level idea and wants it implemented as code.
  Trigger phrases: "paper to code", "implement this paper", "reproduce this paper",
  "build this model", "code this up", "复现论文", "论文转代码", "把论文实现成代码",
  "帮我写这个模型的代码", "根据这个文档生成代码".
---

# Paper-to-Code: Convert Documents & Ideas to Runnable Code

Convert any source material — a research paper PDF, a Markdown technical doc, a pasted text description, a design spec, or even a rough idea — into a complete, runnable code repository through a structured pipeline: source ingestion → IR construction → modular code generation → adversarial debate → AST patching → execution verification.

## Setup

Create a working directory for this conversion:
```
WORKDIR = ./paper2code_output/
```

All intermediate and final files go here. Create it if it does not exist:
```
mkdir WORKDIR
mkdir WORKDIR/src
```

If `mkdir` fails (e.g., on Windows PowerShell), use the equivalent `New-Item` command:
```
New-Item -ItemType Directory -Path WORKDIR -Force
New-Item -ItemType Directory -Path WORKDIR/src -Force
```

Install dependencies if missing:
```
pip install PyMuPDF
```

The bundled helper scripts are located in the `scripts/` folder relative to this skill directory:
- `scripts/extract_paper.py` (optional, for PDF input)
- `scripts/ast_patch.py`
- `scripts/run_code.py`

If any script is missing, create it before proceeding (see `scripts/` for reference implementations).

---

## Phase 1: Ingest Source Material

This phase converts the user's input into a single normalized text file `WORKDIR/source.md`. The input can be any of the following:

### Supported Input Types

| Input Type | How to Handle |
|------------|---------------|
| **PDF** | Run `python scripts/extract_paper.py <paper.pdf> --output WORKDIR/source.md` |
| **Markdown / HTML / plain text file** | Read the file directly, copy its contents into `WORKDIR/source.md` |
| **Pasted text** (user provided the description in chat) | Write the text directly into `WORKDIR/source.md` |
| **Multiple files** | Concatenate them in logical order (e.g., spec → diagrams → appendix) into `WORKDIR/source.md` |
| **URL / web page** | Fetch the page content, extract the main article text, write to `WORKDIR/source.md` |

**If the source material is vague or incomplete** (e.g., only a rough idea with no architecture details):
- Proceed anyway — the IR construction phase will ask the user for clarification on missing fields.
- Do not block the pipeline; use placeholders like `"TBD — ask user"` in the IR and confirm during Phase 2.

**If PDF extraction fails** (missing dependencies, unreadable PDF, etc.):
- Ask the user to provide the text directly (paste, upload a `.txt`/`.md`, or give a URL).
- Do not stop the pipeline permanently.

Once `WORKDIR/source.md` exists, Read it and identify:
- Title, abstract, key contributions (if present)
- Method section: architecture, equations, algorithms
- Experimental setup: datasets, hyperparameters, evaluation metrics
- Any figures/tables describing model structure
- **If any of the above are missing**, note them as gaps to fill during Phase 2.

---

## Phase 2: Build Structured IR

Read `references/ir-schema.md` for the complete schema definition.

Based on `WORKDIR/source.md`, produce a structured IR JSON object capturing:
- Task type (classification, generation, detection, etc.)
- Framework: `pytorch` or `tensorflow` — ask user if unclear
- Model architecture (layers, dimensions, connections)
- Data pipeline (dataset, preprocessing, augmentation)
- Training config (optimizer, lr, schedule, epochs)
- Evaluation metrics
- File plan (mapping of modules to files, under the `files` field)

**If the source material is vague or incomplete:**
- Fill in the fields you can infer from the text.
- For any missing critical fields (e.g., input dimensions, number of classes, loss function), add `"TBD"` and ask the user during the confirmation step.
- Do not guess hyperparameters; if they are not in the source, either leave them as `"TBD"` or use sensible defaults and document them.

Write the IR to `WORKDIR/ir.json`.

Show the IR summary to the user and ask for confirmation before proceeding.
**This step is critical — all subsequent phases depend on IR accuracy.**

**If the user rejects the IR or asks for changes:**
- Update `ir.json` accordingly
- Re-show the summary and ask again
- Do not proceed until the user confirms

---

## Phase 3: Plan Code Modules

Based on `ir.json`, plan the output file structure.

Write `WORKDIR/plan.md` with the following sections:

```markdown
# Module Plan

## File List
| File | Contents | Dependencies |
|------|----------|-------------|
| utils.py | helper functions | none |
| model.py | model classes | utils.py |
| dataset.py | dataset and dataloader | utils.py |
| train.py | training loop | model.py, dataset.py, utils.py |
| evaluate.py | evaluation loop | model.py, dataset.py, utils.py |

## Generation Order
1. utils.py (no deps)
2. model.py (depends on utils)
3. dataset.py (depends on utils)
4. train.py (depends on model, dataset, utils)
5. evaluate.py (depends on model, dataset, utils)

## External Dependencies
- torch, torchvision, etc.
```

1. Determine file list from IR's `files` field
2. Determine generation order by dependency graph (utils → model → data → train → eval)
3. Identify external dependencies (torch, torchvision, transformers, etc.)
4. Write the above plan to `WORKDIR/plan.md`

---

## Phase 4: Generate & Critique (Debate Loop)

This is the core quality mechanism. Use the `task` tool to launch isolated subagents for generator and critic roles. Separation ensures the critic reviews code without bias from the generator's reasoning.

**Debate Loop State:**
- `debate_round`: 1, 2, or 3 (max 3)
- `execution_retries`: 0, 1, or 2 (max 3 total attempts including first run)

Track both variables explicitly.

### Generate

Before launching the generator, Read the contents of:
- `WORKDIR/ir.json`
- `WORKDIR/plan.md`
- `references/code-patterns.md`

Launch a task subagent (`subagent_type: "general"`) with prompt:

```
You are a code generator. Generate complete, runnable {framework} code.

IR: {paste the full contents of WORKDIR/ir.json here}
Plan: {paste the full contents of WORKDIR/plan.md here}
Round: {debate_round}
Previous feedback: {paste critic feedback from last round, or "None (first round)"}

Read the file `references/code-patterns.md` (relative to the skill directory) for framework patterns to follow.

For each file in the plan, write complete code to `WORKDIR/src/<filename>`.
Ensure:
- All tensor shapes are consistent across layers
- All imports are present
- Training loop includes: zero_grad, backward, step, logging
- Device handling (CPU/GPU) is correct
- Do not overwrite files that are not mentioned in this round's feedback unless they are broken.
```

### Critique

After generator completes, Read all generated files from `WORKDIR/src/`.

Launch a SEPARATE task subagent (`subagent_type: "general"`) with prompt:

```
You are a strict code critic. Review the generated code against the IR specification.

IR: {paste the full contents of WORKDIR/ir.json here}
Code files: {paste the full contents of all files in WORKDIR/src/ here}

Check each item:
- Tensor shapes consistent across all layers?
- All imports present and correct?
- Forward pass logic matches the source material's architecture?
- Loss function matches IR specification?
- Training loop correct (zero_grad → backward → step)?
- Data loading and preprocessing correct?
- Device handling (CPU/GPU) present?
- Evaluation metrics implemented correctly?

Return a JSON object (and nothing else) in this exact format:
{
  "approved": true,
  "issues": []
}

or

{
  "approved": false,
  "issues": [
    {"file": "model.py", "severity": "critical|warning", "line": 42, "problem": "description", "fix": "suggested fix"}
  ]
}
```

### Parse Critic Response

Parse the critic's response:
1. **If the response is wrapped in Markdown code blocks** (e.g., ```json ... ```), extract the JSON from inside the fences.
2. **If the response contains extra text**, attempt to find the first valid JSON object using a regex or by searching for `{` and matching braces.
3. **If parsing fails entirely**, treat the round as `approved: false` with a single issue: `{"file": "unknown", "severity": "critical", "line": 0, "problem": "Critic response was not valid JSON", "fix": "Re-run critique"}`.

### Decide

- If `approved: true` → exit debate loop, proceed to Phase 6
- If `approved: false` and `debate_round < 3` → proceed to Phase 5 (AST Patch)
- If `approved: false` and `debate_round == 3` → proceed to Phase 6 with a **warning** in the final report: "Code has unresolved critical issues; smoke test may fail."

---

## Phase 5: Apply AST Patches

Convert critic issues into structured patches. Read `references/patch-schema.md` for the full patch format specification.

Write patches to `WORKDIR/patches.json`:

```json
[
  {"file": "model.py", "action": "add_import", "code": "import torch.nn.functional as F"},
  {"file": "model.py", "action": "insert_after", "line": 42, "code": "x = x.view(x.size(0), -1)"},
  {"file": "model.py", "action": "replace_function", "function": "forward", "code": "def forward(self, x):\n    ..."}
]
```

Rules:
- `line` is **1-indexed** (first line of the file is line 1).
- When multiple patches target the same file, list them in **reverse line order** (highest line first) to avoid line-number drift after insertions.
- Every patch must be valid JSON; newlines in `code` must be escaped as `\n`.

Run the patching script:
```
python scripts/ast_patch.py --code-dir WORKDIR/src/ --patches WORKDIR/patches.json
```

**If the patch script fails** (file not found, line out of range, invalid JSON):
- Log the error
- Do not increment `debate_round` for a patch failure
- Attempt to fix the patch JSON manually (correct line numbers, valid JSON syntax)
- Re-run the patch script
- If it still fails after 2 attempts, report to the user and stop

If patch succeeds and `debate_round < 3`, increment `debate_round` and return to Phase 4 for another critique round.
If patch succeeds and `debate_round == 3`, return to Phase 4 without incrementing `debate_round` (this is the final round).

---

## Phase 6: Execute & Reflect

### Run Smoke Test

Execute the bundled runner:
```
python scripts/run_code.py --code-dir WORKDIR/src/ --timeout 120
```

The script will:
1. Scan imports to determine dependencies
2. Create a temporary venv and install packages
3. Run a smoke test (1 batch or 1 epoch)
4. Capture stdout, stderr, and any traceback
5. Output a structured JSON result to stdout

### Parse Smoke Test Result

The expected JSON output is:
```json
{
  "status": "success" | "failure",
  "exit_code": 0,
  "stdout": "...",
  "stderr": "...",
  "error": "RuntimeError: ..." | null
}
```

Parse the JSON using the same rules as Phase 4 (extract from Markdown if needed).

**If the runner script itself crashes** (e.g., Python traceback from the script, not the generated code):
- Report the script error to the user
- Stop here; the generated code is in `WORKDIR/src/` for manual execution

### Evaluate Result

**If SUCCESS (`status: "success"`):**
- Report success to user
- List all generated files in `WORKDIR/src/`
- Provide instructions for full training

**If FAILURE (`status: "failure"`) and `execution_retries < 2`:**
- Increment `execution_retries`
- Analyze the error output
- Produce a reflection JSON:
  ```json
  {"error_type": "RuntimeError", "root_cause": "shape mismatch in linear layer", "fix_strategy": "add flatten before linear", "confidence": 0.85}
  ```
- Convert `fix_strategy` into AST patches (write to `WORKDIR/patches.json`)
- Return to Phase 5 (apply patches), then Phase 4 (generator with reflection as additional context)

  **Note:** Re-entering Phase 4 with execution feedback does NOT reset `debate_round`. The generator gets one more chance within the remaining rounds. If `debate_round` is already 3, the generator still runs but the critic will perform the final round; if issues remain, proceed with the warning as per Phase 4 rules.

**If FAILURE and `execution_retries >= 2` (exhausted):**
- Report the error to user with the full analysis
- Suggest manual fixes based on the last reflection
- Leave the code in `WORKDIR/src/` for user to complete
- Do not retry again

---

## Output Structure

Final output in `WORKDIR/`:
- `source.md` — normalized input text (extracted from PDF, copied from file, or written from chat)
- `ir.json` — structured intermediate representation
- `plan.md` — module plan
- `patches.json` — AST patches applied (if any)
- `src/` — directory with all generated code files

If the pipeline stops early due to an error, the files produced up to that point are still available in `WORKDIR/`.

---

## Design Notes

- The IR is a compiler-style intermediate representation — all phases work from IR, not raw source text. This reduces hallucination.
- Generator and critic are isolated subagents with separate contexts, ensuring genuine adversarial review.
- AST patching preserves reviewed code. Only problematic sections are modified.
- The debate loop converges quickly — most inputs resolve in 1–2 rounds.
- Hard limits (`debate_round ≤ 3`, `execution_retries < 2`) prevent infinite loops while still allowing iterative refinement.
- The pipeline accepts any input fidelity — from a full PDF to a one-paragraph idea — and fills gaps through user interaction during Phase 2.

---

## Error Recovery Quick Reference

| Phase | Failure | Action |
|-------|---------|--------|
| 1 | Source ingestion fails (PDF unreadable, URL unreachable, etc.) | Ask user for alternative input (paste text, upload `.md`/`.txt`, or provide another URL) |
| 2 | Source material is too vague to build IR | Ask user for missing details (architecture, dimensions, hyperparameters, etc.) |
| 2 | User rejects IR | Revise IR and re-confirm |
| 4 | Critic returns invalid JSON | Attempt extraction; if impossible, treat as `approved: false` with meta-issue |
| 5 | Patch script fails | Fix patch JSON manually; retry up to 2 times; then stop |
| 6 | Smoke test fails | Reflect → patch → regenerate (if retries remain); else report and stop |
| 6 | Runner script crashes | Report script bug; leave code for manual run |

(End of file)
