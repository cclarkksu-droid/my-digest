"""Compare a first render against the intended speed curve and write per-gap corrections.
Usage: python3 calibrate.py RENDER.mp4 OUT.npy   (expects RENDER.mp4.timing.npz next to it)"""
import sys, cv2, numpy as np
vid, out = sys.argv[1], sys.argv[2]
tm = np.load(vid + ".timing.npz"); pos, want, J = tm["pos"], tm["want"], int(tm["J"])
cap = cv2.VideoCapture(vid); dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
prev, got = None, [0.0]
while True:
    ok, f = cap.read()
    if not ok: break
    g = cv2.cvtColor(cv2.resize(f, (640, 360), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    if prev is not None: got.append(max(0.0, float(np.median(dis.calc(prev, g, None)[140:, :, 1]))))
    prev = g
got = np.array(got)[:len(want)]
T = len(want); k = np.floor((pos[:T] + np.concatenate([[0], pos[:T-1]])) / 2).astype(int)   # source gap each output step lies in
mult = np.ones(J)
ratio = got[48:] / np.maximum(want[48:], 1e-6); scale = np.median(ratio)
for g in range(J):
    m = (k == g) & (np.arange(T) >= 48)
    if m.sum() >= 2:
        r = got[m].sum() / want[m].sum() / scale
        if abs(r - 1) > 0.12: mult[g] = r
print("gaps corrected:", int((mult != 1).sum()), "of", J, " largest:", np.round(np.sort(mult)[-5:], 2))
np.save(out, mult)
