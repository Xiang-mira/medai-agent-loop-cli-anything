# GitHub Demo Guide

This guide separates demos into two tiers.

## Tier 1: self-contained GitHub demo

Purpose: prove that the CLI, mock model, agent state logging, RadThinking trace generation, and JSON outputs work after cloning the repository.

No external dependencies required beyond Python packages in `requirements-base.txt`.

```powershell
conda create -n medai-agent python=3.10 -y
conda activate medai-agent
pip install -r agent-harness\requirements-base.txt
pip install -e agent-harness
python run_medai_cli.py --json doctor
python scripts\create_radthinking_demo.py
python run_medai_cli.py --json agent-loop `
  --patient-folder data\radthinking_demo\patient_001 `
  --output-folder outputs\agent_loop_mock `
  --backend custom `
  --model-command "python third_party\mock_model\mock_seg_infer.py --image {image} --output {output}" `
  --postprocess none `
  --organ liver `
  --expected-organs liver `
  --max-scans 1
```

Inspect:

```text
outputs/agent_loop_mock/final_summary.json
outputs/agent_loop_mock/agent_state.json
outputs/agent_loop_mock/patient_traces.json
outputs/agent_loop_mock/review_queue.jsonl
```

Static examples are included in `examples/sample_outputs/`.

## Tier 2: local full demo

Requires local tools/data:

- ShapeKit in `third_party/ShapeKit-main/`
- optional TotalSegmentator installation
- optional Ollama + `qwen2.5vl:7b`
- optional real PanTS data

### ShapeKit

```powershell
python run_medai_cli.py --json agent-loop `
  --patient-folder data\radthinking_demo\patient_001 `
  --output-folder outputs\agent_loop_shapekit `
  --backend custom `
  --model-command "python third_party\mock_model\mock_seg_infer.py --image {image} --output {output}" `
  --postprocess shapekit `
  --shapekit-root third_party\ShapeKit-main `
  --organ liver `
  --expected-organs liver `
  --max-scans 1
```

### VLM Label Expert

```powershell
python run_medai_cli.py --json projection-build `
  --ct-image ct.nii.gz `
  --annotation-a ref\pancreas.nii.gz `
  --annotation-b pred\pancreas.nii.gz `
  --organ pancreas `
  --output-folder outputs\projections `
  --strict-alignment

python run_medai_cli.py --json vlm-label-expert `
  --ct-image ct.nii.gz `
  --annotation-a ref\pancreas.nii.gz `
  --annotation-b pred\pancreas.nii.gz `
  --organ pancreas `
  --output-folder outputs\vlm_out `
  --vlm-backend ollama `
  --vlm-model qwen2.5vl:7b `
  --strict-alignment
```

### PanTS sanity check

Real PanTS data and batch outputs are not bundled. After preparing local data, use:

```powershell
python run_medai_cli.py --json pants-import-files ...
python run_medai_cli.py --json pants-eval-case ...
python scripts\batch_run_pants50.py --limit 3
python scripts\batch_eval_dice.py ...
```

## Interpretation boundaries

- This is not a clinical diagnostic system.
- This is not a full ScaleMAI reproduction.
- M-step retraining is a stub.
- TotalSegmentator is an anatomical segmentation backend, not a PanTS tumor-specific model.
