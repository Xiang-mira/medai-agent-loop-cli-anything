from __future__ import annotations

from pathlib import Path

from .qc_checker import mask_volume_cm3


def _dice(mask_a: Path, mask_b: Path) -> float | None:
    try:
        import numpy as np
        import nibabel as nib
        a = np.asanyarray(nib.load(str(mask_a)).dataobj) > 0
        b = np.asanyarray(nib.load(str(mask_b)).dataobj) > 0
        intersection = int((a & b).sum())
        total = int(a.sum()) + int(b.sum())
        return round(2 * intersection / total, 6) if total > 0 else 0.0
    except Exception:
        return None


def verify_annotation(
    current_annotation: str | Path | None,
    model_prediction: str | Path | None,
    organ: str,
    dsc_replace_threshold: float = 0.0,
    dsc_vlm_threshold: float = 0.5,
) -> dict:
    """
    Compare current annotation vs. model prediction for one organ mask.

    Decision rules (mirrors ScaleMAI Label Verifier):
      DSC == 0 (or current empty, prediction non-empty) → auto_replace_candidate
      0 < DSC < dsc_vlm_threshold                       → send_to_vlm_label_expert
      DSC >= dsc_vlm_threshold                           → accept
      Either mask missing                                → review_queue
    """
    result: dict = {"stage": "label_verifier", "organ": organ,
                    "dsc_replace_threshold": dsc_replace_threshold,
                    "dsc_vlm_threshold": dsc_vlm_threshold}

    ann_path = Path(current_annotation).resolve() if current_annotation else None
    pred_path = Path(model_prediction).resolve() if model_prediction else None

    ann_exists = ann_path is not None and ann_path.exists()
    pred_exists = pred_path is not None and pred_path.exists()

    result["current_annotation"] = str(ann_path) if ann_path else None
    result["model_prediction"] = str(pred_path) if pred_path else None
    result["current_annotation_exists"] = ann_exists
    result["model_prediction_exists"] = pred_exists

    if not pred_exists:
        result.update({"status": "failed", "decision": "review_queue",
                       "reason": "Model prediction missing; cannot verify."})
        return result

    if not ann_exists:
        result.update({"status": "warning", "decision": "auto_replace_candidate",
                       "reason": "No current annotation; prediction becomes candidate.",
                       "dice": None})
        return result

    dice = _dice(ann_path, pred_path)
    result["dice"] = dice

    ann_vol = mask_volume_cm3(ann_path)
    pred_vol = mask_volume_cm3(pred_path)
    result["current_voxels"] = ann_vol.get("voxel_count")
    result["prediction_voxels"] = pred_vol.get("voxel_count")

    if dice is None:
        result.update({"status": "failed", "decision": "review_queue",
                       "reason": "DSC computation failed (read error)."})
        return result

    pred_nonempty = (pred_vol.get("voxel_count") or 0) > 10
    ann_empty = (ann_vol.get("voxel_count") or 0) <= 10
    ann_nonempty = not ann_empty

    if dice == 0.0 and pred_nonempty and ann_empty:
        # Annotation is empty, prediction has content → safe to auto-replace.
        result.update({"status": "warning", "decision": "auto_replace_candidate",
                       "reason": "Current annotation is empty but prediction is non-empty. Prediction is a replacement candidate."})
    elif dice == 0.0 and pred_nonempty and ann_nonempty:
        # Both masks non-empty but completely disjoint → likely a localization error.
        # Auto-replace would be too aggressive; route to VLM for pairwise comparison.
        result.update({"status": "warning", "decision": "send_to_vlm_label_expert",
                       "reason": "DSC=0 but both annotation and prediction are non-empty (completely disjoint). "
                                 "Possible localization error — requires VLM pairwise comparison before replacing."})
    elif dice <= dsc_replace_threshold and pred_nonempty and ann_empty:
        # Generalised replace threshold, but only when annotation is effectively empty.
        result.update({"status": "warning", "decision": "auto_replace_candidate",
                       "reason": f"DSC={dice} at or below replace threshold {dsc_replace_threshold} and annotation is empty. Prediction is a replacement candidate."})
    elif dice < dsc_vlm_threshold:
        result.update({"status": "warning", "decision": "send_to_vlm_label_expert",
                       "reason": f"DSC={dice} below VLM threshold {dsc_vlm_threshold}. Requires VLM pairwise comparison."})
    else:
        result.update({"status": "success", "decision": "accept",
                       "reason": f"DSC={dice} >= {dsc_vlm_threshold}. Annotation accepted."})

    return result


def verify_case(
    segmentation_folder: str | Path,
    prediction_folder: str | Path,
    organs: list[str],
    dsc_replace_threshold: float = 0.0,
    dsc_vlm_threshold: float = 0.5,
) -> dict:
    """Run label_verifier on multiple organs for one case."""
    seg_dir = Path(segmentation_folder).resolve()
    pred_dir = Path(prediction_folder).resolve()
    results = []
    for organ in organs:
        ann = seg_dir / f"{organ}.nii.gz"
        pred = pred_dir / f"{organ}.nii.gz"
        r = verify_annotation(ann if ann.exists() else None,
                              pred if pred.exists() else None,
                              organ, dsc_replace_threshold, dsc_vlm_threshold)
        results.append(r)

    decisions = [r["decision"] for r in results]
    needs_vlm = [r for r in results if r.get("decision") == "send_to_vlm_label_expert"]
    needs_replace = [r for r in results if r.get("decision") == "auto_replace_candidate"]
    accepted = [r for r in results if r.get("decision") == "accept"]

    return {
        "stage": "label_verifier_case",
        "segmentation_folder": str(seg_dir),
        "prediction_folder": str(pred_dir),
        "organs_checked": organs,
        "num_accepted": len(accepted),
        "num_vlm_needed": len(needs_vlm),
        "num_replace_candidates": len(needs_replace),
        "organ_results": results,
        "vlm_organs": [r["organ"] for r in needs_vlm],
        "replace_candidate_organs": [r["organ"] for r in needs_replace],
    }
