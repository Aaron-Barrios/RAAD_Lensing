import json
import numpy as np
from scipy.ndimage import gaussian_filter
from pathlib import Path

root = Path(__file__).resolve().parents[3]
clean_dir = root / "test_proto"
output_dir = Path(__file__).resolve().parent / "output"

# Blur sizes as full width at half maximum on the sky [uas]; the EHT beam is ~20 uas
fwhms_uas = [15.0, 20.0, 25.0]

FWHM_TO_SIGMA = 1.0 / (2.0 * np.sqrt(2.0 * np.log(2.0)))


def pixel_size_uas(data):
    """Pixel size [uas] of an .npz image (test_proto or AART dataset format)."""
    meta = json.loads(str(data["meta"]))
    if "psize_uas" in meta:
        return float(meta["psize_uas"])
    axis = data["alpha_rg"]
    return float(axis[1] - axis[0]) * float(meta["theta_g_uas"])


def fwhm_to_sigma_px(fwhm_uas, psize_uas):
    return fwhm_uas * FWHM_TO_SIGMA / psize_uas


def apply_psf(image, fwhm_uas, psize_uas):
    """Gaussian blur with the given FWHM [uas]."""
    sigma_px = fwhm_to_sigma_px(fwhm_uas, psize_uas)
    return gaussian_filter(image, sigma=sigma_px, mode="reflect")


def main():
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(clean_dir.glob("*.npz")):

        with np.load(path, allow_pickle=False) as data:
            original = {key: data[key] for key in data.files}
            psize_uas = pixel_size_uas(data)

        image = original["image"].astype(float)

        for fwhm in fwhms_uas:
            blurred = apply_psf(image, fwhm, psize_uas)

            result = original.copy()
            result["image"] = blurred
            result["psf_fwhm_uas"] = fwhm
            result["psf_sigma_px"] = fwhm_to_sigma_px(fwhm, psize_uas)

            filename = f"{path.stem}_psf_{fwhm:g}uas.npz"
            np.savez_compressed(output_dir / filename, **result)

    print("Gaussian PSF blurring complete.")


if __name__ == "__main__":
    main()
