# Proposal Critiques: "Seeing Through the Blur"

Comments on the Phy 5080 project proposal, covering:

1. General comments on the proposal.
2. Accretion disk models, from simplest to most expensive.
3. How to blur the images, based on what the literature does.
4. A recommended plan.

Citations were checked against Crossref, arXiv, and publisher or repository records on
2026-10-20. DOIs are listed where they were confirmed.

---

## 1. General comments on the proposal

### Things to fix or tighten

1. **"Telescope PSF blurring" doesn't match how black holes are actually imaged.** The
   only resolved horizon-scale images (M87\*, Sgr A\*) come from VLBI. In VLBI the
   "blur" comes from sparse Fourier sampling, and the noise lives in the visibilities,
   not in image pixels. A Gaussian blur plus white pixel noise is fine as an idealized
   first model, but the proposal should say that it is an idealization (see §3).

   **Proposed Solution:** TODO

2. **The emission model doesn't fit the targets.** A Novikov–Thorne (NT) disk is
   optically thick and geometrically thin, and it glows thermally in the UV and X-ray
   for supermassive black holes. M87\* and Sgr A\* at 230 GHz are optically thin
   synchrotron from a hot, thick flow. There are two possible framings:
   - "a generic thin disk at some future resolution," or
   - add an optically thin equatorial model (§2, Model B), which is barely more work
     and is also what produces real photon rings.

   The abstract talks about photon rings. An opaque NT disk shows mostly the direct
   image plus a faint $n=1$ ring.

3. **What "analytical lensing deflection" means needs to be pinned down.** If it means
   a Beloborodov-type approximation, that is Schwarzschild-only and throws away exactly
   the spin dependence we are trying to infer. Kerr null geodesics have closed-form
   solutions (Gralla & Lupsasca 2020), and public codes implement them, so we should do
   the exact calculation. It is not slow.

4. **"Traditional deconvolution is slow" is not accurate.** Richardson–Lucy and Wiener
   filtering take milliseconds. The honest argument is that deconvolution is ill-posed
   and generic priors are bad, while a learned prior fits this image class.

5. **Spin is weakly identifiable.** The size of the critical curve changes by only
   about 4% across spin (Johannsen & Psaltis 2010). Most of the spin information sits
   in the ISCO edge and in the asymmetry, and both are degenerate with inclination. So:
   - Predict $\cos i$ rather than $i$.
   - Consider regressing $r_{\rm ISCO}$, or using it as an auxiliary target. It is what
     the image actually encodes, and $a(r_{\rm ISCO})$ is very nonlinear near $a\to1$.
   - Output uncertainties, for example with a Gaussian negative log-likelihood head. A
     point estimate of $a$ under a degeneracy is misleading.
   - Consider sampling retrograde spins too, $a\in[-0.99,0.99]$.

6. **Nuisance parameters.** Either randomize or fix the position angle, the
   mass-to-distance scale (ring size in pixels), and the overall flux normalization.
   Otherwise the network can latch onto them. Rotation is also free data augmentation.

7. **Dataset size.** About 1,500 images is small for a U-Net. With a closed-form ray
   tracer, $10^4$–$10^5$ images take minutes to generate.

8. **Loss and evaluation.**
   - Pure MSE gives oversmoothed reconstructions. Add L1 or SSIM terms.
   - Add a hallucination test: images from a *different* emission model (for example,
     train on Model A and test on Model B or GRMHD). A learned prior will happily
     "restore" a photon ring that isn't there, and showing that would make the
     limitations section concrete.

---

## 2. Disk models, simplest to most expensive

All images should be in units of $M$ (that is, $GM/c^2$; angles in
$\theta_g = GM/c^2D$). For scale:

- M87\*: $\theta_g\approx3.8\,\mu\mathrm{as}$.
- Sgr A\*: $\theta_g\approx5\,\mu\mathrm{as}$.
- The critical-curve diameter is $\approx 2\sqrt{27}\,M\approx10.4\,M$.
- $r_{\rm ISCO}$ runs from $6M$ at $a=0$ to $\approx1.45M$ at $a=0.99$.

### Model 0: Geometric crescents or rings (pipeline debugging only)

Use a ring, crescent (Kamruddin & Dexter 2013), or m-ring (EHT 2019 Paper VI). These are
trivial to generate and have no spin physics. They are useful for checking the
degradation and network code before the physics is ready.

### Model A: Thin Novikov–Thorne disk with exact Kerr ray tracing

This is the proposal's model, done properly.

**Ray tracing.** A pixel $(\alpha,\beta)$ for an observer at inclination $i$ has
conserved quantities

$$\lambda = -\alpha\sin i,\qquad \eta = (\alpha^2 - a^2)\cos^2 i + \beta^2$$

(Bardeen 1973; Cunningham & Bardeen 1973). Gralla & Lupsasca (2020) give the radius
$r_s^{(n)}(\alpha,\beta)$ where the ray crosses the equator for the $n$-th time, in
closed form using elliptic functions. For an opaque disk, keep the first crossing with
$r_s\ge r_{\rm ISCO}$.

**ISCO** (Bardeen, Press & Teukolsky 1972):

$$Z_1 = 1+(1-a^2)^{1/3}\left[(1+a)^{1/3}+(1-a)^{1/3}\right],\quad
Z_2=\sqrt{3a^2+Z_1^2},$$

$$r_{\rm ISCO} = M\left[3+Z_2 \mp\sqrt{(3-Z_1)(3+Z_1+2Z_2)}\right]$$

(upper sign prograde, lower sign retrograde).

**Emitted flux** (Page & Thorne 1974). Write $x=\sqrt{r/M}$ and
$x_0=\sqrt{r_{\rm ISCO}/M}$. Let $x_{1,2,3}$ be the roots of $x^3-3x+2a=0$:

$$x_1 = 2\cos\left(\tfrac13\arccos a-\tfrac\pi3\right),\quad
x_2 = 2\cos\left(\tfrac13\arccos a+\tfrac\pi3\right),\quad
x_3=-2\cos\left(\tfrac13\arccos a\right).$$

Then

$$F(r)=\frac{3\dot M}{8\pi M^2}\,\frac{1}{x^4(x^3-3x+2a)}\Big[x-x_0-\tfrac32 a\ln\tfrac{x}{x_0}
-\sum_{k=1}^{3}\frac{3(x_k-a)^2}{x_k\prod_{j\ne k}(x_k-x_j)}\ln\frac{x-x_k}{x_0-x_k}\Big].$$

**Redshift.** For Keplerian circular orbits,

$$\Omega=\frac{M^{1/2}}{r^{3/2}+aM^{1/2}},\qquad
u^t=\frac{r^{3/2}+aM^{1/2}}{r^{3/4}\sqrt{r^{3/2}-3Mr^{1/2}+2aM^{1/2}}},\qquad
g=\frac{1}{u^t(1-\Omega\lambda)}.$$

The factor $g$ combines Doppler boosting and gravitational redshift in one expression,
so they should not be added separately.

**Observed intensity.** Bolometric: $I_{\rm obs}=g^4\,F(r_s)/\pi$. At a single
frequency, use $I_\nu=g^3B_\nu(T_{\rm em})$ with $T_{\rm em}=(F/\sigma)^{1/4}$ and
$\nu_{\rm em}=\nu/g$.

**Validation.** Reproduce Luminet (1979), check that the $a=0$ shadow edge sits at
$\sqrt{27}M$, and compare against the test problems in Gold et al. (2020).

**Codes:**

- `kgeo` (A. Chael, Python; used in Chael+2023): has this disk model built in,
  essentially.
- AART (Cárdenas-Avendaño, Lupsasca & Zhu 2023; JAX, fast).
- `geokerr` (Dexter & Agol 2009).

### Model B: Optically thin equatorial emission (recommended second model)

Use the same closed-form geodesics, but add emission at *every* equatorial crossing
$n=0,1,2,\dots$:

$$I_{\rm obs}(\alpha,\beta)=\sum_n \xi_n\, g^{3}\left(r_s^{(n)}\right) J\left(r_s^{(n)}\right),$$

- $J(r)$ is a parametrized profile, for example a power law or Johnson SU (Johnson+2020;
  Gralla, Holz & Wald 2019).
- $\xi_n$ is a geometric "fudge" factor of about 1–1.5 that approximates the path length
  through a thin layer.
- The emission can extend inside the ISCO with plunging geodesics, or use a
  sub-Keplerian/infall velocity mixture (Narayan+2021; Chael, Johnson & Lupsasca 2021).

This gives real nested photon subrings and the "inner shadow," which is a spin- and
inclination-sensitive feature. It is the appropriate regime for EHT, and `kgeo` and AART
already support it. The cost is the same as Model A.

### Model C: Semi-analytic thick flow (RIAF) with full radiative transfer

A 3D density, temperature, and field model (Broderick & Loeb 2006; Broderick+2016;
Pu+2016) is integrated with thermal synchrotron emission and absorption in `ipole`
(Mościbrodzka & Gammie 2018), RAPTOR, or GYOTO. Each image takes seconds to a minute.
This is a step up in realism (finite thickness, optical depth) without running any
simulations.

### Model D: GRMHD plus GRRT (KHARMA or iharm3d → `ipole`)

This is the EHT standard (EHT 2019 Paper V; Sgr A\* 2022 Paper V; Wong+2022 "Patoka"
library):

- Run MAD and/or SANE at a few spins, for example $\{-0.94,-0.5,0,0.5,0.94\}$.
- Post-process each snapshot at several inclinations, with electron temperatures from
  the $R_{\rm high}$ prescription (Mościbrodzka, Falcke & Shiokawa 2016).

Pros:

- Turbulent, time-variable structure.
- Snapshot-to-snapshot variance is a great robustness test.

Cons:

- 3D runs cost many GPU-hours. 2D runs with harm2d are cheap, but turbulence decays
  because of the anti-dynamo theorem.
- Spin becomes a *classification* problem over a few values.
- Images depend strongly on $R_{\rm high}$ and on MAD vs SANE, which are degenerate with
  spin.

KHARMA, pyharm, and harm2d are already available, so a small set of runs is feasible.
Use it as an **out-of-distribution test set** (train on A/B, test on D), not for
training.

### Model E: GR PIC (Aperture)

Not recommended for this project.

- GR PIC (Parfrey, Philippov & Cerutti 2019; Crinquand+2020; Galishnikova+2023) models
  collisionless magnetospheres and accretion with heavily compressed scale separation.
- There is no established pipeline from those runs to disk images, and each run is very
  expensive.
- At most, one image from an existing dump could serve as a qualitative "exotic" test
  case. Anything more is a research project of its own.

---

## 3. How to blur: what people actually do

### The physical picture

- An interferometer measures $V(u,v)=\int I(x,y)\,e^{-2\pi i(ux+vy)}\,dx\,dy$ only at
  sparse baselines (Thompson, Moran & Swenson 2017).
- The "dirty image" is the true image convolved with the dirty beam, which has strong
  sidelobes.
- Noise is thermal and Gaussian *in the visibilities*, so it is correlated in the image.
  On top of that come station gain and phase errors.
- The nominal resolution at 1.3 mm is $\lambda/D_{\rm Earth}\approx25\,\mu\mathrm{as}$.

### The convention in the literature

- To compare models with data, the EHT blurs model images with a **circular Gaussian of
  FWHM 20 μas** (EHT 2019 Papers IV and VI). That is $\approx5.3M$ for M87\* and
  $\approx4M$ for Sgr A\*.
- So the proposal's Gaussian choice *is* standard, but the width should be parametrized
  in units of $M$, not pixels.

### Sgr A\* scattering

- Diffractive interstellar scattering is an anisotropic Gaussian with FWHM
  $1.380\,(\lambda/\mathrm{cm})^2$ mas by $0.703\,(\lambda/\mathrm{cm})^2$ mas at PA
  $81.9^\circ$ (Johnson+2018; earlier $\lambda^2$ fits in Bower+2006). At 1.3 mm that is
  about $23\times12\,\mu\mathrm{as}$.
- Refractive substructure adds noise-like structure (Johnson & Gwinn 2015; Johnson
  2016; Psaltis+2018; Johnson+2018).

### Optical and X-ray (filled-aperture) PSFs

- Space-based telescopes have an Airy PSF.
- Ground-based seeing is closer to a Moffat profile (Moffat 1969).
- Noise is Poisson plus read noise, added *after* the blur.

### Recommended degradation tiers

| Tier | Kernel | Noise | Role |
|---|---|---|---|
| 1 | Gaussian, FWHM $\sim U[0.5,6]\,M$, optional ellipticity and PA | Gaussian or Poisson, added after blur, SNR range | Main experiment (the proposed one, in physical units) |
| 2 | Anisotropic Sgr A\* scattering kernel ± Moffat | same | Robustness to the kernel shape |
| 3 | `ehtim` (Chael+2016, 2018): observe with the EHT 2017 array, thermal noise and gains → dirty image or RML reconstruction | visibility-domain | "Realistic" test; good for the limitations section |

Also try passing the PSF FWHM as an extra input channel (non-blind restoration) and
compare with the blind case. That comparison is cheap and informative.

### Baselines

- Richardson–Lucy (Richardson 1972; Lucy 1974) and Wiener filtering via
  `skimage.restoration`.
- For Tier 3, CLEAN or RML in `ehtim`.

### ML precedents to cite

- Schawinski+2017 (GAN deblurring of galaxies).
- van der Gucht+2020 (CNN recovery of black hole parameters from GRMHD images).
- Medeiros+2023 PRIMO (learned dictionary from GRMHD, applied to the M87\* image).
- Sun & Bouman 2021 (Deep Probabilistic Imaging).

---

## 4. Recommended plan

1. **Training data:** Model A (exact Kerr ray tracing, Page–Thorne flux, $g^4$) *and*
   Model B (optically thin, $n\le2$), both from `kgeo` or AART. Sample
   $a\in[-0.99,0.99]$, $\cos i$ uniform, and a random PA, for about $10^4$ images or
   more.
2. **Degradation:** Tier 1 Gaussian in units of $M$ with SNR sweeps as the core. Use
   Tier 2 and Tier 3 as robustness tests.
3. **Out-of-distribution test:** a few GRMHD snapshots (KHARMA → `ipole`). The trained
   network sees them only at test time.
4. **Heads:** $(a,\cos i)$ plus $r_{\rm ISCO}$, with predicted uncertainties.

Skip GR PIC for this course project.

---

## References

Ray tracing, disk physics, and equatorial-emission models:

- Bardeen 1973, "Timelike and null geodesics in the Kerr metric," in *Black Holes (Les
  Astres Occlus)*, eds. C. DeWitt & B. S. DeWitt (Gordon & Breach), p. 215
- Bardeen, Press & Teukolsky 1972, ApJ 178, 347, doi:10.1086/151796
- Cunningham & Bardeen 1973, ApJ 183, 237, doi:10.1086/152223
- Novikov & Thorne 1973, in *Black Holes (Les Astres Occlus)*, eds. C. DeWitt &
  B. S. DeWitt (Gordon & Breach), p. 343
- Page & Thorne 1974, ApJ 191, 499, doi:10.1086/152990
- Luminet 1979, A&A 75, 228
- Gralla, Holz & Wald 2019, PRD 100, 024018, doi:10.1103/PhysRevD.100.024018
- Gralla & Lupsasca 2020, PRD 101, 044032, doi:10.1103/PhysRevD.101.044032
- Johnson et al. 2020, Sci. Adv. 6, eaaz1310, doi:10.1126/sciadv.aaz1310
- Chael, Johnson & Lupsasca 2021, ApJ 918, 6, doi:10.3847/1538-4357/ac09ee
- Narayan et al. 2021, ApJ 912, 35, doi:10.3847/1538-4357/abf117
- Cárdenas-Avendaño, Lupsasca & Zhu 2023, PRD 107, 043030,
  doi:10.1103/PhysRevD.107.043030 (AART)
- Chael et al. 2023, ApJ 958, 65, doi:10.3847/1538-4357/acf92d (uses `kgeo`)
- Johannsen & Psaltis 2010, ApJ 718, 446, doi:10.1088/0004-637X/718/1/446
- Kamruddin & Dexter 2013, MNRAS 434, 765, doi:10.1093/mnras/stt1068

Radiative transfer codes and semi-analytic flows:

- Dexter & Agol 2009, ApJ 696, 1616, doi:10.1088/0004-637X/696/2/1616 (`geokerr`)
- Vincent et al. 2011, CQG 28, 225011, doi:10.1088/0264-9381/28/22/225011 (GYOTO)
- Mościbrodzka & Gammie 2018, MNRAS 475, 43, doi:10.1093/mnras/stx3162 (`ipole`)
- Bronzwaer et al. 2018, A&A 613, A2, doi:10.1051/0004-6361/201732149 (RAPTOR)
- Gold et al. 2020, ApJ 897, 148, doi:10.3847/1538-4357/ab96c6
- Broderick & Loeb 2006, MNRAS 367, 905, doi:10.1111/j.1365-2966.2006.10152.x
- Broderick et al. 2016, ApJ 820, 137, doi:10.3847/0004-637X/820/2/137
- Pu et al. 2016, ApJ 831, 4, doi:10.3847/0004-637X/831/1/4

GRMHD and GR PIC:

- Prather et al. 2021, JOSS 6, 3336, doi:10.21105/joss.03336 (iharm3D)
- Mościbrodzka, Falcke & Shiokawa 2016, A&A 586, A38,
  doi:10.1051/0004-6361/201526630
- Wong et al. 2022, ApJS 259, 64, doi:10.3847/1538-4365/ac582e
- Parfrey, Philippov & Cerutti 2019, PRL 122, 035101,
  doi:10.1103/PhysRevLett.122.035101
- Crinquand et al. 2020, PRL 124, 145101, doi:10.1103/PhysRevLett.124.145101
- Galishnikova et al. 2023, PRL 130, 115201, doi:10.1103/PhysRevLett.130.115201

EHT results:

- EHT Collaboration 2019, ApJL 875, L4 (Paper IV, imaging), L5 (Paper V, physical
  origin), L6 (Paper VI, shadow and mass)
- EHT Collaboration 2022, ApJL 930, L14 (Sgr A\* Paper III, imaging), L15 (Paper IV,
  variability and morphology), L16 (Paper V, astrophysical models)

Interferometry, scattering, and PSFs:

- Thompson, Moran & Swenson 2017, *Interferometry and Synthesis in Radio Astronomy*,
  3rd ed. (Springer)
- Chael et al. 2016, ApJ 829, 11, doi:10.3847/0004-637X/829/1/11
- Chael et al. 2018, ApJ 857, 23, doi:10.3847/1538-4357/aab6a8
- Bower et al. 2006, ApJ 648, L127, doi:10.1086/508019
- Johnson & Gwinn 2015, ApJ 805, 180, doi:10.1088/0004-637X/805/2/180
- Johnson 2016, ApJ 833, 74, doi:10.3847/1538-4357/833/1/74
- Johnson et al. 2018, ApJ 865, 104, doi:10.3847/1538-4357/aadcff
- Psaltis et al. 2018, arXiv:1805.01242
- Moffat 1969, A&A 3, 455

Deconvolution and machine learning:

- Richardson 1972, JOSA 62, 55, doi:10.1364/JOSA.62.000055
- Lucy 1974, AJ 79, 745, doi:10.1086/111605
- Schawinski et al. 2017, MNRAS 467, L110, doi:10.1093/mnrasl/slx008
- van der Gucht et al. 2020, A&A 636, A94, doi:10.1051/0004-6361/201937014
- Sun & Bouman 2021, Proc. AAAI 35, 2628, doi:10.1609/aaai.v35i3.16366
- Medeiros et al. 2023, ApJL 947, L7, doi:10.3847/2041-8213/acc32d
