from pathlib import Path

import numpy as np


root = Path(__file__).resolve().parents[3]
clean_dir = root / "test_proto"
blurred_dir = root / "Deniz" / "simple" / "Blurring" / "output"
output_dir = Path(__file__).resolve().parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

noise_levels = [0.01, 0.03, 0.05]
rng = np.random.default_rng(2026)

for path in sorted(blurred_dir.glob("*_psf_*px.npz")):
    clean_name = path.stem.rsplit("_psf_", 1)[0] + ".npz"
    with np.load(clean_dir / clean_name, allow_pickle=False) as data:
        clean_peak = float(np.max(np.abs(data["image"])))

    with np.load(path, allow_pickle=False) as data:
        original = {key: data[key] for key in data.files}

    for fraction in noise_levels:
        noise_std = fraction * clean_peak
        noisy = original["image"].astype(float) + rng.normal(
            0, noise_std, original["image"].shape
        )

        result = original.copy()
        result["image"] = noisy
        result["noise_std"] = noise_std
        result["noise_std_fraction_of_peak"] = fraction

        filename = f"{path.stem}_noise_{fraction:.2f}peak.npz"
        np.savez_compressed(output_dir / filename, **result)

print("Gaussian noise complete.")
