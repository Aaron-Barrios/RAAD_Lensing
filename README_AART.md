# Generating GLM Black-Hole Images with AART

This document explains, end to end, how a single image of an optically thin, equatorial emission
model around a Kerr black hole (the Gralla–Lupsasca–Marrone, "GLM", model) is produced with
[AART](https://github.com/iAART/aart) (Cárdenas-Avendaño, Lupsasca & Zhu 2023, PRD 107, 043030).
These images are the clean training targets for our restoration network; the degradation step is
described separately in `EHT_Sampling.tex`.

Derivations of every formula below are in `Emission_and_Raytracing.tex`; section numbers refer to
that document. Units are $G = c = M = 1$ unless stated otherwise.

---

## 1. Setup

```bash
# from the RAAD_Lensing repository root
source .venv/bin/activate          # Python 3.10, numpy 2.2, scipy 1.15 (AART needs scipy >= 1.14)
cd aart
# edit params.py, then:
python lensingbands.py             # step 1: image-plane grids and lensing bands
python raytracing.py               # step 2: source radius and redshift sign per pixel
python radialintensity.py          # steps 3-4: redshift factor and band intensities
```

`.venv/` and `aart/` are git-ignored. The venv was built from `aart/requirements.txt`
(plus `ipykernel` for notebooks).

All AART modules read their parameters from `params.py` (`from params import *`), so a run is
configured by editing that file. Results are written as HDF5 files to `aart/Results/`.

---

## 2. Overview

For each pixel $(\alpha,\beta)$ on the observer's screen and each image order $n = 0, 1, 2$:

1. **Lensing bands.** Decide whether the $n$-th image exists at that pixel.
2. **Ray tracing.** Trace the light ray backward to its $n$-th crossing of the equatorial plane,
   at radius $r_s^{(n)}(\alpha,\beta)$.
3. **Redshift.** Compute the redshift factor $g$ between the gas at $r_s^{(n)}$ and the observer.
4. **Intensity.** Assign the brightness $g^p\,J(r_s^{(n)})$.
5. **Combine.** Sum the image orders, weighting $n \ge 1$ by the fudge factor $f$.
6. **Physical units.** Convert from $M$ to microarcseconds.

---

## 3. Inputs (`params.py`)

| Symbol | `params.py` | Meaning | GLM / our default |
|---|---|---|---|
| $a$ | `spin_case` | Black-hole spin | varied, $[0, 0.99]$ |
| $\theta_o$ | `i_case` | Observer inclination (degrees) | varied |
| $(\gamma, \mu, \sigma)$ | `gammap`, `mup`, `sigmap` | Emission-profile parameters | $(-3/2,\ r_-,\ 1/2)$ (GLM profile 1) |
| $f$ | `fudge` | Weight on $n \ge 1$ images | $1.5$ |
| $p$ | `gfactor` | Power of $g$ (§7) | **3** (AART default; 230 GHz, flat spectrum). GLM used 4 (bolometric) |
| $\xi, \beta_r, \beta_\phi$ | `sub_kep`, `betar`, `betaphi` | Velocity-model parameters (§6) | all $1$ (= GLM) |
| $L$ | `limits` | Half-width of the image, in $M$ | e.g. 15 |
| $\Delta x_n$ | `dx0`, `dx1`, `dx2` | Pixel size of each band's grid, in $M$ | e.g. 0.1 |
| $D_{\rm obs}$ | `D_obs` | Observer distance in $M$ (ray-tracing boundary) | $10^5$ |
| $\psi$, $D$ | `psi`, `dBH` | Mass scale and distance (physical units, §9) | M87\* by default |
| | `p_image` | 1 = all bands share one grid, so they can be summed | 1 |

---

## 4. Step 1: Image-plane grid and lensing bands (`lensingbands.py`)

**Grid.** Each band $n$ gets a Cartesian grid on the screen,
$\alpha, \beta \in [-L, L]$, with $N_n = 2L/\Delta x_n$ points per side.

**Critical curve.** The boundary of the black-hole "shadow" is traced by photons on bound spherical
orbits of radius $\tilde r \in [\tilde r_-, \tilde r_+]$:

$$
\tilde r_\pm = 2\left[1 + \cos\left(\tfrac23\arccos(\pm a)\right)\right],
$$

$$
\lambda(\tilde r) = a + \frac{\tilde r}{a}\left[\tilde r - \frac{2\Delta(\tilde r)}{\tilde r - 1}\right],
\qquad
\eta(\tilde r) = \frac{\tilde r^3}{a^2}\left[\frac{4\Delta(\tilde r)}{(\tilde r - 1)^2} - \tilde r\right],
$$

mapped to the screen by $\alpha = -\lambda/\sin\theta_o$ and
$\beta = \pm\sqrt{\eta + a^2\cos^2\theta_o - \lambda^2\cot^2\theta_o}$, keeping only $\tilde r$ where
$\beta$ is real.

**Band edges.** The $n$-th image exists at a pixel only if the ray reaches its $n$-th equatorial
crossing before falling into the horizon or escaping back to infinity, i.e.
$G_\theta^{m} \le I_r^{\rm total}$ (§6–8 below). For each point on the critical curve, AART
scales the screen position by a factor $s$ and root-finds the values of $s$ where

$$
G_\theta^{m}(s\alpha, s\beta) = I_r^{\rm total}(s\alpha, s\beta),
$$

one just inside ($s < 1$) and one just outside ($s > 1$) the curve. These points outline the inner
and outer edges of band $n$. A pixel belongs to band $n$ if it lies between them. For $n = 0$ the
inner edge is the *inner shadow* (rays that reach the horizon before crossing the equator even
once) and the outer edge is the image boundary.

The $n = 1$ and $n = 2$ bands are thin annuli around the critical curve. Their widths shrink by
roughly $e^{-\gamma_L}$ with each order, where $\gamma_L \approx \pi$ is the Lyapunov exponent of
the bound orbits. This is why AART allows each band its own resolution.

---

## 5. Step 2: Ray tracing to the equator (`raytracing.py`)

For every pixel inside band $n$:

**Conserved quantities** (§5):

$$
\lambda = -\alpha\sin\theta_o, \qquad \eta = (\alpha^2 - a^2)\cos^2\theta_o + \beta^2.
$$

**Polar motion** (§6). With $\Delta_\theta = \tfrac12\left(1 - (\eta + \lambda^2)/a^2\right)$ and
$u_\pm = \Delta_\theta \pm \sqrt{\Delta_\theta^2 + \eta/a^2}$, the Mino time from the observer to the
equator after $m$ polar turning points is

$$
G_\theta^{m} = \frac{1}{a\sqrt{-u_-}}\left[2m\,K\left(\tfrac{u_+}{u_-}\right) - \operatorname{sign}(\beta)\,F\left(\arcsin\tfrac{\cos\theta_o}{\sqrt{u_+}}\,\middle|\,\tfrac{u_+}{u_-}\right)\right],
\qquad m = n + H(\beta).
$$

The relation $m = n + H(\beta)$ (Heaviside $H$) converts image order to turning points: rays with
$\beta > 0$ must turn around in $\theta$ before reaching the equator.

**Radial roots** (§7.1). The quartic $\mathcal R(r) = (r^2 + a^2 - a\lambda)^2 - \Delta(r)[\eta + (\lambda - a)^2]$
has roots $r_1 \le r_2 \le r_3 \le r_4$ (when real), computed in closed form from the resolvent
cubic.

**Source radius** (§7.2). Setting the radial Mino time equal to $G_\theta^m$ and inverting:

- *$r_4$ real* (rays outside the critical curve, and some inside):

$$
r_s = \frac{r_4 r_{31} - r_3 r_{41}\,\operatorname{sn}^2(X_2\,|\,k)}{r_{31} - r_{41}\,\operatorname{sn}^2(X_2\,|\,k)},
\quad
X_2 = \tfrac12\sqrt{r_{31}r_{42}}\,G_\theta^m - F\left(\arcsin\sqrt{\tfrac{(D_{\rm obs} - r_4)\,r_{31}}{(D_{\rm obs} - r_3)\,r_{41}}}\,\middle|\,k\right),
\quad k = \frac{r_{32}r_{41}}{r_{31}r_{42}}.
$$

- *$r_3 = \bar r_4$ complex* (rays inside the critical curve that fall into the hole):

$$
r_s = \frac{(Br_2 - Ar_1) + (Br_2 + Ar_1)\operatorname{cn}(X_3\,|\,k_3)}{(B - A) + (B + A)\operatorname{cn}(X_3\,|\,k_3)},
\quad
A = \sqrt{r_{32}r_{42}},\; B = \sqrt{r_{31}r_{41}},\; k_3 = \frac{(A+B)^2 - r_{21}^2}{4AB},
$$

with $X_3 = \sqrt{AB}\,G_\theta^m - F(\cdot\,|\,k_3)$ evaluated at the observer.

AART evaluates the starting term at the finite observer distance $D_{\rm obs}$; as
$D_{\rm obs} \to \infty$ these reduce exactly to the formulas in §7. Pixels with
$r_s \le r_+ = 1 + \sqrt{1 - a^2}$ are discarded.

**Radial direction of the photon at emission** (§9). For $r_4$ real, half the total Mino time is
$\tfrac12 I_r^{\rm total} = \frac{2}{\sqrt{r_{31}r_{42}}}F\left(\arcsin\sqrt{r_{31}/r_{41}}\,\middle|\,k\right)$:

$$
\pm_r = \begin{cases} +1, & G_\theta^m \le \tfrac12 I_r^{\rm total} \quad\text{(photon outgoing at emission)}, \\ -1, & \text{otherwise (ingoing, before its radial turning point)}, \end{cases}
$$

and $\pm_r = +1$ for complex roots.

Output per band: `rs{n}` ($r_s^{(n)}$), `sign{n}` ($\pm_r$), plus time delays `t{n}` and azimuths
`phi{n}` (used only for time-dependent sources).

---

## 6. Step 3: Gas velocity and redshift (`intensity_f.py`)

**ISCO** (§3.1):

$$
Z_1 = 1 + (1 - a^2)^{1/3}\left[(1+a)^{1/3} + (1-a)^{1/3}\right],\quad Z_2 = \sqrt{3a^2 + Z_1^2},\quad
r_{\rm ISCO} = 3 + Z_2 - \sqrt{(3 - Z_1)(3 + Z_1 + 2Z_2)}.
$$

**General velocity model.** AART interpolates between a (sub-)Keplerian flow and radial free fall.
With $\Pi = (r^2 + a^2)^2 - a^2\Delta$:

$$
\hat\ell = \xi\,\frac{r^2 + a^2 - 2a\sqrt r}{\sqrt r\,(r - 2) + a}, \qquad
\hat\Omega = \frac{a + (1 - 2/r)(\hat\ell - a)}{\Pi/r^2 - 2a\hat\ell/r},
$$

$$
\bar\Omega = \frac{2ar}{\Pi}, \qquad \bar u^r = -\frac{\sqrt{2r(r^2 + a^2)}}{r^2},
$$

$$
\Omega = \hat\Omega + (1 - \beta_\phi)(\bar\Omega - \hat\Omega), \qquad
u^r = \hat u^r + (1 - \beta_r)(\bar u^r - \hat u^r),
$$

where $\hat u^r = 0$ outside the ISCO. Inside the ISCO, $\hat u^r$ is the infall velocity of gas
carrying the ISCO's energy and angular momentum, and $\hat\ell, \hat\Omega$ use $\hat\ell(r_{\rm ISCO})$.
The time component follows from $u\cdot u = -1$:

$$
u^t = \sqrt{\frac{1 + (u^r)^2 r^2/\Delta}{1 - (r^2 + a^2)\Omega^2 - \frac{2}{r}(1 - a\Omega)^2}}, \qquad u^\phi = \Omega\,u^t.
$$

**GLM limit.** With $\xi = \beta_r = \beta_\phi = 1$ (our setting) this is exactly GLM: circular
Keplerian orbits $\Omega = 1/(r^{3/2} + a)$ outside the ISCO, and Cunningham plunging inside it, with
$u^r = -\sqrt{2/(3r_{\rm ISCO})}\,(r_{\rm ISCO}/r - 1)^{3/2}$.

**Redshift factor** (§9). With the photon normalized to $p_t = -1$, $p_\phi = \lambda$,
$p_r = \pm_r\sqrt{\mathcal R(r_s)}/\Delta(r_s)$:

$$
g = \frac{\nu_{\rm obs}}{\nu_{\rm em}} = \frac{1}{-p_\mu u^\mu}
= \frac{1}{u^t - \lambda\,u^\phi - \pm_r\,\dfrac{\sqrt{\mathcal R(r_s)}}{\Delta(r_s)}\,u^r}.
$$

This single factor includes Doppler boosting, transverse Doppler and gravitational redshift.
Outside the ISCO ($u^r = 0$) it reduces to
$g = \sqrt{r^3 - 3r^2 + 2ar^{3/2}}\,/\,(r^{3/2} + a - \lambda)$.

---

## 7. Step 4: Emission and band intensities (`radialintensity.py`)

**Emission profile** (§4), Johnson's $S_U$ form:

$$
J(r) = \frac{\exp\left\{-\tfrac12\left[\gamma + \operatorname{arcsinh}\left(\frac{r - \mu}{\sigma}\right)\right]^2\right\}}{\sqrt{(r - \mu)^2 + \sigma^2}}.
$$

**Band intensity.** Because the source is optically thin, each crossing contributes
independently, and $I_\nu/\nu^3$ is conserved along the ray:

$$
I_n(\alpha,\beta) = \begin{cases} g^p\!\left(r_s^{(n)}\right) J\!\left(r_s^{(n)}\right), & (\alpha,\beta) \in \text{band } n,\ r_s^{(n)} > r_+, \\ 0, & \text{otherwise}, \end{cases}
$$

**Choice of $p$.** Light emitted at frequency $\nu/g$ is observed at $\nu$, and invariance of
$I_\nu/\nu^3$ gives

$$
I_\nu^{\rm obs}(\nu) = g^3\, I_\nu^{\rm em}(\nu/g).
$$

For an emission spectrum $I_\nu^{\rm em} \propto \nu^{-\alpha_\nu}$ this is
$I_\nu^{\rm obs} = g^{3+\alpha_\nu} I_\nu^{\rm em}(\nu)$, so $p = 3 + \alpha_\nu$. Integrating over
frequency instead ($d\nu_{\rm obs} = g\,d\nu_{\rm em}$) gives the bolometric result $p = 4$, which
is what GLM used.

**We use $p = 3$.** Our images represent EHT observations at a single frequency (230 GHz), where the
spectra of Sgr A\* and M87\* are close to flat ($\alpha_\nu \approx 0$). A larger $p$ would
strengthen the Doppler asymmetry (the brightness contrast scales as $(g_{\max}/g_{\min})^p$) and
further dim the strongly redshifted inner region; GLM note that the difference between $p = 3$ and
$p = 4$ is small and largely degenerate with the emission-profile parameters.

Output: `bghts0`, `bghts1`, `bghts2` in `Intensity_a_{a}_i_{i}.h5`, each $N \times N$.

---

## 8. Step 5: Combining image orders

AART stores the orders separately. The GLM image is

$$
I_{\rm obs}(\alpha,\beta) = I_0(\alpha,\beta) + f\left[I_1(\alpha,\beta) + I_2(\alpha,\beta)\right],
$$

which requires `p_image = 1` and `dx0 = dx1 = dx2` so the three arrays share one grid. Orders
$n \ge 3$ are omitted; each contributes $\sim e^{-\pi}$ of the previous one and is far below EHT
resolution.

Array layout: `bghts{n}[j, i]` is the pixel at $\beta_j$ (row), $\alpha_i$ (column), with both
axes running from $-L$ to $+L$. Display with `imshow(..., origin="lower", extent=[-L, L, -L, L])`.

```python
import h5py, numpy as np
with h5py.File("Results/Intensity_a_0.94_i_17.h5") as h:
    I0, I1, I2 = (np.nan_to_num(h[k][:]) for k in ("bghts0", "bghts1", "bghts2"))
image = I0 + fudge * (I1 + I2)
```

---

## 9. Step 6: Physical units

The image is computed in units of $M$. On the sky, one $M$ subtends the angular gravitational radius

$$
\theta_g = \frac{GM}{c^2 D},
$$

so a pixel of size $\Delta x$ (in $M$) is $\Delta x\,\theta_g$ in radians, and the field of view
is $2L\,\theta_g$. AART sets $M = 6.2\times10^9\,\psi\,M_\odot$ and $D$ = `dBH` (M87\* by default),
and prints the field of view in µas. For reference:

| Source | $\theta_g$ | $L = 15\,M$ field of view | $\Delta x = 0.1\,M$ pixel |
|---|---|---|---|
| M87\* | ≈ 3.8 μas | ≈ 114 μas | ≈ 0.38 μas |
| Sgr A\* | ≈ 4.8 μas | ≈ 144 μas | ≈ 0.48 μas |

This conversion is what links the ray-traced image to the EHT sampling in `EHT_Sampling.tex`.

---

## 10. Test run

Configuration: $a = 0.94$, $\theta_o = 17^\circ$ (GLM's best-fit values), profile 1, $f = 1.5$,
$p = 3$, $L = 15$, $\Delta x = 0.1$ (300 × 300 pixels per band). Run in the project venv:

| Step | Time |
|---|---|
| `lensingbands.py` | 32 s (root-finding of the band edges) |
| `raytracing.py` | 2 s (270,000 rays) |
| `radialintensity.py` | 1 s |

Flux fractions of the combined image: $n = 0$: 87.0%, $n = 1$: 12.2%, $n = 2$: 0.8%. The photon
ring lies at radius $\approx 5\,M$, and the approaching (left) side is brighter, as expected. At
$\Delta x = 0.1\,M$ the $n = 2$ ring is under-resolved; that is acceptable for EHT-resolution
training data but not for photon-ring science.

---

## 11. Notes for building the training set

- **Keep `gfactor = 3`** (the AART default) for 230 GHz images; see §7. If the network should not
  depend on this choice, $p$ can instead be drawn from $[3, 4]$ as a nuisance parameter.
- **Keep $\xi = \beta_r = \beta_\phi = 1$** unless the flow model is meant to be another nuisance
  parameter.
- **Lensing bands dominate the cost.** They depend only on $(a, \theta_o)$, not on the emission
  profile, so they can be computed once per $(a, \theta_o)$ and reused for many profiles and
  fudge factors.
- **Parameters are global.** Every module reads `params.py` at import time. Looping over
  1,500 $(a, \theta_o)$ values needs either `ChangeParams.py` plus re-running the scripts, the
  `aart` pip package, or a small wrapper that calls `lb()`, `calculate_observables()` and
  `bright_radial()` directly.
- **Normalize** each image (e.g. to unit total flux) before degradation, since the profile's
  overall scale is arbitrary.
- **Validation.** The tests in §12 of `Emission_and_Raytracing.tex` (Schwarzschild limit, critical
  curve, face-on symmetry, Doppler asymmetry, continuity at the ISCO) apply directly to these
  outputs.

---

## AI Acknowledgments

This document was prepared with the assistance of Claude (Anthropic), used through Claude Code.
The author directed the scope, content, and modeling choices. Claude read the AART source code,
wrote the mathematical description from it and from `Emission_and_Raytracing.tex`, and set up and
ran the software environment used for the test run. The author is responsible for the final content.
