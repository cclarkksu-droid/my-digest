"""
Journey Theme (provisional) — ~25s, tender & hopeful.

A light bamboo-flute (dizi) melody over warm strings, with soft plucked
guzheng movement, a gentle low caravan pulse, a faint chime on the pebble
moment, and a thin desert-wind bed tying it to the opening's world.
Shaped to the Scene 2 beats:
  0–5s  caravan arrives      strings fade in, pulse, first flute phrase
  5–10s greeting             warm swell, tender flute
  10–16s pebbles             sparse & intimate, a soft chime
  16–19s face glimpse        melody lifts warmly
  19–25s departure           theme opens up, hopeful, gently settles to wind

Key: D major pentatonic. Synthesized from scratch (no samples).
Run: python3 audio/make_journey_theme.py
"""
import os
import subprocess
import numpy as np
from scipy import signal

SR = 48000
DUR = 26.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(23)
OUT = os.path.dirname(os.path.abspath(__file__))


def sos_filter(x, kind, freq, order=4):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pan(mono, p):
    a = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(a), mono * np.sin(a)])


def place(buf, snd, at, gain=1.0):
    i = int(at * SR)
    L = snd.shape[-1]
    if i >= buf.shape[-1] or i + L <= 0:
        return
    j = min(buf.shape[-1], i + L)
    s = max(0, -i)
    buf[..., max(i, 0):j] += gain * snd[..., s:j - i]


def reverb(stereo, seconds=2.2, damp=5000, wet=0.28):
    n = int(seconds * SR)
    tt = np.arange(n) / SR
    out = np.empty_like(stereo)
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-tt * 6.0 / seconds)
        ir = sos_filter(ir, "lowpass", damp, 2)
        ir[: int(0.015 * SR)] *= np.linspace(0, 1, int(0.015 * SR))
        ir /= np.sqrt(np.sum(ir ** 2))
        out[c] = signal.fftconvolve(stereo[c], ir)[: stereo.shape[1]]
    return (1 - wet) * stereo + wet * out * 1.5


# ---------------------------------------------------------------- instruments
def flute(m, dur, amp=1.0):
    """Dizi-like bamboo flute: near-sine tone, eased-in vibrato, breath noise, chiff."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = midi(m)
    vib = 1 + 0.028 * np.sin(2 * np.pi * 5.6 * tt) * np.clip(tt / 0.35, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    tone = np.sin(ph) + 0.16 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph) + 0.02 * np.sin(4 * ph)
    breath = sos_filter(rng.standard_normal(n), "bandpass", [1500, 5000], 2)
    breath *= 0.05 + 0.10 * np.exp(-tt * 18)            # chiff at the attack
    env = np.clip(tt / 0.07, 0, 1) * np.clip((dur - tt) / 0.28, 0, 1)
    return (tone * 0.9 + breath) * env * amp


def strings(notes, dur, amp=1.0):
    """Warm sustained string pad from a stack of detuned, filtered saws."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for m in notes:
        f = midi(m)
        for det in (0.996, 1.0, 1.004):
            ph = 2 * np.pi * np.cumsum(np.full(n, f * det)) / SR + rng.uniform(0, 6)
            saw = np.zeros(n)
            for k in range(1, 14):
                saw += (1.0 / k) * np.sin(k * ph)
            x += saw
    x = sos_filter(x, "lowpass", 2600, 3)
    x += 0.3 * sos_filter(x, "lowpass", 1200, 2)
    shimmer = 1 + 0.04 * np.sin(2 * np.pi * 0.3 * tt)   # slow swell
    env = np.clip(tt / 0.8, 0, 1) * np.clip((dur - tt) / 1.0, 0, 1) * shimmer
    x = x / (len(notes) * 3) * env * amp
    return x


def pluck(m, dur=1.2, amp=1.0):
    """Guzheng-ish plucked string."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = midi(m)
    x = np.zeros(n)
    for k, w in [(1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15), (5, 0.08)]:
        x += w * np.sin(2 * np.pi * f * k * tt) * np.exp(-tt * (2.2 + 0.5 * k))
    x *= np.clip(tt / 0.003, 0, 1)
    return x * amp


def low_pulse(amp=1.0):
    """Soft muffled low thud — the caravan's gentle plod."""
    n = int(0.5 * SR)
    tt = np.arange(n) / SR
    f = midi(38) * (1 + 0.1 * np.exp(-tt * 25))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7)
    x = sos_filter(x, "lowpass", 300, 2)
    return x * amp


def bell(m, dur=3.0, amp=1.0):
    """Soft chime with slightly inharmonic partials — the pebble shimmer."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = midi(m)
    x = np.zeros(n)
    for r, w in [(1.0, 1.0), (2.01, 0.5), (3.01, 0.25), (4.2, 0.12), (5.43, 0.08)]:
        x += w * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * (1.1 + 0.25 * r))
    x *= np.clip(tt / 0.002, 0, 1)
    return x * amp


# ---------------------------------------------------------------- arrangement
melody = [  # (start, midi, dur, amp)
    (1.6, 62, 1.0, 0.9), (2.6, 64, 0.8, 0.9), (3.4, 66, 1.2, 1.0), (4.6, 69, 1.6, 1.0),
    (6.6, 66, 0.8, 0.85), (7.4, 64, 1.4, 0.85),
    (9.0, 69, 1.0, 0.95), (10.0, 71, 1.0, 0.95), (11.0, 69, 1.0, 0.9),
    (12.0, 66, 1.4, 0.9), (13.5, 64, 1.8, 0.85),
    (15.6, 62, 1.6, 0.8), (17.3, 66, 1.8, 0.85),                       # pebbles: sparse
    (19.2, 69, 1.0, 1.0), (20.2, 71, 1.0, 1.0), (21.2, 74, 1.7, 1.05),  # lift / soar
    (22.9, 71, 1.0, 0.95), (23.9, 69, 2.0, 0.9),                        # settle home
]

chords = [  # (start, dur, notes, amp) — warm pad
    (0.0, 4.2, [50, 62, 66, 69], 0.55),      # D
    (4.0, 4.2, [55, 59, 62, 67], 0.55),      # G
    (8.0, 3.2, [50, 62, 66, 69], 0.55),      # D
    (11.0, 2.8, [57, 61, 64, 69], 0.5),      # A  (tender)
    (13.6, 2.2, [55, 59, 62, 67], 0.5),      # G
    (15.6, 3.6, [50, 62, 66, 69], 0.6),      # D  (pebbles, warm)
    (19.0, 2.2, [55, 59, 62, 67], 0.6),      # G
    (21.0, 2.2, [57, 61, 64, 69], 0.6),      # A
    (23.0, 3.0, [50, 62, 66, 69], 0.65),     # D  (resolve)
]

plucks = [  # gentle movement during arrival & departure
    (2.0, 69), (2.5, 74), (3.0, 71), (5.0, 66), (5.5, 69),
    (19.5, 69), (20.0, 74), (20.5, 78), (21.5, 76), (22.0, 74), (23.5, 69),
]


def main():
    mel = np.zeros((2, N))
    for at, m, d, a in melody:
        place(mel, pan(flute(m, d, a), 0.0), at, 1.0)

    pad = np.zeros((2, N))
    for at, d, notes, a in chords:
        s = strings(notes, d, a)
        place(pad, np.stack([s, np.roll(s, 300)]), at, 1.0)

    plk = np.zeros((2, N))
    for at, m in plucks:
        place(plk, pan(pluck(m, 1.2, 0.5), rng.uniform(-0.4, 0.4)), at, 1.0)

    # caravan pulse: present at arrival & departure, softer in the intimate middle
    puls = np.zeros((2, N))
    at = 0.8
    while at < 25.5:
        lvl = 0.5 if (at < 9 or at > 18.5) else 0.22
        place(puls, pan(low_pulse(lvl), 0.0), at, 1.0)
        at += 1.0

    # pebble chime
    chime = np.zeros((2, N))
    place(chime, pan(bell(81, 3.5, 0.5), 0.2), 16.2, 1.0)
    place(chime, pan(bell(85, 3.0, 0.35), -0.2), 16.7, 1.0)

    # thin wind bed (ties to the opening world)
    gust = np.interp(t, np.linspace(0, DUR, 40), rng.uniform(0.3, 1.0, 40))
    gust = sos_filter(gust, "lowpass", 0.6, 2)
    wind = sos_filter(rng.standard_normal(N), "bandpass", [200, 1400], 2)
    wind = np.stack([wind * gust, np.roll(wind, 4000) * np.roll(gust, 6000)])
    wind *= np.interp(t, [0, 2, 23, 26], [0.5, 0.35, 0.35, 0.7]) * 0.04

    mix = reverb(mel, 2.4, 6000, 0.3) + reverb(pad, 3.0, 3500, 0.35) \
        + reverb(plk, 2.0, 7000, 0.25) + reverb(chime, 3.5, 8000, 0.45) \
        + puls * 0.9 + wind
    mix *= np.interp(t, [0, 1.2, 24.0, 26.0], [0, 1, 1, 0])[None, :]   # fade in/out
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    mix *= 10 ** (-3 / 20) / np.abs(mix).max()                        # peak ~ -3 dBFS

    wav = os.path.join(OUT, "journey_theme_provisional.wav")
    raw = (np.clip(mix.T, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2",
                    "-i", "-", "-c:a", "pcm_s16le", wav], input=raw, check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame",
                    "-b:a", "320k", os.path.splitext(wav)[0] + ".mp3"], check=True)
    print("done ->", wav)


if __name__ == "__main__":
    main()
