from __future__ import annotations

import json
from pathlib import Path
import click

from .core.adapter import normalize_totalseg_to_shapekit
from .core.agent_controller import run_agent_loop
from .core.data_checker import check_case_folder, check_ct_image, check_environment
from .core.json_utils import to_jsonable
from .core.em_loop import run_em_loop
from .core.label_verifier import verify_case
from .core.paths import resolve_path
from .core.pants_utils import pants_download_info, check_pants_dataset, find_pants_case, import_pants_case, import_pants_files, evaluate_segmentation_folder
from .core.presets import SHAPEKIT_ABDOMEN_ROI, SHAPEKIT_EXPECTED_ORGANS
from .core.projection_builder import build_projection
from .core.radthinking import build_patient_traces_from_outputs, build_reasoning_trace, check_radthinking_patient, compare_temporal_masks, discover_radthinking_scans, extract_observation, parse_report_sections
from .core.reasoning_trace import create_radthinking_trace_template
from .core.shapekit_runner import run_shapekit
from .core.summary import summarize_segmentation_folder, write_run_summary
from .core.totalseg_runner import run_custom_inference, run_totalsegmentator
from .core.vlm_label_expert import run_vlm_label_expert


def emit(data: dict) -> None:
    click.echo(json.dumps(to_jsonable(data), indent=2, ensure_ascii=False))


def fail(data: dict, code: int = 1) -> None:
    emit(data); raise SystemExit(code)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--json", "use_json", is_flag=True, default=False, help="Output machine-readable JSON. This CLI always emits JSON for agent compatibility.")
def cli(use_json: bool):
    """medai-cli: CLI-Anything style medical AI toolchain and lightweight agent loop."""


@cli.command("doctor")
@click.option("--shapekit-root", default="third_party/ShapeKit-main", show_default=True)
def doctor_cmd(shapekit_root: str):
    result = check_environment(resolve_path(shapekit_root))
    result["teacher_task_alignment"] = {"ai_model_backend": "TotalSegmentator medical image segmentation model/tool or custom infer command", "postprocess_tool": "ShapeKit", "cli_standard": "CLI-Anything-style command interface with JSON output", "data_format": "PanTS/ShapeKit-like case folder: case_id/segmentations/*.nii.gz", "reasoning_layer": "RadThinking-style longitudinal trace"}
    emit(result)


@cli.command("presets")
def presets_cmd():
    emit({"roi_preset": "shapekit_abdomen", "totalsegmentator_roi_subset": SHAPEKIT_ABDOMEN_ROI, "shapekit_expected_organs": SHAPEKIT_EXPECTED_ORGANS})




@cli.command("pants-info")
def pants_info_cmd():
    """Show official PanTS download/layout information without downloading data."""
    emit(pants_download_info())


@cli.command("pants-check")
@click.option("--pants-root", required=True, help="Path to PanTS repo root or PanTS/data folder.")
@click.option("--max-cases", default=10, type=int, show_default=True)
def pants_check_cmd(pants_root: str, max_cases: int):
    """Check whether real PanTS images/labels/reports have been downloaded."""
    emit(check_pants_dataset(resolve_path(pants_root), max_cases=max_cases))




@cli.command("pants-find-case")
@click.option("--pants-root", required=True, help="Path to PanTS repo root or PanTS/data folder.")
@click.option("--case-id", required=True, help="PanTS case id, e.g., PanTS_00000001")
@click.option("--split", default="auto", type=click.Choice(["auto", "train", "test"]), show_default=True)
def pants_find_case_cmd(pants_root: str, case_id: str, split: str):
    """Locate a downloaded PanTS case without importing it."""
    emit(find_pants_case(resolve_path(pants_root), case_id, split))


@cli.command("pants-import-case")
@click.option("--pants-root", required=True, help="Path to PanTS repo root or PanTS/data folder.")
@click.option("--case-id", required=True, help="PanTS case id, e.g., PanTS_00000001")
@click.option("--output-root", required=True, help="Folder where the imported RadThinking-style patient folder will be created.")
@click.option("--split", default="auto", type=click.Choice(["auto", "train", "test"]), show_default=True)
@click.option("--patient-id", default=None, help="Optional patient folder name. Defaults to case id.")
@click.option("--scan-id", default=None, help="Optional scan id. Defaults to case id.")
@click.option("--copy-labels/--no-copy-labels", default=True, show_default=True)
def pants_import_case_cmd(pants_root: str, case_id: str, output_root: str, split: str, patient_id: str | None, scan_id: str | None, copy_labels: bool):
    """Import one downloaded PanTS case into this CLI's RadThinking-style layout."""
    emit(import_pants_case(resolve_path(pants_root), case_id, resolve_path(output_root), split=split, patient_id=patient_id, scan_id=scan_id, copy_labels=copy_labels))


@cli.command("pants-import-files")
@click.option("--ct", "ct_path", required=True, help="Path to one real ct.nii.gz file.")
@click.option("--label-folder", default=None, help="Optional folder containing reference masks, e.g., segmentations/*.nii.gz")
@click.option("--output-root", required=True, help="Folder where the imported patient folder will be created.")
@click.option("--patient-id", required=True, help="Patient/case folder name to create.")
@click.option("--scan-id", default=None, help="Optional scan id. Defaults to patient id.")
@click.option("--report", "report_path", default=None, help="Optional report.txt or source report path.")
@click.option("--copy-labels/--no-copy-labels", default=True, show_default=True)
def pants_import_files_cmd(ct_path: str, label_folder: str | None, output_root: str, patient_id: str, scan_id: str | None, report_path: str | None, copy_labels: bool):
    """Import any one PanTS-like CT case into this CLI layout, without requiring full PanTS download."""
    emit(import_pants_files(resolve_path(ct_path), resolve_path(label_folder) if label_folder else None, resolve_path(output_root), patient_id=patient_id, scan_id=scan_id, report_path=resolve_path(report_path) if report_path else None, copy_labels=copy_labels))


@cli.command("pants-eval-case")
@click.option("--pred-folder", required=True, help="Folder containing predicted masks, usually .../segmentations")
@click.option("--reference-label-folder", required=True, help="Folder containing reference masks from imported PanTS case")
@click.option("--organs", default=None, help="Comma-separated mask names/organs, e.g. pancreas,pancreatic_lesion,liver. Defaults to all reference masks.")
def pants_eval_case_cmd(pred_folder: str, reference_label_folder: str, organs: str | None):
    """Compute simple binary Dice for one case. This is a sanity check, not full PanTS benchmark."""
    organ_list = [x.strip() for x in organs.replace(';', ',').split(',') if x.strip()] if organs else None
    emit(evaluate_segmentation_folder(resolve_path(pred_folder), resolve_path(reference_label_folder), organ_list))


@cli.command("check-image")
@click.option("--image", required=True)
def check_image_cmd(image: str): emit(check_ct_image(resolve_path(image)))


@cli.command("check-folder")
@click.option("--input-folder", required=True)
def check_folder_cmd(input_folder: str): emit(check_case_folder(resolve_path(input_folder)))


@cli.command("infer")
@click.option("--image", required=True)
@click.option("--output-folder", required=True)
@click.option("--case-id", default=None)
@click.option("--backend", default="totalseg", type=click.Choice(["totalseg", "custom"]), show_default=True)
@click.option("--model-command", default=None)
@click.option("--fast/--no-fast", default=True, show_default=True)
@click.option("--task", default=None)
@click.option("--roi-preset", default="shapekit_abdomen", show_default=True)
@click.option("--roi-subset", default=None)
@click.option("--device", default=None)
@click.option("--adapt/--no-adapt", default=True, show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
def infer_cmd(image, output_folder, case_id, backend, model_command, fast, task, roi_preset, roi_subset, device, adapt, dry_run):
    if backend == "totalseg":
        infer_result = run_totalsegmentator(resolve_path(image), resolve_path(output_folder), case_id, fast, task, roi_preset, roi_subset, device, dry_run=dry_run)
    else:
        if not model_command: fail({"status": "failed", "reason": "--model-command is required for custom backend"})
        infer_result = run_custom_inference(resolve_path(image), resolve_path(output_folder), model_command, case_id, dry_run)
    adapter_result = normalize_totalseg_to_shapekit(infer_result["segmentation_output"]) if adapt and infer_result.get("status") == "success" and infer_result.get("segmentation_output") and not dry_run else None
    emit({"pipeline_stage": "infer", "infer": infer_result, "adapter": adapter_result})


@cli.command("adapt")
@click.option("--segmentation-folder", required=True)
def adapt_cmd(segmentation_folder: str): emit(normalize_totalseg_to_shapekit(resolve_path(segmentation_folder)))


@cli.command("postprocess")
@click.option("--input-folder", required=True)
@click.option("--output-folder", required=True)
@click.option("--shapekit-root", default="third_party/ShapeKit-main", show_default=True)
@click.option("--log-folder", default=None)
@click.option("--cpu-count", default=2, show_default=True, type=int)
@click.option("--continue-prediction", is_flag=True, default=False)
@click.option("--auto-config/--no-auto-config", default=True, show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
def postprocess_cmd(input_folder, output_folder, shapekit_root, log_folder, cpu_count, continue_prediction, auto_config, dry_run):
    out = resolve_path(output_folder); logs = resolve_path(log_folder) if log_folder else out / "logs"
    emit(run_shapekit(resolve_path(shapekit_root), resolve_path(input_folder), out, logs, cpu_count, continue_prediction, dry_run=dry_run, auto_config=auto_config))


@cli.command("run")
@click.option("--image", required=True)
@click.option("--output-folder", required=True)
@click.option("--case-id", default=None)
@click.option("--backend", default="totalseg", type=click.Choice(["totalseg", "custom"]), show_default=True)
@click.option("--model-command", default=None)
@click.option("--postprocess", default="shapekit", type=click.Choice(["none", "shapekit"]), show_default=True)
@click.option("--shapekit-root", default="third_party/ShapeKit-main", show_default=True)
@click.option("--fast/--no-fast", default=True, show_default=True)
@click.option("--task", default=None)
@click.option("--roi-preset", default="shapekit_abdomen", show_default=True)
@click.option("--roi-subset", default=None)
@click.option("--device", default=None)
@click.option("--cpu-count", default=2, type=int, show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
def run_cmd(image, output_folder, case_id, backend, model_command, postprocess, shapekit_root, fast, task, roi_preset, roi_subset, device, cpu_count, dry_run):
    out = resolve_path(output_folder); raw = out / "raw_predictions"; refined = out / "refined_predictions"; logs = out / "logs"
    if backend == "totalseg": infer_result = run_totalsegmentator(resolve_path(image), raw, case_id, fast, task, roi_preset, roi_subset, device, dry_run=dry_run)
    else:
        if not model_command: fail({"status": "failed", "reason": "--model-command is required for custom backend"})
        infer_result = run_custom_inference(resolve_path(image), raw, model_command, case_id, dry_run)
    adapter_result = normalize_totalseg_to_shapekit(infer_result["segmentation_output"]) if infer_result.get("status") == "success" and not dry_run else None
    post_result = None; summary = None
    if postprocess == "shapekit" and infer_result.get("status") == "success":
        post_result = run_shapekit(resolve_path(shapekit_root), raw, refined, logs, cpu_count, dry_run=dry_run)
        if not dry_run: summary = summarize_segmentation_folder(refined if post_result.get("status") == "success" else raw)
    elif infer_result.get("status") == "success" and not dry_run: summary = summarize_segmentation_folder(raw)
    result = {"pipeline": "AI infer + adapter + optional ShapeKit", "teacher_alignment": {"AI_model_infer": "TotalSegmentator/custom", "ShapeKit": "post-processing, not model", "CLI_Anything": "single JSON CLI", "PanTS": "case_id/segmentations layout"}, "infer": infer_result, "adapter": adapter_result, "postprocess": post_result, "final_summary": summary}
    if not dry_run: result["summary_json"] = write_run_summary(out, result)
    emit(result)


@cli.command("summary")
@click.option("--folder", required=True)
def summary_cmd(folder: str): emit(summarize_segmentation_folder(resolve_path(folder)))


@cli.command("radthinking-check")
@click.option("--patient-folder", required=True)
def radthinking_check_cmd(patient_folder: str): emit(check_radthinking_patient(resolve_path(patient_folder)))


@cli.command("radthinking-run-patient")
@click.option("--patient-folder", required=True)
@click.option("--output-folder", required=True)
@click.option("--backend", default="totalseg", type=click.Choice(["totalseg", "custom"]), show_default=True)
@click.option("--model-command", default=None)
@click.option("--postprocess", default="shapekit", type=click.Choice(["none", "shapekit"]), show_default=True)
@click.option("--shapekit-root", default="third_party/ShapeKit-main", show_default=True)
@click.option("--fast/--no-fast", default=True, show_default=True)
@click.option("--task", default=None)
@click.option("--roi-preset", default="shapekit_abdomen", show_default=True)
@click.option("--roi-subset", default=None)
@click.option("--device", default=None)
@click.option("--cpu-count", default=2, type=int, show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
def radthinking_run_patient_cmd(patient_folder, output_folder, backend, model_command, postprocess, shapekit_root, fast, task, roi_preset, roi_subset, device, cpu_count, dry_run):
    patient_root = resolve_path(patient_folder); out_root = resolve_path(output_folder); scans = discover_radthinking_scans(patient_root); results = []
    for scan in scans:
        scan_out = out_root / scan.scan_id; raw = scan_out / "raw_predictions"; refined = scan_out / "refined_predictions"; logs = scan_out / "logs"; case_id = f"{patient_root.name}_{scan.scan_id}"
        if not scan.ct_image: results.append({"scan_id": scan.scan_id, "status": "skipped", "reason": "ct image missing"}); continue
        if backend == "totalseg": infer_result = run_totalsegmentator(scan.ct_image, raw, case_id, fast, task, roi_preset, roi_subset, device, dry_run=dry_run)
        else:
            if not model_command: fail({"status": "failed", "reason": "--model-command is required for custom backend"})
            infer_result = run_custom_inference(scan.ct_image, raw, model_command, case_id, dry_run)
        adapter = normalize_totalseg_to_shapekit(infer_result["segmentation_output"]) if infer_result.get("status") == "success" and not dry_run else None
        post = run_shapekit(resolve_path(shapekit_root), raw, refined, logs, cpu_count, dry_run=dry_run) if postprocess == "shapekit" and infer_result.get("status") == "success" else None
        results.append({"scan_id": scan.scan_id, "case_id": case_id, "ct_image": str(scan.ct_image), "infer": infer_result, "adapter": adapter, "postprocess": post})
    result = {"pipeline": "RadThinking patient batch: per-scan AI inference + optional ShapeKit", "status": "success" if results else "warning", "patient_folder": str(patient_root), "output_folder": str(out_root), "num_scans": len(scans), "num_attempted": len(results), "not_agent_loop": "deterministic patient workflow", "results": results}
    if not dry_run: result["summary_json"] = write_run_summary(out_root, result)
    emit(result)


@cli.command("trace-template")
@click.option("--case-id", required=True)
@click.option("--ct-image", default=None)
@click.option("--segmentation-folder", default=None)
@click.option("--report-path", default=None)
@click.option("--prior-case-id", default=None)
def trace_template_cmd(case_id, ct_image, segmentation_folder, report_path, prior_case_id): emit(create_radthinking_trace_template(case_id, str(resolve_path(ct_image)) if ct_image else None, str(resolve_path(segmentation_folder)) if segmentation_folder else None, str(resolve_path(report_path)) if report_path else None, prior_case_id))


@cli.command("trace-observation")
@click.option("--ct-image", required=True)
@click.option("--mask", "mask_path", required=True)
@click.option("--organ", default=None)
def trace_observation_cmd(ct_image, mask_path, organ): emit(extract_observation(resolve_path(ct_image), resolve_path(mask_path), organ))


@cli.command("trace-temporal")
@click.option("--previous-mask", default=None)
@click.option("--current-mask", default=None)
@click.option("--organ", default=None)
def trace_temporal_cmd(previous_mask, current_mask, organ): emit(compare_temporal_masks(resolve_path(previous_mask) if previous_mask else None, resolve_path(current_mask) if current_mask else None, organ))


@cli.command("trace-context")
@click.option("--report", "report_path", default=None)
@click.option("--clinical", "clinical_path", default=None)
@click.option("--organ", default=None)
def trace_context_cmd(report_path, clinical_path, organ): emit(parse_report_sections(resolve_path(report_path) if report_path else None, resolve_path(clinical_path) if clinical_path else None, organ))


@cli.command("trace-build")
@click.option("--patient-folder", default=None)
@click.option("--scan-id", default=None)
@click.option("--ct-image", default=None)
@click.option("--current-mask", default=None)
@click.option("--previous-mask", default=None)
@click.option("--organ", default=None)
@click.option("--report", "report_path", default=None)
@click.option("--clinical", "clinical_path", default=None)
@click.option("--pathology", "pathology_path", default=None)
@click.option("--output-json", default=None)
def trace_build_cmd(patient_folder, scan_id, ct_image, current_mask, previous_mask, organ, report_path, clinical_path, pathology_path, output_json): emit(build_reasoning_trace(resolve_path(patient_folder) if patient_folder else None, scan_id, resolve_path(ct_image) if ct_image else None, resolve_path(current_mask) if current_mask else None, resolve_path(previous_mask) if previous_mask else None, organ, resolve_path(report_path) if report_path else None, resolve_path(clinical_path) if clinical_path else None, resolve_path(pathology_path) if pathology_path else None, resolve_path(output_json) if output_json else None))


@cli.command("trace-patient")
@click.option("--patient-folder", required=True)
@click.option("--output-folder", required=True)
@click.option("--organ", required=True)
@click.option("--output-json", default=None)
def trace_patient_cmd(patient_folder, output_folder, organ, output_json): emit(build_patient_traces_from_outputs(resolve_path(patient_folder), resolve_path(output_folder), organ, resolve_path(output_json) if output_json else None))


@cli.command("agent-loop")
@click.option("--patient-folder", required=True)
@click.option("--output-folder", required=True)
@click.option("--backend", default="totalseg", type=click.Choice(["totalseg", "custom"]), show_default=True)
@click.option("--model-command", default=None)
@click.option("--postprocess", default="shapekit", type=click.Choice(["none", "shapekit"]), show_default=True)
@click.option("--shapekit-root", default="third_party/ShapeKit-main", show_default=True)
@click.option("--fast/--no-fast", default=True, show_default=True)
@click.option("--task", default=None)
@click.option("--roi-preset", default="shapekit_abdomen", show_default=True)
@click.option("--roi-subset", default=None)
@click.option("--device", default=None)
@click.option("--cpu-count", default=2, type=int, show_default=True)
@click.option("--organ", default="liver", show_default=True)
@click.option("--expected-organs", default="liver,pancreas,aorta,postcava", show_default=True)
@click.option("--enable-trace/--no-enable-trace", default=True, show_default=True)
@click.option("--enable-qc/--no-enable-qc", default=True, show_default=True)
@click.option("--retry-failed/--no-retry-failed", default=True, show_default=True)
@click.option("--max-iterations", default=1, type=int, show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--max-scans", default=None, type=int, help="Optional smoke-test limit for processing only the first N scans.")
@click.option("--shapekit-timeout-sec", default=120, type=int, show_default=True, help="Maximum seconds allowed for each ShapeKit call before fallback/review.")
@click.option("--enable-vlm-refinement", is_flag=True, default=False, help="Enable real VLM calls during iterative refinement (max_iterations>=2). Default: stub.")
@click.option("--vlm-backend-refinement", default="stub", type=click.Choice(["ollama", "stub"]), show_default=True)
@click.option("--vlm-model-refinement", default="qwen2.5vl:7b", show_default=True)
def agent_loop_cmd(patient_folder, output_folder, backend, model_command, postprocess, shapekit_root, fast, task, roi_preset, roi_subset, device, cpu_count, organ, expected_organs, enable_trace, enable_qc, retry_failed, max_iterations, dry_run, max_scans, shapekit_timeout_sec, enable_vlm_refinement, vlm_backend_refinement, vlm_model_refinement):
    organs = [x.strip() for x in expected_organs.replace(";", ",").split(",") if x.strip()]
    if backend == "custom" and not model_command: fail({"status": "failed", "reason": "--model-command is required for custom backend"})
    emit(run_agent_loop(resolve_path(patient_folder), resolve_path(output_folder), backend, model_command, postprocess, resolve_path(shapekit_root), fast, task, roi_preset, roi_subset, device, cpu_count, organ, organs, enable_trace, enable_qc, retry_failed, max_iterations, dry_run, max_scans, shapekit_timeout_sec, enable_vlm_refinement, vlm_backend_refinement, vlm_model_refinement))


@cli.command("label-verify")
@click.option("--annotation-folder", required=True, help="Folder with current annotations (ground truth / prior labels).")
@click.option("--prediction-folder", required=True, help="Folder with model predictions.")
@click.option("--organs", default="pancreas,liver,spleen,kidney_left,kidney_right,aorta", show_default=True)
@click.option("--dsc-replace-threshold", default=0.0, type=float, show_default=True, help="DSC at or below this → auto_replace_candidate.")
@click.option("--dsc-vlm-threshold", default=0.5, type=float, show_default=True, help="DSC below this → send_to_vlm_label_expert.")
def label_verify_cmd(annotation_folder, prediction_folder, organs, dsc_replace_threshold, dsc_vlm_threshold):
    """Compare current annotations vs model predictions using DSC thresholds (Label Verifier)."""
    organ_list = [x.strip() for x in organs.replace(";", ",").split(",") if x.strip()]
    emit(verify_case(resolve_path(annotation_folder), resolve_path(prediction_folder),
                     organ_list, dsc_replace_threshold, dsc_vlm_threshold))


@cli.command("projection-build")
@click.option("--ct-image", required=True, help="Path to CT image (.nii.gz).")
@click.option("--annotation-a", default=None, help="Candidate A mask (.nii.gz).")
@click.option("--annotation-b", default=None, help="Candidate B mask (.nii.gz).")
@click.option("--organ", required=True, help="Organ name, e.g. pancreas.")
@click.option("--output-folder", required=True, help="Where to save projection PNGs.")
@click.option("--views", default="axial,coronal", show_default=True, help="Comma-separated views: axial,coronal,sagittal.")
@click.option("--strict-alignment/--no-strict-alignment", default=False, show_default=True, help="Fail if mask/CT affine or shape mismatch detected.")
def projection_build_cmd(ct_image, annotation_a, annotation_b, organ, output_folder, views, strict_alignment):
    """Build 2D CT+mask overlay PNGs for manual inspection or VLM input."""
    view_list = [v.strip() for v in views.split(",") if v.strip()]
    emit(build_projection(
        resolve_path(ct_image),
        resolve_path(annotation_a) if annotation_a else None,
        resolve_path(annotation_b) if annotation_b else None,
        resolve_path(output_folder),
        organ=organ,
        views=view_list,
        strict_alignment=strict_alignment,
    ))


@cli.command("vlm-label-expert")
@click.option("--ct-image", required=True, help="Path to CT image (.nii.gz).")
@click.option("--annotation-a", default=None, help="Current annotation mask (.nii.gz).")
@click.option("--annotation-b", default=None, help="Model prediction mask (.nii.gz).")
@click.option("--organ", required=True, help="Organ name, e.g. pancreas.")
@click.option("--output-folder", required=True, help="Where to save projections and results.")
@click.option("--vlm-backend", default="ollama", type=click.Choice(["ollama", "stub"]), show_default=True)
@click.option("--vlm-model", default="qwen2.5vl:7b", show_default=True)
@click.option("--case-id", default=None)
@click.option("--dsc-replace-threshold", default=0.0, type=float, show_default=True)
@click.option("--dsc-vlm-threshold", default=0.5, type=float, show_default=True)
@click.option("--strict-alignment/--no-strict-alignment", default=False, show_default=True, help="Fail if mask/CT affine or shape mismatch detected.")
def vlm_label_expert_cmd(ct_image, annotation_a, annotation_b, organ, output_folder,
                          vlm_backend, vlm_model, case_id, dsc_replace_threshold, dsc_vlm_threshold,
                          strict_alignment):
    """VLM Label Expert: project 3D masks to 2D, compare with VLM, output annotation decision."""
    emit(run_vlm_label_expert(
        resolve_path(ct_image),
        resolve_path(annotation_a) if annotation_a else None,
        resolve_path(annotation_b) if annotation_b else None,
        organ, resolve_path(output_folder),
        vlm_backend, vlm_model, case_id,
        dsc_replace_threshold, dsc_vlm_threshold,
        strict_alignment=strict_alignment,
    ))


@cli.command("em-loop")
@click.option("--case-id", required=True, help="Unique case identifier.")
@click.option("--ct-image", required=True, help="Path to CT image (.nii.gz).")
@click.option("--annotation-folder", required=True, help="Folder with reference label masks (*.nii.gz).")
@click.option("--output-folder", required=True, help="Output folder for predictions, annotations, metrics.")
@click.option("--organs", default="pancreas,liver,spleen,kidney_left,kidney_right,aorta", show_default=True)
@click.option("--num-rounds", default=2, type=int, show_default=True, help="Number of EM rounds.")
@click.option("--vlm-backend", default="ollama", type=click.Choice(["ollama", "stub"]), show_default=True)
@click.option("--vlm-model", default="qwen2.5vl:7b", show_default=True)
@click.option("--dsc-replace-threshold", default=0.0, type=float, show_default=True)
@click.option("--dsc-vlm-threshold", default=0.5, type=float, show_default=True)
@click.option("--fast/--no-fast", default=True, show_default=True)
@click.option("--device", default=None, help="TotalSegmentator device (cpu/gpu).")
@click.option("--postprocess", default="none", type=click.Choice(["none", "shapekit"]), show_default=True,
              help="Apply ShapeKit anatomy-aware refinement after inference in each round.")
@click.option("--shapekit-root", default="third_party/ShapeKit-main", show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
def em_loop_cmd(case_id, ct_image, annotation_folder, output_folder, organs,
                num_rounds, vlm_backend, vlm_model, dsc_replace_threshold,
                dsc_vlm_threshold, fast, device, postprocess, shapekit_root, dry_run):
    """Mini EM loop: TotalSegmentator → (ShapeKit) → Label Verifier → VLM → annotation update."""
    organ_list = [x.strip() for x in organs.replace(";", ",").split(",") if x.strip()]
    emit(run_em_loop(
        case_id=case_id,
        ct_image=resolve_path(ct_image),
        annotation_folder=resolve_path(annotation_folder),
        output_folder=resolve_path(output_folder),
        organs=organ_list,
        num_rounds=num_rounds,
        vlm_backend=vlm_backend,
        vlm_model=vlm_model,
        dsc_replace_threshold=dsc_replace_threshold,
        dsc_vlm_threshold=dsc_vlm_threshold,
        fast=fast,
        device=device,
        postprocess=postprocess,
        shapekit_root=resolve_path(shapekit_root),
        dry_run=dry_run,
    ))


def main(): cli()
if __name__ == "__main__": main()
