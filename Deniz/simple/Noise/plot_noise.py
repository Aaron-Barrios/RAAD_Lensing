import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


output_dir = Path(__file__).resolve().parent / "output"
plot_dir = Path(__file__).resolve().parent
image_name = sys.argv[1] if len(sys.argv) > 1 else "sgra_i30_Rh1_mean"
files = sorted(output_dir.glob(f"{image_name}_psf_*px_noise_*peak.npz"))

if not files:
    raise FileNotFoundError(f"No noisy images found for {image_name} in {output_dir}")

images = {}
for path in files:
    with np.load(path, allow_pickle=False) as data:
        sigma = float(data["psf_sigma_px"])
        fraction = float(data["noise_std_fraction_of_peak"])
        images[sigma, fraction] = data["image"]

sigmas = sorted({sigma for sigma, _ in images})
noise_levels = sorted({fraction for _, fraction in images})
values = np.concatenate([image.ravel() for image in images.values()])
vmin, vmax = values.min(), values.max()

fig, axes = plt.subplots(
    len(sigmas), len(noise_levels),
    figsize=(4 * len(noise_levels), 4 * len(sigmas)),
)

for row, sigma in enumerate(sigmas):
    for column, fraction in enumerate(noise_levels):
        ax = axes[row, column]
        image = images[sigma, fraction]
        height, width = image.shape
        ax.imshow(image, origin="lower", cmap="inferno", vmin=vmin, vmax=vmax)
        ax.set_xlim(3 * width // 8, 5 * width // 8)
        ax.set_ylim(3 * height // 8, 5 * height // 8)
        ax.set_title(f"PSF {sigma:g}px, noise {fraction:.0%}")
        ax.axis("off")

fig.suptitle(image_name)
fig.tight_layout(rect=(0, 0, 1, 0.98))
plot_path = plot_dir / f"{image_name}_noise.png"
fig.savefig(plot_path, dpi=200)
plt.close(fig)
print("Saved:", plot_path)
