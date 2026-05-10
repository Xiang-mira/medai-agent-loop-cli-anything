# GitHub upload manifest

This archive is intended for public GitHub upload and project demonstration. It includes only source code, lightweight mock/demo assets, tests, and sanitized documentation.

## Included directories

| Path | Included? | Role in project |
|---|---:|---|
| `agent-harness/cli_anything/medai/` | Yes | Core `medai-cli` package: CLI commands, medical tool wrappers, agent loop, mini EM loop, VLM Label Expert, RadThinking trace generation |
| `agent-harness/tests/` | Yes | Unit tests for core modules and imports |
| `scripts/` | Yes | Demo generation, PanTS helper scripts, batch-run helpers, Ollama smoke test |
| `docs/` | Yes | Architecture, validation, meeting/demo reports, material mapping, command cheat sheet |
| `assets/` | Yes | Lightweight SVG and PNG diagrams for GitHub/README visualization |
| `examples/sample_outputs/` | Yes | Sanitized JSON examples; no CT data or private paths |
| `third_party/mock_model/` | Yes | Lightweight mock inference backend for self-contained demo |
| `third_party/README.md` | Yes | Explains optional local third-party placement |

## Excluded directories/files

| Excluded | Reason |
|---|---|
| `data/` | May contain real or private CT data, labels, reports, or generated synthetic runtime data; generated locally instead |
| `outputs/` | Runtime artifacts, local absolute paths, large predictions, and possible derived medical data |
| `third_party/ShapeKit-main/` | Third-party source; must be obtained separately under its own license |
| `third_party/PanTS-main/` | Third-party dataset/repo resources; large and license/terms dependent |
| `docs/*.pdf` | Research PDFs/private materials; use links instead |
| `.git/`, `.claude/`, caches | Local metadata, assistant settings, and non-source artifacts |
| `*.nii`, `*.nii.gz`, `*.dcm`, model checkpoints | Large medical/model files; should never be committed by default |

## Mapping to project requirements

| Requirement | Where represented |
|---|---|
| CLI-wrapped AI model/tool | `medai_cli.py`, `totalseg_runner.py`, `shapekit_runner.py`, `run_medai_cli.py` |
| Agent loop | `agent_controller.py`, `agent_state.py`, `decision_policy.py`, `human_review.py` |
| ScaleMAI-inspired E-step | `label_verifier.py`, `projection_builder.py`, `vlm_label_expert.py`, `annotation_manager.py` |
| Mini EM loop | `em_loop.py`, `rounds_metrics.json` examples in docs/sample outputs |
| RadThinking-style reasoning | `radthinking.py`, `reasoning_trace.py`, `examples/sample_outputs/patient_traces_mock.json` |
| Data/benchmark integration | `pants_utils.py`, `scripts/download_pants_mini.py`, `batch_run_pants50.py`, `batch_eval_dice.py` |
| Validation | `agent-harness/tests/`, `docs/VALIDATION_REPORT.md`, `docs/VALIDATION_RUN_2026-05-10.md` |
| Public safety boundaries | `README.md`, `PACKAGE_NOTES.md`, `.gitignore`, `third_party/README.md` |

## Root-level files

| Path | Role |
|---|---|
| `README.md` | Main GitHub entry point, project workflow, figures, and self-contained demo instructions |
| `QUICKSTART_WINDOWS.md` | Windows quickstart for local setup and CLI usage |
| `run_medai_cli.py` / `run_medai_cli.bat` | Python and Windows launchers for `medai-cli` |
| `.gitignore` | Prevents committing data, outputs, model weights, PDFs, caches, and third-party repos |
| `LICENSE` | License for this repository's original code |
| `PACKAGE_NOTES.md` | Notes about scope, validation, and excluded assets |
| `UPLOAD_MANIFEST.md` | This upload/exclusion manifest |
