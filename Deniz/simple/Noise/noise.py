from pathlib import Path

import numpy as np


root = Path(__file__).resolve().parents[3]
clean_dir = root / "test_proto"
blurred_dir = root / "Deniz" / "simple" / "Blurring" / "output"
output_dir = Path(__file__).resolve().parent / "output"

noise_levels = [0.01, 0.03, 0.05]


def add_noise(image, fraction, clean_peak, rng):
    """Add Gaussian noise with standard deviation = fraction * clean_peak."""
    noise_std = fraction * clean_peak
    return image + rng.normal(0, noise_std, image.shape), noise_std


def main():
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)

    for path in sorted(blurred_dir.glob("*_psf_*uas.npz")):
        clean_name = path.stem.rsplit("_psf_", 1)[0] + ".npz"
        with np.load(clean_dir / clean_name, allow_pickle=False) as data:
            clean_peak = float(np.max(np.abs(data["image"])))

        with np.load(path, allow_pickle=False) as data:
            original = {key: data[key] for key in data.files}

        for fraction in noise_levels:
            noisy, noise_std = add_noise(original["image"].astype(float), fraction,
                                         clean_peak, rng)

            result = original.copy()
            result["image"] = noisy
            result["noise_std"] = noise_std
            result["noise_std_fraction_of_peak"] = fraction

            filename = f"{path.stem}_noise_{fraction:.2f}peak.npz"
            np.savez_compressed(output_dir / filename, **result)

    print("Gaussian noise complete.")


if __name__ == "__main__":
    main()
