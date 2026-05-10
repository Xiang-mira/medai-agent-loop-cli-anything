# third_party dependencies

Only the lightweight `mock_model/` directory is included in this public repository. It is used for the self-contained smoke test and does not contain real medical data or trained clinical weights.

The following third-party resources are **not bundled** and should be placed here only in your local environment when needed:

```text
third_party/
├── mock_model/          # included: synthetic/mock inference scripts
├── ShapeKit-main/       # not included: optional local ShapeKit clone/extract
├── PanTS-main/          # not included: optional local PanTS repo clone/extract
└── CLI-Anything-reference/ # not required; design reference only
```

## Why these are not included

- **ShapeKit** has its own source code and license. This repository only provides a wrapper (`shapekit_runner.py`) that can call a local copy through `--shapekit-root`.
- **PanTS/PanTSMini** data and repository resources may be large and may have dataset-specific terms. Real CT data, masks, reports, and derived outputs must not be committed here.
- **TotalSegmentator** and VLM models should be installed separately through their official channels.

## Local placement example

```text
third_party/
├── mock_model/
├── ShapeKit-main/
└── PanTS-main/
```

Then run commands such as:

```powershell
python run_medai_cli.py --json postprocess `
  --input-folder outputs\raw `
  --output-folder outputs\refined `
  --shapekit-root third_party\ShapeKit-main
```
