"""Export a small set of 230 GHz Sgr A* GRMHD images (Cyclo-Synchrotron grtrans runs)
into plain .npz files for prototyping the degradation (blurring / EHT sampling) pipeline.

Each output file holds one image in Jy/pixel on a square grid, with rows = beta and
columns = alpha (row 0 at the bottom), plus the metadata needed to place it on the sky.

Run from the repository root:
    .venv/bin/python test_proto/make_test_proto.py
"""
import csv
import json
import os

import h5py
import numpy as np

SRC = "/home/aaron/Research/Cylco-Synchrotron/fluid_out/Data_vert_B0.6_pair/raytrace"
OUT = os.path.dirname(os.path.abspath(__file__))

INCS = (30, 60)                       # observer inclination [deg]
RHIGHS = (1, 20, 100)                 # electron-temperature parameter R_high
NUP = {1: 400, 20: 1600, 100: 6400}   # file-name tag per R_high
T_SNAP = 1500.0                       # snapshot time [GM/c^3]
T_MIN, T_MAX = 250.0, 2620.0          # averaging window [GM/c^3]

G, C, MSUN, KPC = 6.674e-8, 2.998e10, 1.989e33, 3.0857e21   # cgs
DIST_KPC = 8.178
RAD_TO_UAS = 180.0 / np.pi * 3600.0 * 1e6


def src_path(inc, rh):
    return os.path.join(SRC, f"inc{inc}_a0p998_infinity_fov30_npix512_f230000MHz_d4_"
                             f"rlN1836_Rl1_Rh{rh}_sp0p5_rm80_n{NUP[rh]}.h5")


def clean(frame):
    """Stored frames are indexed [alpha, beta]; return [beta, alpha], NaN -> 0, no negatives."""
    return np.clip(np.nan_to_num(frame.astype(np.float64)), 0.0, None).T


def main():
    rows = []
    for inc in INCS:
        for rh in RHIGHS:
            p = src_path(inc, rh)
            with h5py.File(p, "r") as f:
                cam = json.loads(f.attrs["camera"])
                t = f["times"][:]
                k = int(np.argmin(np.abs(t - T_SNAP)))
                snap = clean(f["I"][k])
                idx = np.nonzero((t >= T_MIN) & (t < T_MAX))[0]
                mean = np.zeros_like(snap)
                for j in idx:
                    mean += clean(f["I"][j])
                mean /= len(idx)
                alpha_axis = f["alpha"][:, 0].astype(np.float64)
                beta_axis = f["beta"][0, :].astype(np.float64)

            npix = cam["npix"]
            half_width_rg = cam["fov_rg"]                     # image spans +/- fov_rg
            psize_rg = 2.0 * half_width_rg / npix
            r_g_cm = G * cam["m_bh_msun"] * MSUN / C**2
            theta_g_rad = r_g_cm / (DIST_KPC * KPC)
            psize_rad = psize_rg * theta_g_rad
            # cgs specific intensity -> Jy per pixel: I * (pixel solid angle) * 1e23
            to_jy = psize_rad**2 * 1e23

            for kind, img, time_label in (("snap", snap, float(t[k])),
                                          ("mean", mean, f"{T_MIN:g}-{T_MAX:g}")):
                img_jy = (img * to_jy).astype(np.float32)
                name = f"sgra_i{inc}_Rh{rh}_{kind}.npz"
                meta = dict(
                    psize_rad=psize_rad, psize_uas=psize_rad * RAD_TO_UAS,
                    psize_rg=psize_rg, npix=npix,
                    fov_uas=npix * psize_rad * RAD_TO_UAS, fov_rg=2.0 * half_width_rg,
                    theta_g_uas=theta_g_rad * RAD_TO_UAS,
                    freq_hz=float(cam["freq_hz"]), mbh_msun=float(cam["m_bh_msun"]),
                    dist_kpc=DIST_KPC, spin=float(cam["spin"]), inc_deg=float(inc),
                    r_high=float(rh), kind=kind, time_M=str(time_label),
                    total_flux_jy=float(img_jy.sum()), source_file=os.path.basename(p),
                )
                np.savez_compressed(os.path.join(OUT, name), image=img_jy,
                                    alpha_rg=alpha_axis, beta_rg=beta_axis,
                                    meta=json.dumps(meta))
                rows.append(dict(file=name, **{k_: meta[k_] for k_ in (
                    "inc_deg", "r_high", "kind", "time_M", "total_flux_jy",
                    "npix", "psize_uas", "fov_uas", "spin", "freq_hz")}))
                print(f"{name}: {img_jy.sum():.3f} Jy")

    with open(os.path.join(OUT, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
