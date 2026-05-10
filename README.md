# medai-agent-loop-cli-anything

> **A runnable CLI-based medical AI workflow prototype with tool calling, verification, and structured reasoning.**

`medai-agent-loop-cli-anything` provides a unified `medai-cli` interface for running medical AI tools from the command line. It wraps model inference, segmentation post-processing, annotation verification, VLM-assisted review, versioned annotation management, and RadThinking-style trace generation into reproducible commands with structured JSON outputs.

This project focuses on the core engineering layer needed for a medical agent workflow: making models and utilities callable, making intermediate results auditable, and organizing multiple tools into a controlled loop of observation, inference, quality checking, verification, review, and state saving.

---

## Table of Contents

- [Project Goal](#project-goal)
- [Core Contributions](#core-contributions)
- [System Architecture](#system-architecture)
- [Design Lineage](#design-lineage)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Self-contained Demo](#self-contained-demo)
- [Main CLI Commands](#main-cli-commands)
- [Implementation Details](#implementation-details)
- [Output Artifacts](#output-artifacts)
- [Validation Status](#validation-status)
- [What Is Not Included](#what-is-not-included)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Summary](#summary)

---

## Project Goal

Medical AI workflows often rely on separate scripts, model checkpoints, post-processing tools, manual inspection steps, and evaluation utilities. These components are difficult to reuse in an agentic workflow unless they expose stable interfaces and structured outputs.

This project addresses that engineering gap by building a CLI-centered workflow prototype:

```text
medical model / utility
→ CLI-callable tool
→ JSON-readable output
→ deterministic workflow controller
→ review / refinement / trace artifacts
```

The current system is built around three design principles:

1. **Reproducible interfaces**  
   Every major operation is exposed through `medai-cli` and can be invoked with explicit command-line arguments.

2. **Structured outputs**  
   Commands return JSON-compatible results and save auditable artifacts such as `agent_state.json`, `final_summary.json`, `patient_traces.json`, and `review_queue.jsonl`.

3. **Controlled workflow composition**  
   Medical tools are connected through a deterministic workflow controller rather than an unconstrained autonomous planner.

---

## Core Contributions

The repository currently implements the following components:

| Component | Status | Role |
|---|---:|---|
| `medai-cli` command interface | Implemented | Unified CLI entry point for medical AI tools |
| TotalSegmentator / custom backend wrapper | Implemented | AI segmentation or model execution backend |
| ShapeKit wrapper | Implemented | Optional anatomy-aware post-processing interface |
| Label Verifier | Implemented | DSC-based annotation-vs-prediction routing |
| Projection Builder | Implemented | Mask-centered 2D overlay generation for VLM/human review |
| VLM Label Expert | Implemented as optional module | Pairwise candidate annotation comparison through Ollama/VLM or stub |
| AnnotationManager | Implemented | Versioned raw / prediction / updated annotation storage |
| Mini EM loop | Implemented as prototype | Executable E-step, stubbed M-step and data-annealing plan |
| RadThinking-style trace | Implemented as rule-based prototype | Structured observation, temporal comparison, clinical context, conclusion fields |
| Deterministic workflow controller | Implemented | Observe → infer → QC → verify → review/update → trace → save state |

A concise summary:

```text
Current implementation:
CLI wrapper layer + medical tool commands + deterministic workflow prototype

Not included:
clinical diagnosis, full autonomous planning, full model retraining, full ScaleMAI reproduction
```

---

## System Architecture

The architecture is presented at three levels. Each figure answers a different design question.

### 1. Conceptual Relationship: Model, CLI, Tool, Agent, and Agent Loop

![Relationship among Model, CLI, Tool, Agent, and Agent Loop](assets/concept_map_model_cli_tool_agent_loop.png)

This view defines the project’s conceptual vocabulary.

| Concept | Meaning in this repository |
|---|---|
| **Model** | Backend capability such as TotalSegmentator, a custom model, a mock backend, or a VLM. |
| **Tool** | A callable operation such as `infer`, `postprocess`, `label-verify`, `projection-build`, `vlm-label-expert`, `em-loop`, or `trace-build`. |
| **CLI** | The reproducible interface that exposes tools as commands. |
| **Agent Controller** | The orchestration layer that sequences tool calls and routes intermediate results. |
| **Agent Loop** | The repeated workflow of observe → decide/route → act → evaluate → save state. |

The key distinction is:

```text
Model = backend capability
Tool = callable action
CLI = reproducible interface
Agent Controller = workflow orchestrator
Agent Loop = stateful control process
```

---

### 2. CLI Wrapper Layer for Medical AI Tools

![CLI Wrapper Layer for Medical AI Tools](assets/cli_based_ai_model_wrapper.png)

This view shows the engineering layer that makes medical AI components callable and reusable.

```text
command invocation
→ argument parsing
→ input loading
→ validation and data preparation
→ tool / model execution
→ output formatting
→ saved results and logs
```

| Wrapper stage | Implementation |
|---|---|
| Command invocation | `python run_medai_cli.py --json <command> ...` |
| Argument parsing | `click`-based CLI definitions in `medai_cli.py` |
| Input loading | CT images, masks, reports, patient folders, JSON metadata |
| Validation / preparation | path checks, folder normalization, organ lists, projection building |
| Tool / model execution | TotalSegmentator, ShapeKit wrapper, VLM Label Expert, custom backend, mock model |
| Output formatting | JSON serialization, summary generation, trace construction, state logging |
| Saved artifacts | `final_summary.json`, `agent_state.json`, `patient_traces.json`, `review_queue.jsonl`, projection PNGs |

The wrapper layer makes tools:

```text
terminal-runnable
JSON-readable
loggable
reproducible
agent-callable
```

---

### 3. Medical Agent Loop Prototype

![Medical Agent Loop Prototype](assets/medical_agent_loop_prototype.png)

This view shows how the wrapper layer is composed into a medical workflow.

```text
Medical inputs
→ observe / prepare
→ infer
→ QC and verification
→ review / refinement
→ reasoning trace
→ save state and outputs
```

The implemented deterministic loop is:

```text
Observe → Infer → QC → Verify → Review / Update → Trace → Save State
```

| Workflow stage | Implementation | Output |
|---|---|---|
| Medical inputs | CT image, masks, reports, clinical JSON, patient folder | input layout |
| Observe / prepare | input checks, folder scan, adapter, projection builder | normalized inputs / metadata |
| Infer | TotalSegmentator, custom backend, or mock model | segmentation masks / model outputs |
| QC and verification | QC checker + Label Verifier | organ presence, metrics, DSC routing |
| Review / refinement | VLM Label Expert, human review queue, AnnotationManager, mini EM loop | decisions, updated candidates, review items |
| Reasoning trace | RadThinking-style trace builder | `patient_traces.json` |
| Save state | auditable execution logging | `agent_state.json`, `final_summary.json` |

The workflow is intentionally deterministic and auditable. Optional VLM review is used as a bounded comparison module, not as a free-form clinical decision maker.

---

## Design Lineage

The project combines ideas from several research and engineering systems. External projects, papers, datasets, and third-party source code are **not redistributed** in this repository.

| Source / idea | Key concept | Project implementation |
|---|---|---|
| CLI-Anything-style design | Expose software functions as agent-callable CLI commands | `medai-cli`, `--json`, `SKILL.md`, stable tool commands |
| ScaleMAI-style refinement | Iterative verification and annotation refinement | Label Verifier, VLM Label Expert, AnnotationManager, mini EM loop |
| ShapeKit-style post-processing | Anatomy-aware segmentation post-processing | optional `postprocess` wrapper |
| PanTS-style setting | Pancreatic CT segmentation / evaluation context | PanTS import/eval helpers and batch scripts |
| RadThinking-style reasoning | Structured longitudinal reasoning trace | observation, temporal comparison, clinical context, diagnostic conclusion fields |

---

## Repository Structure

```text
medai-agent-loop-cli-anything/
├── README.md
├── QUICKSTART_WINDOWS.md
├── run_medai_cli.py
├── run_medai_cli.bat
├── assets/
├── agent-harness/
│   ├── setup.py
│   ├── requirements*.txt
│   ├── cli_anything/
│   │   └── medai/
│   │       ├── medai_cli.py
│   │       ├── skills/SKILL.md
│   │       └── core/
│   │           ├── agent_controller.py
│   │           ├── agent_state.py
│   │           ├── totalseg_runner.py
│   │           ├── shapekit_runner.py
│   │           ├── adapter.py
│   │           ├── label_verifier.py
│   │           ├── projection_builder.py
│   │           ├── vlm_label_expert.py
│   │           ├── annotation_manager.py
│   │           ├── em_loop.py
│   │           ├── radthinking.py
│   │           ├── qc_checker.py
│   │           ├── human_review.py
│   │           └── pants_utils.py
│   └── tests/
├── docs/
├── scripts/
├── examples/
└── third_party/
    └── mock_model/
```

---

## Installation

### Minimal installation

The minimal setup is sufficient for the self-contained demo. It does not require PanTS, ShapeKit, TotalSegmentator, Ollama, GPU, or private medical data.

```powershell
conda create -n medai-agent python=3.10 -y
conda activate medai-agent
cd medai-agent-loop-cli-anything
pip install -r agent-harness\requirements.txt
pip install -e agent-harness
python run_medai_cli.py --json doctor
```

### Optional TotalSegmentator support

```powershell
pip install -r agent-harness\requirements-totalseg.txt
```

### Development tests

```powershell
pip install -r agent-harness\requirements-dev.txt
cd agent-harness
python -m pytest tests/ -v
```

Validation notes are documented in:

- `docs/VALIDATION_REPORT.md`
- `docs/VALIDATION_RUN_2026-05-10.md`

---

## Self-contained Demo

The repository includes a synthetic demo with a mock model backend.

### Step 1 — Generate synthetic patient data

```powershell
python scripts\create_radthinking_demo.py
```

### Step 2 — Check the patient layout

```powershell
python run_medai_cli.py --json radthinking-check `
  --patient-folder data\radthinking_demo\patient_001
```

### Step 3 — Run the workflow prototype

```powershell
python run_medai_cli.py --json agent-loop `
  --patient-folder data\radthinking_demo\patient_001 `
  --output-folder outputs\agent_loop_mock_self_contained `
  --backend custom `
  --model-command "python third_party\mock_model\mock_seg_infer.py --image {image} --output {output}" `
  --postprocess none `
  --organ liver `
  --expected-organs liver
```

### Step 4 — Inspect outputs

```text
outputs/agent_loop_mock_self_contained/
├── agent_state.json
├── final_summary.json
├── patient_traces.json
├── review_queue.jsonl
└── scan_outputs/
```

This demo verifies that the CLI runs, the backend is called, outputs are generated, and workflow state is saved.

---

## Main CLI Commands

| Command | Purpose |
|---|---|
| `doctor` | Check runtime environment and backend availability |
| `infer` | Run AI segmentation backend or custom model command |
| `postprocess` | Run ShapeKit post-processing if available locally |
| `run` | One-shot inference + optional post-processing |
| `label-verify` | Compare annotation and prediction using DSC |
| `projection-build` | Generate mask-centered 2D projection PNGs |
| `vlm-label-expert` | Ask a VLM to compare candidate annotations |
| `em-loop` | Run the mini EM annotation-refinement workflow |
| `agent-loop` | Run the patient-level workflow prototype |
| `trace-build` | Build one RadThinking-style trace |
| `pants-import-*` | Import PanTS-like cases into project layout |
| `pants-eval-case` | Compute Dice sanity checks for selected organs |

Typical command form:

```powershell
python run_medai_cli.py --json <command> ...
```

---

## Implementation Details

### Label Verifier

The Label Verifier compares a current annotation with a model prediction using Dice/DSC and routes cases conservatively.

| Condition | Decision |
|---|---|
| prediction missing | `review_queue` |
| current annotation missing | `auto_replace_candidate` |
| current annotation empty + prediction non-empty | `auto_replace_candidate` |
| both masks non-empty but DSC ≈ 0 | `send_to_vlm_label_expert` |
| `0 < DSC < threshold` | `send_to_vlm_label_expert` |
| DSC ≥ threshold | `accept` |

The system avoids the unsafe shortcut:

```text
DSC = 0 → always replace
```

### VLM Label Expert

The VLM Label Expert is optional and bounded.

```text
CT image + annotation A + annotation B
→ build mask-centered 2D overlays
→ send projections to VLM
→ parse JSON decision
→ update decision log or route to review queue
```

Example output:

```json
{
  "winner": "A",
  "confidence": 0.80,
  "reason": "Candidate A is more anatomically plausible.",
  "num_projection_images_sent": 2
}
```

If projection alignment fails or the VLM response cannot be parsed safely, the system routes the case to review rather than forcing a decision.

### Mini EM Annotation-Refinement Loop

The mini EM loop is inspired by iterative annotation-refinement workflows.

```text
Round N
→ inference
→ optional post-processing
→ E-step: verifier + optional VLM review
→ annotation update
→ M-step: retraining stub / data-annealing plan
→ metrics saved
```

Current implementation:

- executable inference / verification / annotation-update path;
- optional ShapeKit post-processing;
- optional VLM routing;
- per-round metrics;
- stubbed M-step for future training backend integration.

### RadThinking-style Trace

The trace generator produces structured case-level summaries:

| Field | Meaning |
|---|---|
| `observation` | CT/mask-derived observation fields |
| `temporal_comparison` | comparison with prior scan when available |
| `clinical_context` | parsed report / clinical JSON information |
| `diagnostic_conclusion` | structured field derived from provided pathology/follow-up JSON when available |

The trace generator does not fabricate clinical diagnosis.

---

## Output Artifacts

| Output | Meaning |
|---|---|
| `final_summary.json` | final run-level summary |
| `agent_state.json` | auditable event trajectory |
| `patient_traces.json` | RadThinking-style structured traces |
| `review_queue.jsonl` | uncertain cases requiring VLM or human review |
| `annotation_versions/` | versioned raw / prediction / updated annotations and decisions |
| `rounds_metrics.json` | mini EM loop per-round metrics |
| projection PNGs | visual annotation-comparison artifacts |

Static sample outputs are provided in:

```text
examples/sample_outputs/
```

---

## Validation Status

The repository includes unit and smoke-test coverage for key modules:

- Label Verifier routing;
- AnnotationManager versioning;
- VLM response parsing;
- projection builder;
- RadThinking negation-aware parsing;
- QC checks;
- EM loop dry-run;
- package import checks.

Recorded validation artifacts are available in:

- `docs/VALIDATION_REPORT.md`
- `docs/VALIDATION_RUN_2026-05-10.md`

---

## What Is Not Included

The upload intentionally excludes:

```text
real CT data
real PanTS data
runtime outputs
ShapeKit source code
PanTS source repository
private or unpublished research materials
paper PDFs
model weights
API keys / tokens / secrets
```

Reasons:

- avoid uploading medical or derived data;
- avoid third-party copyright/license risks;
- avoid redistributing private or unpublished materials;
- keep the repository lightweight and reproducible.

Additional notes:

- `UPLOAD_MANIFEST.md`
- `PACKAGE_NOTES.md`
- `third_party/README.md`

---

## Limitations

| Topic | Current status |
|---|---|
| Full ScaleMAI reproduction | Not included; only a mini EM-inspired prototype |
| Real training backend / continual tuning | Not included; M-step is a stub |
| Fully autonomous LLM planner | Not included by default |
| Clinical diagnosis | Not performed |
| Real PanTS tumor-specific model | Not bundled; can be plugged in through a custom backend |
| ShapeKit source | Not bundled; local installation required |
| Optional VLM | Supported when a local Ollama model is available |

---

## Roadmap

Planned extensions include:

1. plug in a task-specific or lab-provided segmentation model through `--backend custom`;
2. add a real training backend for the M-step;
3. connect human review/editing to annotation refinement;
4. expand VLM Label Expert evaluation and projection modes;
5. improve report-to-structure extraction for richer clinical context;
6. optionally add a constrained LLM planner with a strict tool registry and JSON action schema.

---

## Summary

`medai-agent-loop-cli-anything` demonstrates a first-stage engineering prototype for medical AI tool orchestration:

```text
CLI wrapper layer
+ medical tool commands
+ deterministic workflow controller
+ verification and review routing
+ mini EM-inspired annotation refinement
+ RadThinking-style structured traces
+ auditable JSON outputs
```

The repository is structured for reproducible demonstration, code review, and future extension into larger medical AI agent systems.
