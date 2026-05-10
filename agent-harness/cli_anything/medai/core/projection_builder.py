from __future__ import annotations

from pathlib import Path


def build_projection(
    ct_image: str | Path,
    mask_a: str | Path | None,
    mask_b: str | Path | None,
    output_folder: str | Path,
    organ: str = "organ",
    views: list[str] | None = None,
    strict_alignment: bool = False,
) -> dict:
    """
    Create mask-centered 2D slice-overlay images from a 3D CT and up to two candidate masks.
    Saves side-by-side PNG overlays for each view (axial/coronal/sagittal).
    Used by VLM Label Expert to compare candidate annotations.
    """
    if views is None:
        views = ["axial", "coronal"]

    output_dir = Path(output_folder).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import numpy as np
        import nibabel as nib
    except ImportError:
        return {"stage": "projection_builder", "status": "failed",
                "reason": "nibabel not installed"}

    try:
        from PIL import Image as PILImage
        _has_pil = True
    except ImportError:
        _has_pil = False

    ct_path = Path(ct_image).resolve()
    if not ct_path.exists():
        return {"stage": "projection_builder", "status": "failed",
                "reason": f"CT image not found: {ct_path}"}

    ct_img = nib.load(str(ct_path))
    ct_data = np.asanyarray(ct_img.dataobj).astype(float)

    shape_warnings: list[str] = []

    def _load_mask(p, label: str) -> "np.ndarray | None":
        if p is None:
            return None
        pp = Path(p).resolve()
        if not pp.exists():
            return None
        mask_img = nib.load(str(pp))
        arr = np.asanyarray(mask_img.dataobj) > 0
        if arr.shape != ct_data.shape:
            shape_warnings.append(
                f"{label} shape {arr.shape} != CT shape {ct_data.shape}; overlay may be misaligned"
            )
        if not np.allclose(mask_img.affine, ct_img.affine, atol=1e-3):
            shape_warnings.append(
                f"{label} affine does not match CT affine; voxel registration may be off"
            )
        return arr

    mask_a_arr = _load_mask(mask_a, "mask_a")
    mask_b_arr = _load_mask(mask_b, "mask_b")

    if strict_alignment and shape_warnings:
        return {
            "stage": "projection_builder",
            "status": "failed",
            "organ": organ,
            "reason": "strict_alignment=True: mask/CT registration mismatch detected",
            "shape_warnings": shape_warnings,
        }

    # Window CT to soft tissue [-150, 250] HU
    ct_win = np.clip(ct_data, -150, 250)
    ct_norm = ((ct_win + 150) / 400 * 255).astype(np.uint8)

    def _get_slice(arr3d, view, idx=None):
        s = arr3d.shape
        if view == "axial":
            mid = s[2] // 2 if idx is None else idx
            return arr3d[:, :, mid]
        elif view == "coronal":
            mid = s[1] // 2 if idx is None else idx
            return arr3d[:, mid, :]
        else:
            mid = s[0] // 2 if idx is None else idx
            return arr3d[mid, :, :]

    def _find_mask_center(mask_arr, view):
        if mask_arr is None:
            return None
        s = mask_arr.shape
        nz = np.nonzero(mask_arr)
        if len(nz[0]) == 0:
            return None
        if view == "axial":
            return int(np.median(nz[2]))
        elif view == "coronal":
            return int(np.median(nz[1]))
        else:
            return int(np.median(nz[0]))

    saved_files = []
    for view in views:
        ref_mask = mask_a_arr if mask_a_arr is not None else mask_b_arr
        center_idx = _find_mask_center(ref_mask, view)
        ct_slice = _get_slice(ct_norm, view, center_idx)

        panels = []
        for label, mask_arr in [("candidate_A", mask_a_arr), ("candidate_B", mask_b_arr)]:
            if mask_arr is None:
                continue
            mask_slice = _get_slice(mask_arr.astype(np.uint8), view, center_idx)
            # Build RGB overlay: CT grey + red mask overlay
            h, w = ct_slice.shape
            rgb = np.stack([ct_slice, ct_slice, ct_slice], axis=-1)
            rgb[mask_slice > 0, 0] = np.clip(rgb[mask_slice > 0, 0].astype(int) + 120, 0, 255)
            rgb[mask_slice > 0, 2] = np.clip(rgb[mask_slice > 0, 2].astype(int) - 60, 0, 255)
            panels.append((label, rgb))

        if not panels:
            continue

        fname = output_dir / f"{organ}_{view}.png"
        if _has_pil and panels:
            from PIL import ImageDraw
            label_height = 20  # pixels reserved for text header
            if len(panels) == 2:
                h, w = panels[0][1].shape[:2]
                combined = np.zeros((h + label_height, w * 2 + 4, 3), dtype=np.uint8)
                combined[label_height:, :w] = panels[0][1]
                combined[label_height:, w + 4:] = panels[1][1]
                img = PILImage.fromarray(combined)
                draw = ImageDraw.Draw(img)
                draw.text((4, 2), "Candidate A", fill=(255, 220, 0))
                draw.text((w + 8, 2), "Candidate B", fill=(255, 220, 0))
                img.save(str(fname))
            else:
                h, w = panels[0][1].shape[:2]
                padded = np.zeros((h + label_height, w, 3), dtype=np.uint8)
                padded[label_height:] = panels[0][1]
                img = PILImage.fromarray(padded)
                draw = ImageDraw.Draw(img)
                lbl = panels[0][0].replace("candidate_", "Candidate ")
                draw.text((4, 2), lbl, fill=(255, 220, 0))
                img.save(str(fname))
            saved_files.append(str(fname))
        else:
            # Fallback: save raw numpy arrays as npy if PIL not available
            npy_fname = output_dir / f"{organ}_{view}.npy"
            np.save(str(npy_fname), np.stack([p[1] for p in panels]))
            saved_files.append(str(npy_fname))

    return {
        "stage": "projection_builder",
        "status": "success" if saved_files else "failed",
        "organ": organ,
        "views": views,
        "ct_image": str(ct_path),
        "mask_a": str(mask_a) if mask_a else None,
        "mask_b": str(mask_b) if mask_b else None,
        "output_folder": str(output_dir),
        "saved_projections": saved_files,
        "projection_mode": "mask_centered_2d_slice",
        "strict_alignment": strict_alignment,
        "shape_warnings": shape_warnings if shape_warnings else None,
        "note": "Left panel = Candidate A, Right panel = Candidate B. Red overlay = mask region. Uses mask-centered 2D slice (not full MIP).",
    }
