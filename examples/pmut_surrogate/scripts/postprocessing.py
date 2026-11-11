"""Custom afterAll script for PMUT transient simulation."""

import numpy as np

timestepper = qs.genalpha(form, qs.vec(form), qs.vec(form))
timestepper.settolerance(1e-05)
timestepper.setrelaxationfactor(-1)
qs.settime(var.start_time)

nt = int(np.ceil(var.end_time / var.time_step)) + 1
V = np.zeros((nt,))
I = np.zeros((nt,))
Pav = np.zeros((nt,))
Vav = np.zeros((nt,))

while qs.gettime() < var.end_time:
    timestepper.allnext(
        relrestol=1e-06,
        maxnumit=1000,
        timestep=var.time_step,
        maxnumnlit=1000,
    )

    # Value output: V
    var.discrete = qs.evaluate(port.lump.V)
    V[timestepper.count()] = var.discrete[0]

    # Value output: I
    var.discrete = qs.evaluate(qs.dt(port.lump.Q))
    I[timestepper.count()] = var.discrete[0]

    # Value output: Pav
    var.discrete = qs.allaverage(reg.front_face, fld.p, 2)
    Pav[timestepper.count()] = var.discrete

    # Value output: Vav
    var.discrete = qs.allaverage(reg.front_face, qs.dt(qs.compz(fld.u)), 2)
    Vav[timestepper.count()] = var.discrete

    var.step_index += 1


def hanning_window(nt):
    window = np.hanning(nt * 2)
    return window[nt:]


def compute_fwhm(freq, tx_sensitivity):
    max_sens = np.max(tx_sensitivity)
    half = max_sens / 2
    inds = np.where(tx_sensitivity >= half)[0]
    if inds.size > 1:
        bw = freq[inds[-1]] - freq[inds[0]]
    else:
        bw = 0.0
    return bw


win = hanning_window(nt)

V_spect = np.fft.fft(V * win, int(nt * expr.npad))
I_spect = np.fft.fft(I * win, int(nt * expr.npad))
Pav_spect = np.fft.fft(Pav * win, int(nt * expr.npad))
Vav_spect = np.fft.fft(Vav * win, int(nt * expr.npad))

freq = np.linspace(0, 1 / var.time_step, int(nt * expr.npad))

# Impedance and transmit sensitivity
Z_spect = V_spect / I_spect
Tx_spect = Pav_spect / V_spect

# Truncate to fmax
idx = (np.abs(freq - expr.fmax)).argmin()
freq = freq[:idx]
Z_spect = Z_spect[:idx]
Tx_spect = Tx_spect[:idx]

tx_max = np.max(np.abs(Tx_spect))
fc = freq[np.argmax(np.abs(Tx_spect))]
zfc = np.abs(Z_spect)[np.argmax(np.abs(Tx_spect))]
bw = compute_fwhm(freq, np.abs(Tx_spect))
fbw = 100.0 * bw / fc

qs.setoutputvalue("tx_max", tx_max)
qs.setoutputvalue("fc", fc)
qs.setoutputvalue("zfc", zfc)
qs.setoutputvalue("fbw", fbw)

qs.setoutputvalue("freq", freq.tolist())
qs.setoutputvalue("Zmag", np.abs(Z_spect).tolist())
qs.setoutputvalue("Zphase", np.angle(Z_spect, deg=True).tolist())
qs.setoutputvalue("Txmag", np.abs(Tx_spect).tolist())
qs.setoutputvalue("Txphase", np.angle(Tx_spect, deg=True).tolist())
