"""
6-second wind + blowing-sand bed for the dark cold-open, synthesized to match
the opening texture of desert_intro_60s.wav (high-altitude gusting wind,
whistling air, hissing sand, two travelling sand sweeps). No music.

The last ~1s is crossfaded into the main track by the build step, so the
scene can open on 5 seconds of pure darkness + wind before the picture fades in.

Run: python3 audio/make_wind_intro.py   (writes audio/wind_intro_6s.wav)
"""
import os
import subprocess
import numpy as np
from scipy import signal

SR = 48000
DUR = 6.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(11)
OUT = os.path.dirname(os.path.abspath(__file__))


def sos_filter(x, kind, freq, order=4):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def noise(n=N):
    return rng.standard_normal(n)


def smooth_random(rate_hz, lo, hi, n=N):
    k = int(DUR * rate_hz) + 6
    x = np.interp(np.arange(n) / SR, np.linspace(0, DUR, k), rng.uniform(0, 1, k))
    x = sos_filter(x, "lowpass", rate_hz, 2)
    x = (x - x.min()) / (x.max() - x.min() + 1e-9)
    return lo + (hi - lo) * x


def pan(mono, p):
    a = (np.asarray(p) + 1) * np.pi / 4
    return np.stack([mono * np.cos(a), mono * np.sin(a)])


def place(buf, snd, at, gain=1.0):
    i = int(at * SR)
    L = snd.shape[-1]
    if i >= buf.shape[-1] or i + L <= 0:
        return
    j = min(buf.shape[-1], i + L)
    s = max(0, -i)
    buf[..., max(i, 0):j] += gain * snd[..., s:j - i]


# ---- wind: low rumble + mid whoosh + high-altitude whistle ----
gustL = smooth_random(0.4, 0.3, 1.0)
gustR = np.roll(gustL, int(0.7 * SR)) * 0.6 + smooth_random(0.35, 0.2, 1.0) * 0.4
rumble = sos_filter(np.cumsum(noise()) * 0.02, "bandpass", [25, 180], 2)
rumble /= np.abs(rumble).max()
whoosh = sos_filter(noise(), "bandpass", [250, 1100], 2)
whoosh /= np.abs(whoosh).max()
whistle = np.zeros(N)
for fc in (620, 930, 1480):
    w = sos_filter(noise(), "bandpass", [fc * 0.985, fc * 1.015], 2)
    whistle += w / np.abs(w).max() * smooth_random(0.25, 0, 1) ** 3

# fade in from true silence, stay strong, hold into the crossfade at the end
level = np.interp(t, [0, 0.5, 2.0, 5.0, 6.0], [0.0, 0.7, 1.0, 1.0, 1.0])
L = level * gustL * (0.55 * rumble + 0.35 * whoosh + 0.45 * gustL * whistle)
R = level * gustR * (0.55 * np.roll(rumble, 3000) + 0.35 * np.roll(whoosh, 5000)
                     + 0.45 * gustR * np.roll(whistle, 7000))
wind = np.stack([L, R]) * 0.5

# ---- sand hiss + travelling sweeps ----
gust2 = smooth_random(0.5, 0.1, 1.0) ** 2
hissL = sos_filter(noise(), "highpass", 3500, 4)
hissR = sos_filter(noise(), "highpass", 3500, 4)
sand = np.stack([hissL * gust2, hissR * np.roll(gust2, int(0.4 * SR))]) * level * 0.10
for at, length, direction in [(0.6, 3.0, 1), (2.8, 3.0, -1), (4.2, 2.5, 1)]:
    n = int(length * SR)
    x = sos_filter(rng.standard_normal(n), "bandpass", [2500, 11000], 2)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    grains = sos_filter((rng.random(n) < 0.02).astype(float), "lowpass", 3000, 2) * 8
    p = np.linspace(-0.9, 0.9, n) * direction
    place(sand, pan(x * e * (0.6 + grains), p), at, 0.14)

mix = wind + sand
mix *= 10 ** (-3 / 20) / np.abs(mix).max()   # headroom; peak at -3 dBFS

wav = os.path.join(OUT, "wind_intro_6s.wav")
raw = (np.clip(mix.T, -1, 1) * 32767).astype("<i2").tobytes()
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2",
                "-i", "-", "-c:a", "pcm_s16le", wav], input=raw, check=True)
print("wrote", wav)
