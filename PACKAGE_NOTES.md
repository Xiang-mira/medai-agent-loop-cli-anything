# Package notes

This archive is the sanitized GitHub-ready version of the project.

## Included

- Core `medai-cli` source code.
- Unit tests.
- Documentation and validation notes.
- Lightweight mock model for self-contained smoke tests.
- Sanitized sample JSON outputs.
- Lightweight SVG architecture diagrams.

## Excluded

- Real CT data, masks, reports, private/local datasets, and derived outputs.
- Full `outputs/` and `data/` directories.
- Full ShapeKit and PanTS third-party repositories.
- Research PDF files and private reference materials.
- `.git/`, `.claude/`, caches, local logs, and environment files.

## Validation status

The project code is designed to support:

- `doctor` environment check;
- self-contained mock `agent-loop` smoke test;
- Label Verifier / Projection Builder / VLM Label Expert;
- mini EM loop dry-run;
- tests under `agent-harness/tests/`.

The public package itself does not include the large optional resources needed for real PanTS/ShapeKit/TotalSegmentator experiments. See the README and `third_party/README.md` for local setup details.


## Final package check performed

- Python syntax compile check: passed.
- Unit tests in `agent-harness/tests/`: 24 passed in the build environment after installing base requirements.
- Self-contained mock `agent-loop` smoke test: executed successfully; runtime-generated `data/` and `outputs/` were removed before packaging.
- Exclusion scan: no `.git/`, `.claude/`, `data/`, `outputs/`, `__pycache__/`, PDFs, NIfTI/DICOM files, model checkpoints, or third-party ShapeKit/PanTS source directories are included.
