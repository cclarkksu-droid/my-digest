"""
Re-time and polish the opening desert shot.

  * slow fade-in from black
  * one smooth camera-speed curve (no sudden speed changes, no stutter):
    new in-between frames are synthesized with optical flow
  * slow left-to-right drift across the terrain
  * soft vignette + fine grain

Usage: python3 smooth_opening.py INPUT.mp4 OUTPUT.mp4
Needs: numpy, opencv-python-headless, ffmpeg
"""
import subprocess, sys
import cv2
import numpy as np

SRC, DST = sys.argv[1], sys.argv[2]
FPS = 24
START_FRAME = 30        # skip the clip's own quick fade-in (first 1.25 s)
REALTIME_FROM = 12.0    # source seconds: from here the camera is already slow & steady
PEAK_SLOWDOWN = 3.4     # how much slower the fast fly-over becomes
FADE_SECONDS = 7.0
ZOOM = 1.2              # head-room needed for the sideways drift
USE_MODEL = '--model' in sys.argv   # optional 4-frame stutter model; direct measurement works better
rng = np.random.default_rng(3)

# ---------------------------------------------------------------- load
cap = cv2.VideoCapture(SRC)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
frames = frames[START_FRAME:]
# drop exact repeats (a stitched join leaves one)
keep = [0]
for i in range(1, len(frames)):
    if np.abs(frames[i].astype(np.int16) - frames[keep[-1]]).mean() > 0.6:
        keep.append(i)
print("source frames:", len(frames), "after removing repeats:", len(keep))
gaps = [k for k in range(1, len(keep)) if keep[k] - keep[k - 1] > 1]
frames = [frames[i] for i in keep]
H, W = frames[0].shape[:2]
# real-time playback begins where the second generated clip was joined on (a repeated frame marks it)
J = gaps[0] if gaps else int(REALTIME_FROM * FPS) - START_FRAME
print("join found at source second", (J + START_FRAME) / FPS)

# ---------------------------------------------------------------- measure camera travel
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
small = [cv2.cvtColor(cv2.resize(f, (640, 360), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
         for f in frames]
step = np.zeros(len(frames) - 1)
for i in range(J + 48):
    fl = dis.calc(small[i], small[i + 1], None)
    step[i] = max(0.0, float(np.median(fl[140:, :, 1])))   # ground streaming toward camera
# The first clip repeats a 4-frame stutter (uneven spacing between frames). Model it as
# smooth speed x repeating 4-frame pattern, which removes measurement noise from single frames.
from scipy.ndimage import uniform_filter1d
raw = step[:J].copy()
base = uniform_filter1d(raw, 8, mode="nearest")
ratio = raw / np.maximum(base, 1e-3)
model = raw.copy()
for i in range(J):
    same = np.arange(i % 4, J, 4)
    same = same[np.abs(same - i) <= 48]
    model[i] = base[i] * np.median(ratio[same])
jumpy = (np.maximum(np.roll(base, 6), np.roll(base, -6)) / np.maximum(np.minimum(np.roll(base, 6), np.roll(base, -6)), 1e-3)) > 1.8
model[jumpy] = raw[jumpy]
if USE_MODEL:
    step[:J] = model
if "--calib" in sys.argv:   # second pass: per-frame-gap corrections learned from a first render
    c = np.load(sys.argv[sys.argv.index("--calib") + 1])
    step[:len(c)] *= c
travel = np.concatenate([[0], np.cumsum(step)])
S = travel[J]
v_src_fast = np.median(step[12:120])
v_end = np.mean(step[J:J + 24])                            # speed at the start of the real-time section
v_peak = v_src_fast / PEAK_SLOWDOWN
print(f"fast speed {v_src_fast:.2f}px/f -> peak {v_peak:.2f}px/f, settle {v_end:.3f}px/f")


def smooth(x):                       # smootherstep 0..1
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (x * 6 - 15) + 10)


def profile(T):
    """Camera speed per output frame over T frames: gentle build, long glide down."""
    u = np.arange(T) / T
    build = 0.45 + 0.55 * smooth(u / 0.30)
    glide = 1 - smooth((u - 0.30) / 0.70)
    return v_end + (v_peak - v_end) * build * glide


lo, hi = 24, 24 * 120                # solve duration so total travel matches
while hi - lo > 1:
    mid = (lo + hi) // 2
    if profile(mid).sum() < S:
        lo = mid
    else:
        hi = mid
T = hi
pos_travel = np.cumsum(profile(T)) * (S / profile(T).sum())
pos = np.interp(pos_travel, travel[:J + 1], np.arange(J + 1))     # fractional source frame
tail = np.arange(J + 1, len(frames))
# ease the leftover fraction to a whole frame so the army section uses untouched frames
pos = np.concatenate([pos, tail])
n_out = len(pos)
print(f"re-timed part: {T/FPS:.1f}s, total: {n_out/FPS:.1f}s")

# ---------------------------------------------------------------- look
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r2 = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
vignette = (1 - 0.12 * np.clip(r2 - 0.25, 0, None) ** 1.2)[..., None].astype(np.float32)
cw, ch = W / ZOOM, H / ZOOM
slack = W - cw
u = np.arange(n_out) / (n_out - 1)
pan_speed = smooth(u / 0.18) * (1 - 0.8 * smooth((u - 0.35) / 0.65))   # eases in, glides down, never stops dead
pan_curve = np.cumsum(pan_speed) / pan_speed.sum()

enc = subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
     "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
     "-pix_fmt", "yuv420p", "-movflags", "+faststart", DST], stdin=subprocess.PIPE)

flow_cache = {}


def flows(i):
    if i not in flow_cache:
        flow_cache.clear()
        a = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        b = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
        flow_cache[i] = (dis.calc(a, b, None), dis.calc(b, a, None))
    return flow_cache[i]


for n in range(n_out):
    p = pos[n]
    i = int(np.floor(p))
    a = np.float32(p - i)
    if a < 0.02 or i >= len(frames) - 1:
        img = frames[min(i, len(frames) - 1)].astype(np.float32)
    elif a > 0.98:
        img = frames[i + 1].astype(np.float32)
    else:
        f01, f10 = flows(i)
        b = np.float32(1) - a
        fa, fb = f01, f10
        for _ in range(3):   # find the motion as seen from the in-between frame
            fa = cv2.remap(f01, xx - a * fa[..., 0], yy - a * fa[..., 1],
                           cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            fb = cv2.remap(f10, xx - b * fb[..., 0], yy - b * fb[..., 1],
                           cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        w0 = cv2.remap(frames[i], xx - a * fa[..., 0], yy - a * fa[..., 1],
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        w1 = cv2.remap(frames[i + 1], xx - b * fb[..., 0], yy - b * fb[..., 1],
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        img = (1 - a) * w0.astype(np.float32) + a * w1.astype(np.float32)
    # left-to-right drift
    x0 = slack * pan_curve[n]
    y0 = (H - ch) * 0.12          # keep the horizon and sky in frame
    M = np.float32([[1 / ZOOM, 0, x0], [0, 1 / ZOOM, y0]])
    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP)
    # grade
    img *= vignette
    img += rng.normal(0, 1.6, (H, W, 1)).astype(np.float32)
    fade = smooth(n / (FADE_SECONDS * FPS)) ** 1.6
    img *= fade
    enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    if n % 120 == 0:
        print(f"  {n}/{n_out}", flush=True)
enc.stdin.close()
enc.wait()
np.savez(DST + ".timing.npz", pos=pos, want=np.diff(pos_travel, prepend=0), J=J)
print("done", DST)
