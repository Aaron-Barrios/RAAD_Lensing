import numpy as np
from scipy.ndimage import gaussian_filter
from pathlib import Path

root = Path(__file__).resolve().parents[3]
clean_dir = root / "test_proto"
output_dir = Path(__file__).resolve().parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

sigmas = [0.5, 1.0, 2.0, 3.0]

def apply_psf(image, sigma):
    return gaussian_filter(image, sigma=sigma, mode="reflect")

for path in sorted(clean_dir.glob("*.npz")):

    with np.load(path, allow_pickle=False) as data:
        original = {key: data[key] for key in data.files}

    image = original["image"].astype(float)

    for sigma in sigmas:
        blurred = apply_psf(image, sigma)

        result = original.copy()
        result["image"] = blurred
        result["psf_sigma_px"] = sigma

        filename = f"{path.stem}_psf_{sigma:g}px.npz"
        np.savez_compressed(output_dir / filename, **result)

print("Gaussian PSF blurring complete.")