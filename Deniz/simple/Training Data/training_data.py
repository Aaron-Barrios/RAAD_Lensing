import numpy as np
import json
import csv
from pathlib import Path

root = Path(__file__).resolve().parents[3]
simple_dir = Path(__file__).resolve().parents[1]
clean_dir = root / "test_proto"
blurred_dir = simple_dir / "Blurring" / "output"
noise_dir = simple_dir / "Noise" / "output"

output_dir = Path(__file__).resolve().parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

pairs = []

for path in sorted(noise_dir.glob("*_psf_*uas_noise_*peak.npz")):

    clean_name = path.stem.split("_psf_", 1)[0] + ".npz"
    clean_path = clean_dir / clean_name
    blurred_name = path.stem.split("_noise_", 1)[0] + ".npz"
    blurred_path = blurred_dir / blurred_name

    with np.load(clean_path, allow_pickle=False) as data:
        meta = json.loads(str(data["meta"]))

    with np.load(blurred_path, allow_pickle=False) as data:
        psf_sigma = float(data["psf_sigma_px"])

    with np.load(path, allow_pickle=False) as data:
        noise_std = float(data["noise_std"])
        noise_fraction = float(data["noise_std_fraction_of_peak"])

    pairs.append([
        str(clean_path.relative_to(root)),
        str(blurred_path.relative_to(root)),
        str(path.relative_to(root)),
        meta["spin"],
        meta["inc_deg"],
        psf_sigma,
        noise_std,
        noise_fraction
    ])

with open(output_dir / "dataset_manifest.csv", "w", newline="") as file:

    writer = csv.writer(file, lineterminator="\n")

    writer.writerow([
        "clean_image_path",
        "blurred_image_path",
        "noisy_image_path",
        "spin",
        "inclination_deg",
        "psf_sigma_px",
        "noise_std",
        "noise_fraction_of_peak"
    ])

    writer.writerows(pairs)

print("Number of training pairs:", len(pairs))