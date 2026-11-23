import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm


output_dir = Path(__file__).resolve().parent / "output"

if len(sys.argv) > 1:
    image_name = sys.argv[1]
else:
    first_file = next(output_dir.glob("*_psf_*px.npz"))
    image_name = first_file.stem.rsplit("_psf_", 1)[0]

if "_psf_" in image_name:
    image_name = image_name.split("_psf_", 1)[0]

files = sorted(output_dir.glob(f"{image_name}_psf_*px.npz"))
if not files:
    print("No blurred images found for:", image_name)
    raise SystemExit(1)

fig, axes = plt.subplots(1, len(files), figsize=(4 * len(files), 4))
if len(files) == 1:
    axes = [axes]

for ax, path in zip(axes, files):
    with np.load(path) as data:
        image = data["image"]
        sigma = float(data["psf_sigma_px"])

    positive = image[image > 0]
    norm = LogNorm(vmin=positive.min(), vmax=image.max()) if positive.size else None
    ax.imshow(image, origin="lower", cmap="inferno", norm=norm)
    height, width = image.shape
    margin_x = width // 4
    margin_y = height // 4
    ax.set_xlim(width // 2 - margin_x, width // 2 + margin_x)
    ax.set_ylim(height // 2 - margin_y, height // 2 + margin_y)
    ax.set_title(f"PSF sigma = {sigma}px")
    ax.axis("off")

plt.suptitle(image_name)
plt.tight_layout()
plot_dir = Path(__file__).resolve().parent
plt.savefig(plot_dir / f"{image_name}_blurred.png", dpi=200)
print("Saved:", plot_dir / f"{image_name}_blurred.png")
