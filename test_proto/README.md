# Prototype Sgr A\* images

Twelve 230 GHz images of Sgr A\* from general-relativistic MHD simulations ray-traced with grtrans
(Cyclo-Synchrotron project). They use the same format the AART/GLM training images will have.

## Files

| File | Contents |
|---|---|
| `sgra_i{inc}_Rh{R}_snap.npz` | One snapshot at $t = 1500\,GM/c^3$ |
| `sgra_i{inc}_Rh{R}_mean.npz` | Time average over $250 \le t < 2620\,GM/c^3$ |
| `index.csv` | One row per file: inclination, $R_{\rm high}$, kind, total flux, pixel size, field of view |
| `make_test_proto.py` | Script that produced these files from the original simulation output |

Inclinations: 30° and 60°. $R_{\rm high}$ (electron-temperature parameter): 1, 20, 100.
All images: spin $a = 0.998$, $M = 4.15\times10^6\,M_\odot$, $D = 8.178$ kpc, $\nu = 230$ GHz.

## Format

Each `.npz` contains:

| Key | Shape | Meaning |
|---|---|---|
| `image` | (512, 512) float32 | Intensity in **Jy per pixel** |
| `alpha_rg` | (512,) | Pixel-center $\alpha$ coordinates (columns), in $GM/c^2$ |
| `beta_rg` | (512,) | Pixel-center $\beta$ coordinates (rows), in $GM/c^2$ |
| `meta` | JSON string | Metadata (below) |

**Orientation:** `image[j, i]` is the pixel at $\beta_j$ (row) and $\alpha_i$ (column), both
increasing from $-30$ to $+30\,GM/c^2$. Row 0 is the **bottom** of the image, so display with
`imshow(image, origin="lower")`. The black hole's spin axis projects onto $+\beta$.

**Scale:**

| Quantity | Value |
|---|---|
| Pixel size | 0.587 µas ($= 0.117\,GM/c^2$; `psize_rad` = $2.846\times10^{-12}$ rad) |
| Field of view | 300.6 µas ($60\,GM/c^2$) |
| $\theta_g = GM/(c^2 D)$ | 5.01 µas |

**Flux:** each image keeps the raw flux of its simulation, from 0.66 Jy ($R_{\rm high} = 1$) down to
$\sim$0.001 Jy ($R_{\rm high} = 100$ snapshots); see `total_flux_jy`. The observed 230 GHz flux of
Sgr A\* is about 2.4 Jy.

**Metadata** (`meta`): `psize_rad`, `psize_uas`, `psize_rg`, `npix`, `fov_uas`, `fov_rg`,
`theta_g_uas`, `freq_hz`, `mbh_msun`, `dist_kpc`, `spin`, `inc_deg`, `r_high`, `kind`, `time_M`,
`total_flux_jy`, `source_file`.

The $R_{\rm high} = 100$ snapshots contain single-pixel speckle from the ray-tracing sampling.

## Loading

```python
import json
import numpy as np

d = np.load("test_proto/sgra_i30_Rh20_mean.npz")
image = d["image"]                      # Jy/pixel, rows = beta, columns = alpha
meta = json.loads(str(d["meta"]))
psize_uas = meta["psize_uas"]           # 0.587
```

---

## AI Acknowledgments

This dataset and document were prepared with the assistance of Claude (Anthropic), used through
Claude Code. The author selected the simulations and directed the content. Claude wrote the export
script, converted the images to the format described here, and wrote this document. The author is
responsible for the final content.
