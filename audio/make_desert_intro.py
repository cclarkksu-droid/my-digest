"""
Desert Intro — 60-second epic cinematic cue, synthesized from scratch.

Timeline
  0–8s   High altitude: gusting wind, whistling air, distant sand hiss, low organ drone appears.
  8–40s  Camera descends: marching boots and horse hooves grow louder and brighter;
         organ + brass build through a D-minor progression whose chords change faster and faster;
         an accelerating clock tick and a rising "endless" tone push the tension.
  40s    CRESCENDO — the general raises his hand: full organ + brass hit, sub boom,
         one unison stamp of boots, then the army is silent.
  40–52s Music holds, then fades to near-silence.
  52–60s Only gusting wind, hissing sand, a horse snort, a faint low drone.

Run:  python3 audio/make_desert_intro.py   (needs numpy + scipy; matplotlib for the timeline image)
"""
import os
import subprocess
import numpy as np
from scipy import signal

SR = 48000
DUR = 60.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
OUT = os.path.dirname(os.path.abspath(__file__))
HIT = 40.0


# ---------------------------------------------------------------- helpers
def env(points):
    """Piecewise-linear envelope from [(time, value), ...]."""
    ts, vs = zip(*points)
    return np.interp(t, ts, vs)


def sos_filter(x, kind, freq, order=4):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def noise(n=N):
    return rng.standard_normal(n)


def smooth_random(rate_hz, lo, hi, n=N):
    """Slowly wandering random curve between lo and hi."""
    k = int(DUR * rate_hz) + 4
    pts = rng.uniform(0, 1, k)
    x = np.interp(np.arange(n) / SR, np.linspace(0, DUR, k), pts)
    x = sos_filter(x, "lowpass", rate_hz, 2)
    x = (x - x.min()) / (x.max() - x.min() + 1e-9)
    return lo + (hi - lo) * x


def pan(mono, p):
    """p = -1 (left) .. +1 (right); p may be an array."""
    a = (np.asarray(p) + 1) * np.pi / 4
    return np.stack([mono * np.cos(a), mono * np.sin(a)])


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, snd, at, gain=1.0):
    i = int(at * SR)
    L = snd.shape[-1]
    if i >= buf.shape[-1] or i + L <= 0:
        return
    j = min(buf.shape[-1], i + L)
    s = max(0, -i)
    buf[..., max(i, 0):j] += gain * snd[..., s:j - i]


def reverb(stereo, seconds, damp_hz, wet):
    n = int(seconds * SR)
    tt = np.arange(n) / SR
    out = np.empty_like(stereo)
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-tt * 6.9 / seconds)
        ir = sos_filter(ir, "lowpass", damp_hz, 2)
        ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))  # pre-delay softening
        ir /= np.sqrt(np.sum(ir ** 2))
        out[c] = signal.fftconvolve(stereo[c], ir)[: stereo.shape[1]]
    return (1 - wet) * stereo + wet * out * 1.6


# ---------------------------------------------------------------- 1. WIND
def make_wind():
    gustL = smooth_random(0.35, 0.25, 1.0)
    gustR = np.roll(gustL, int(0.7 * SR)) * 0.6 + smooth_random(0.3, 0.2, 1.0) * 0.4
    rumble = sos_filter(np.cumsum(noise()) * 0.02, "bandpass", [25, 180], 2)
    rumble /= np.abs(rumble).max()
    whoosh = sos_filter(noise(), "bandpass", [250, 1100], 2)
    whoosh /= np.abs(whoosh).max()
    whistle = np.zeros(N)
    for fc in (620, 930, 1480):
        w = sos_filter(noise(), "bandpass", [fc * 0.985, fc * 1.015], 2)
        whistle += w / np.abs(w).max() * smooth_random(0.25, 0, 1) ** 3
    level = env([(0, 0.0), (1.5, 0.95), (8, 0.9), (20, 0.55), (36, 0.4),
                 (40, 0.3), (43, 0.55), (48, 0.9), (60, 0.95)])
    alt = env([(0, 1), (10, 1), (30, 0.2), (60, 0.25)])  # whistling only up high
    L = level * gustL * (0.55 * rumble + 0.35 * whoosh + 0.4 * alt * gustL * whistle)
    R = level * gustR * (0.55 * np.roll(rumble, 3000) + 0.35 * np.roll(whoosh, 5000)
                         + 0.4 * alt * gustR * np.roll(whistle, 7000))
    return np.stack([L, R]) * 0.5


# ---------------------------------------------------------------- 2. SAND HISS
def make_sand():
    gust = smooth_random(0.45, 0.1, 1.0) ** 2
    hissL = sos_filter(noise(), "highpass", 3500, 4)
    hissR = sos_filter(noise(), "highpass", 3500, 4)
    level = env([(0, 0.15), (10, 0.25), (30, 0.4), (38, 0.3), (42, 0.5), (50, 0.9), (60, 0.9)])
    out = np.stack([hissL * gust, hissR * np.roll(gust, int(0.4 * SR))]) * level * 0.09
    # sweeping gusts of sand that travel across the stereo field
    for at, length, direction in [(4, 3.5, 1), (17, 3, -1), (29, 2.5, 1), (44, 4, -1),
                                  (49.5, 3.5, 1), (54, 4.5, -1)]:
        n = int(length * SR)
        x = sos_filter(rng.standard_normal(n), "bandpass", [2500, 11000], 2)
        e = np.sin(np.linspace(0, np.pi, n)) ** 2
        grains = sos_filter((rng.random(n) < 0.02).astype(float), "lowpass", 3000, 2) * 8
        p = np.linspace(-0.9, 0.9, n) * direction
        g = 0.12 if at < 40 else 0.2
        place(out, pan(x * e * (0.6 + grains), p), at, g)
    return out


# ---------------------------------------------------------------- 3. ORGAN
ORGAN_STOPS = [(0.5, 0.55), (1, 1.0), (2, 0.6), (3, 0.28), (4, 0.32), (6, 0.12), (8, 0.14)]


def organ_note(f, dur, att, rel, bright):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for detune in (1.0, 1.0016):
        for h, w in ORGAN_STOPS:
            fh = f * h * detune
            if fh > 9000:
                continue
            ww = w * (bright if h >= 3 else 1.0)
            x += ww * np.sin(2 * np.pi * fh * tt + rng.uniform(0, 6.28))
    e = np.minimum(1, tt / att) * np.minimum(1, (dur - tt) / rel)
    trem = 1 + 0.025 * np.sin(2 * np.pi * 5.2 * tt)
    return x * np.clip(e, 0, 1) * trem


PROGRESSION = [  # (start, end, midi notes, brightness) — chord changes speed up
    (3.0, 16.0, [26, 38, 45], 0.25),                # D drone
    (15.5, 24.0, [26, 38, 45, 50, 53], 0.45),       # D minor
    (23.6, 30.0, [34, 46, 50, 53, 58], 0.6),        # B-flat
    (29.7, 34.0, [31, 43, 50, 55, 58], 0.75),       # G minor
    (33.8, 37.0, [36, 48, 52, 55, 60], 0.9),        # C
    (36.85, 38.5, [33, 45, 52, 57, 62], 1.0),       # A sus4
    (38.4, 40.05, [33, 45, 52, 57, 61, 64], 1.1),   # A major — pulls hard toward D
    (HIT, 53.0, [26, 38, 45, 50, 53, 57, 62, 65, 69], 1.25),  # D minor HIT
]


def make_organ():
    out = np.zeros((2, N))
    for start, end, notes, bright in PROGRESSION:
        is_hit = start == HIT
        att = 0.03 if is_hit else min(2.5, (end - start) * 0.3)
        rel = 0.4 if not is_hit else 1.0
        for k, m in enumerate(notes):
            x = organ_note(midi(m), end - start, att, rel, bright)
            p = np.linspace(-0.5, 0.5, len(notes))[k] if len(notes) > 1 else 0
            place(out, pan(x, p), start, 1.0 / np.sqrt(len(notes)))
    level = env([(0, 0), (3, 0.0), (9, 0.18), (20, 0.35), (32, 0.6), (39.9, 0.95),
                 (40, 1.15), (44.5, 1.0), (49, 0.25), (53, 0.05), (60, 0.04)])
    out *= level
    # faint low D that lingers under the wind after the fade
    tail = organ_note(midi(38), 12, 3, 4, 0.2) + organ_note(midi(26), 12, 3, 4, 0.2)
    place(out, pan(tail, 0), 47.5, 0.03)
    return out * 0.22


# ---------------------------------------------------------------- 4. BRASS
def brass_note(m, start, end, amp_pts, bright_pts, voices=3):
    n = int((end - start) * SR)
    tt = np.arange(n) / SR
    a = np.interp(tt, *zip(*[(p - start, v) for p, v in amp_pts]))
    b = np.interp(tt, *zip(*[(p - start, v) for p, v in bright_pts]))
    f0 = midi(m)
    x = np.zeros(n)
    for v in range(voices):
        cents = (v - (voices - 1) / 2) * 6
        vib = 1 + 0.002 * np.sin(2 * np.pi * (4.6 + v * 0.3) * tt + v)
        phase = 2 * np.pi * np.cumsum(f0 * 2 ** (cents / 1200) * vib) / SR + rng.uniform(0, 6)
        for k in range(1, 40):
            if f0 * k > 8000:
                break
            x += (k ** -0.9) * np.exp(-(k - 1) / b) * np.sin(k * phase)
    return x * a / voices


def make_brass():
    out = np.zeros((2, N))
    parts = [
        # notes, start, end, amp envelope, brightness envelope
        ([38, 45], 13.0, 24.3, [(13, 0), (18, 0.35), (24, 0.45), (24.3, 0)],
         [(13, 1.5), (24, 2.6)]),
        ([31, 38, 43], 23.6, 30.3, [(23.6, 0), (24.0, 0.85), (25.5, 0.5), (30, 0.6), (30.3, 0)],
         [(23.6, 6), (25.5, 3), (30, 3.5)]),                                    # BRAAAM
        ([34, 41, 46], 29.7, 34.2, [(29.7, 0), (30.0, 1.0), (31.2, 0.6), (34, 0.75), (34.2, 0)],
         [(29.7, 7), (31.2, 3.5), (34, 4.5)]),                                  # BRAAAM
        ([36, 43, 48, 52], 33.8, 37.1, [(33.8, 0), (34.2, 0.75), (37, 0.9), (37.1, 0)],
         [(33.8, 4.5), (37, 6)]),
        ([33, 40, 45, 49, 52], 36.85, 40.03, [(36.85, 0), (37.2, 0.8), (39.95, 1.25), (40.03, 0)],
         [(36.85, 5), (39.95, 10)]),
        ([26, 38, 45, 50, 53, 57], HIT, 53.0,                                    # THE HIT
         [(40, 0), (40.03, 1.6), (41.0, 1.15), (44.5, 1.0), (49, 0.2), (53, 0)],
         [(40, 12), (41, 8), (44.5, 6), (49, 2), (53, 1.5)]),
    ]
    for notes, s, e, amp, br in parts:
        for k, m in enumerate(notes):
            x = brass_note(m, s, e, amp, br)
            p = np.linspace(-0.6, 0.6, len(notes))[k] if len(notes) > 1 else 0
            place(out, pan(x, p), s, 1.0 / np.sqrt(len(notes)))
    return out * 0.2


# ---------------------------------------------------------------- 5. TENSION: ticking + rising tone
def make_tension():
    out = np.zeros((2, N))
    # accelerating tempo: 58 bpm at 12s -> 172 bpm at 40s
    bpm = np.where(t < 12, 58, 58 * (172 / 58) ** np.clip((t - 12) / 28, 0, 1))
    phase = np.cumsum(bpm / 60 / SR)
    beats = np.where(np.diff(np.floor(phase)) > 0)[0] / SR
    beats = beats[(beats > 12) & (beats < HIT - 0.05)]
    for i, bt in enumerate(beats):
        prog = (bt - 12) / 28
        # tick (clock)
        n = int(0.03 * SR)
        tt = np.arange(n) / SR
        tick = (sos_filter(rng.standard_normal(n), "highpass", 4000, 2) * 0.5
                + np.sin(2 * np.pi * 2100 * tt)) * np.exp(-tt * 180)
        place(out, pan(tick, 0.35 if i % 2 else -0.35), bt, 0.05 + 0.1 * prog)
        # low pulse (timpani-like D)
        n = int(0.6 * SR)
        tt = np.arange(n) / SR
        f = midi(38) * (1 + 0.15 * np.exp(-tt * 30))
        pulse = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * (6 + 10 * prog))
        place(out, pan(pulse, 0), bt, 0.08 + 0.35 * prog ** 1.5)
    # Shepard tone: feels like it rises forever, 24s -> 40s, speeding up
    rate = env([(0, 0), (24, 0.05), (40, 0.45)])           # octaves per second
    pos = np.cumsum(rate) / SR
    sh = np.zeros(N)
    for i in range(7):
        octv = (i + pos) % 7
        f = 40 * 2 ** octv
        amp = np.exp(-0.5 * ((octv - 3.3) / 1.1) ** 2)
        ph = 2 * np.pi * np.cumsum(f) / SR
        sh += amp * (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph))
    sh *= env([(0, 0), (24, 0), (32, 0.25), (39.97, 0.7), (40.0, 0), (60, 0)])
    out += np.stack([sh, np.roll(sh, 240)]) * 0.05
    # reverse-cymbal riser, cut hard on the hit
    rise = sos_filter(noise(), "highpass", 1500, 2)
    rise *= np.clip((t - 35) / 5, 0, 1) ** 3 * (t < HIT)
    out += np.stack([rise, np.roll(rise, 900)]) * 0.12
    return out


# ---------------------------------------------------------------- 6. IMPACT at 40s
def make_impact():
    out = np.zeros((2, N))
    n = int(6 * SR)
    tt = np.arange(n) / SR
    f = 32 + 30 * np.exp(-tt * 2.5)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 0.9)
    thud = sos_filter(rng.standard_normal(n), "lowpass", 220, 4) * np.exp(-tt * 9) * 3
    crack = sos_filter(rng.standard_normal(n), "bandpass", [800, 6000], 2) * np.exp(-tt * 25)
    place(out, pan(boom + thud, 0), HIT, 0.75)
    place(out, pan(crack, -0.2), HIT, 0.25)
    place(out, pan(np.roll(crack, 300), 0.2), HIT, 0.25)
    return out


# ---------------------------------------------------------------- 7. BOOTS
def footstep(heavy=1.0):
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    f = 55 + 35 * np.exp(-tt * 40)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 28) * heavy
    crunch = sos_filter(rng.standard_normal(n), "bandpass", [700, 4500], 2)
    grains = sos_filter((rng.random(n) < 0.05).astype(float), "lowpass", 5000, 2) * 6
    crunch *= (0.4 + grains) * np.minimum(1, tt / 0.004) * np.exp(-tt * 22)
    return thump * 0.9 + crunch * 0.5


def jingle(n_partials=5, length=0.12):
    n = int(length * SR)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * rng.uniform(2200, 7500) * tt) * np.exp(-tt * rng.uniform(25, 60))
            for _ in range(n_partials))
    return x


def make_boots():
    bus = np.zeros((2, N))
    cadence = 1.75  # steps per second
    grid = HIT - np.arange(0, 60) / cadence
    grid = np.sort(grid[grid > 5.5])[:-1]  # last step before the halt
    soldiers = 28
    offs = rng.normal(0, 0.018, soldiers)
    pans = rng.uniform(-0.8, 0.8, soldiers)
    for s in range(soldiers):
        for g in grid:
            at = g + offs[s] + rng.normal(0, 0.012)
            place(bus, pan(footstep(rng.uniform(0.7, 1.1)), pans[s]), at, rng.uniform(0.6, 1.0))
            if rng.random() < 0.25:
                place(bus, pan(jingle(), pans[s]), at + 0.01, 0.08)
    # HALT: one unison stamp + armour settling
    for s in range(soldiers):
        place(bus, pan(footstep(1.4), pans[s]), HIT + rng.normal(0, 0.006), 1.0)
        for _ in range(2):
            place(bus, pan(jingle(6, 0.25), pans[s]), HIT + rng.uniform(0.02, 0.6), 0.1)
    bus /= np.sqrt(soldiers)
    # distance: far = muffled and quiet, near = bright and loud
    d = env([(0, 0), (6, 0), (40, 1), (60, 1)]) ** 1.6
    far = np.stack([sos_filter(c, "lowpass", 450, 2) for c in bus])
    level = env([(0, 0), (5.5, 0), (9, 0.08), (40, 1), (60, 1)])
    return (far * (1 - d) + bus * d) * level * 0.5


# ---------------------------------------------------------------- 8. HORSES
def hoof():
    n = int(0.15 * SR)
    tt = np.arange(n) / SR
    thud = np.sin(2 * np.pi * (85 + 40 * np.exp(-tt * 50)) * tt) * np.exp(-tt * 35)
    clop = sos_filter(rng.standard_normal(n), "bandpass", [350, 1600], 2) * np.exp(-tt * 45)
    return thud * 0.8 + clop * 0.6


def snort(length=0.7):
    n = int(length * SR)
    tt = np.arange(n) / SR
    x = sos_filter(rng.standard_normal(n), "bandpass", [180, 1400], 2)
    flutter = 0.55 + 0.45 * np.sin(2 * np.pi * 28 * tt)
    e = np.minimum(1, tt / 0.04) * np.exp(-tt * 4.5)
    return x * flutter * e


def make_horses():
    bus = np.zeros((2, N))
    for h in range(5):
        stride = rng.uniform(1.05, 1.25)
        p = rng.uniform(-0.7, 0.7)
        at = 13 + rng.uniform(0, 1)
        while at < HIT - 0.05:
            for frac in (0, 0.27, 0.5, 0.77):
                bt = at + frac * stride + rng.normal(0, 0.01)
                if bt < HIT:
                    place(bus, pan(hoof(), p), bt, rng.uniform(0.6, 1.0))
            at += stride
        # a restless shuffle after the halt
        place(bus, pan(hoof(), p), HIT + 0.5 + h * 0.3, 0.6)
    bus /= np.sqrt(5)
    d = env([(0, 0), (13, 0), (40, 1), (60, 1)]) ** 1.5
    far = np.stack([sos_filter(c, "lowpass", 500, 2) for c in bus])
    level = env([(0, 0), (13, 0), (16, 0.15), (40, 0.9), (60, 0.9)])
    out = (far * (1 - d) + bus * d) * level * 0.35
    for at, g, p in [(22.0, 0.08, -0.5), (31.5, 0.12, 0.4), (43.2, 0.22, 0.3), (52.6, 0.16, -0.4)]:
        place(out, pan(snort(), p), at, g)
        place(out, pan(jingle(5, 0.3), p), at + 0.1, g * 0.4)
    return out


# ---------------------------------------------------------------- MIX
def main():
    print("wind…");    wind = make_wind()
    print("sand…");    sand = make_sand()
    print("organ…");   organ = make_organ()
    print("brass…");   brass = make_brass()
    print("tension…"); tension = make_tension()
    print("impact…");  impact = make_impact()
    print("boots…");   boots = make_boots()
    print("horses…");  horses = make_horses()

    print("reverb…")
    music = reverb(organ + brass + tension + impact, 4.5, 4000, 0.45)
    sfx = reverb(boots + horses, 1.2, 6000, 0.18)
    mix = music + sfx + wind + sand

    fade = env([(0, 0), (0.8, 1), (57.5, 1), (60, 0)])
    mix *= fade
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)          # gentle glue / safety
    mix *= 10 ** (-1 / 20) / np.abs(mix).max()       # peak at -1 dBFS

    wav = os.path.join(OUT, "desert_intro_60s.wav")
    raw = (np.clip(mix.T, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2",
                    "-i", "-", "-c:a", "pcm_s16le", wav], input=raw, check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame",
                    "-b:a", "320k", os.path.join(OUT, "desert_intro_60s.mp3")], check=True)
    print("done ->", wav)


if __name__ == "__main__":
    main()
