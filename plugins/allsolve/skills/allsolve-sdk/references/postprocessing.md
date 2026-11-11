# Allsolve post-processing

**Contents:** [Where to compute the FFT](#where-to-compute-the-fft) · [Right-hand Hanning window](#right-hand-hanning-window) · [Zero-padding](#zero-padding) · [Conventions](#conventions) · [Standard frequency-domain quantities](#standard-frequency-domain-quantities) · [KPI extraction](#kpi-extraction) · [In-simulation FFT (custom script section — solver-side only)](#in-simulation-fft-custom-script-section--solver-side-only) · [Plotting conventions](#plotting-conventions) · [Gotchas](#gotchas)

This reference covers turning Allsolve transient outputs into frequency-domain results: right-hand Hanning window, zero-padding, FFT, electrical impedance, Tx/Rx sensitivity, centre frequency and -6 dB fractional bandwidth. Use it only for time series from an Allsolve transient simulation (`get_output_data` or an in-solver FFT section), not for general FFT work or measured lab data.

It focuses on piezoelectric transducers. The techniques apply to any transient-to-frequency post-processing. For S-parameters, see [the RF domain skill](../../allsolve-domain-rf/SKILL.md). For general output handling, see [simulation.md](simulation.md#outputs).

## Where to compute the FFT

| Scenario | Method | Pros | Cons |
|---|---|---|---|
| One-off analysis / plotting | Local Python | Fast iteration, full matplotlib | Requires CSV download roundtrip |
| KPIs needed in sweep outputs | In-simulation (custom code section) | KPIs in output data, no roundtrip | More complex setup, harder to debug |
| Frequency-domain spectra in output data | In-simulation + CSV file write | Spectra downloadable via SDK | Large output for dense spectra |

Use local Python for exploratory work. Switch to in-simulation for production sweeps where KPIs drive parameter selection.

## Right-hand Hanning window

Apply to time-domain signals before FFT to suppress spectral leakage from incomplete ringdown. Preserves excitation onset, tapers the tail to zero.

```python
def apply_right_hanning(signal):
    n = len(signal)
    window = np.ones(n)
    n_taper = n - n // 2
    window[n // 2:] = 0.5 * (1 + np.cos(np.pi * np.arange(n_taper) / n_taper))
    return signal * window
```

**When to use:** Always for transient wavelet-driven simulations (piezocomposite, PMUT, pulse-echo). Not needed for CW harmonic analysis.

## Zero-padding

Standard: **20x zero-padding** (`n_pad = n * 20`). Interpolates FFT spectrum to finer frequency bins without adding new spectral information.

```python
n_pad = len(signal) * 20
freqs = np.fft.rfftfreq(n_pad, d=dt)
spectrum = np.fft.rfft(windowed_signal, n=n_pad)
```

20x is a good default for smooth spectral curves; 10x acceptable for coarse sweeps.

## Conventions

Tx here = average front-face pressure per volt (not TVR at 1 m). Bandwidth = −6 dB on the one-way Tx spectrum, as a fraction of fc (fc = spectral peak). Use the same window and n_pad on every signal in a ratio, so the gains cancel.

## Standard frequency-domain quantities

### Electrical impedance

```python
Z = V_fft / I_fft
Z_mag = np.abs(Z)
Z_phase = np.angle(Z, deg=True)
```

Limit KPIs to bins where |I_fft| > 1e-2 · its maximum; outside that band the ratio is noise. The 1e-2 is a starting value, to be tuned.

### Transmit sensitivity (Tx)

```python
tx = np.abs(P_fft / V_fft)  # Pa/V
```

Limit KPIs to bins where |V_fft| > 1e-2 · its maximum; outside that band the ratio is noise. The 1e-2 is a starting value, to be tuned.

Where `P_fft = FFT(pressure_on_front_face)`, `V_fft = FFT(drive_voltage)`.

### Receive sensitivity (Rx)

```python
rx = np.abs(V_oc_fft / P_inc_fft)  # V/Pa
```

Requires a receive simulation with incident pressure excitation and open-circuit voltage measurement.

## KPI extraction

### Centre frequency (fc)

Peak of the Tx sensitivity spectrum in the valid frequency range:

```python
band = np.abs(V_fft) > 1e-2 * np.abs(V_fft).max()
mask = (freqs > f_min) & (freqs < f_max) & band
tx_m = tx[mask]
f_m = freqs[mask]
idx = np.argmax(np.abs(tx_m))
max_tx = np.abs(tx_m[idx])
fc = f_m[idx]
```

### Fractional bandwidth (-6 dB)

```python
threshold = max_tx / 2.0  # -6 dB in linear
below = tx_m[:idx]
cl = np.where(below < threshold)[0]
f_lower = f_m[cl[-1]] if len(cl) > 0 else f_m[0]
above = tx_m[idx:]
ch = np.where(above < threshold)[0]
f_upper = f_m[idx + ch[0]] if len(ch) > 0 else f_m[-1]
fbw = (f_upper - f_lower) / fc
```

### Impedance at centre frequency

```python
z_idx = np.argmin(np.abs(freqs - fc))
Z_at_fc = Z_mag[z_idx]
```

## In-simulation FFT (custom script section — solver-side only)

Use `AFTER_FORMULATIONS_CREATED` with the `SOLVE` section disabled (see [simulation-scripts.md](simulation-scripts.md#injection-points)). The custom code creates the timestepper, runs the time loop with data capture, then computes FFT and outputs KPIs.

These calls use the **solver script API** (`import quanscient as qs`) — they run inside the cloud solver, not in local SDK code:

```python
qs.setoutputvalue("fc_Hz", fc)
qs.setoutputvalue("max_tx_sensitivity_PaV", max_tx)
qs.setoutputvalue("Z_mag_at_fc_Ohm", Z_at_fc)
qs.setoutputvalue("fractional_bandwidth", fbw)

# Array outputs: one call per array (the optional third argument is a step label, time or eigenmode index, not frequency)
qs.setoutputvalue("freq_Hz", f_out.tolist())
qs.setoutputvalue("Z_mag_spectrum", z_out.tolist())
qs.setoutputvalue("tx_sensitivity_spectrum", tx_out.tolist())
```

## Plotting conventions

- **Log y-axis** for all magnitude spectra (impedance, sensitivity, PSD)
- **x-axis floor** above DC to hide artefacts (e.g. 100 kHz for MHz-range devices)
- **Clip magnitudes** before log: `np.maximum(Z_mag, 1e-30)`
- **Mark KPIs on plots**: vertical lines for fc, f_lower, f_upper; horizontal line for -6 dB threshold
- **4-panel standard**: time signals | |Z| | Z phase | Tx sensitivity

## Gotchas

- **Band-limit ratios** — limit KPIs to bins where |V_fft| (or |I_fft|) > 1e-2 · its maximum; outside that band the ratio is noise. The 1e-2 is a starting value, to be tuned.
- **`qs.setoutputvalue(name, list)` for array outputs** — pass the whole array as a list. The optional third argument is a step label, time or eigenmode index, not frequency.
- **For harmonic analysis (FBAR), impedance comes directly** from the port V and I; no FFT is needed. See also [acoustics](../../allsolve-domain-acoustics/SKILL.md#impedance-from-a-harmonic-solve) (also for [symmetry models](../../allsolve-domain-acoustics/SKILL.md#symmetry-models)); template: `examples/pzt_disc_in_water`.
