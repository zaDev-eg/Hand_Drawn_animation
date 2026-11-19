"""Hand-drawn sketch -> animated cartoon (exported from Hand_Drawn_Animation.ipynb)"""
import numpy as np, cv2
from dataclasses import dataclass
from typing import Optional, Tuple
from PIL import Image as PILImage

SKIN = (255, 213, 170)
DARK = (60, 40, 30)
COLORS = {'torso': (70, 110, 230), 'arm_l': (230, 90, 90), 'arm_r': (230, 90, 90), 'leg_l': (60, 170, 120), 'leg_r': (60, 170, 120)}
PARENT = {'torso': None, 'head': 'torso', 'arm_l': 'torso', 'arm_r': 'torso', 'leg_l': 'torso', 'leg_r': 'torso'}
Z_ORDER = {'leg_l': 0, 'leg_r': 0, 'torso': 1, 'arm_l': 2, 'arm_r': 2, 'head': 3}

@dataclass
class Part:
    name: str
    rgba: np.ndarray
    offset: Tuple[int, int]
    pivot: Tuple[float, float] = (0, 0)
    parent: Optional[str] = None
    z: int = 0


def make_part_rgba(name, mask):
    H, W = mask.shape
    thick = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    rgba = np.zeros((H, W, 4), np.uint8)
    if name == "head":
        rgba[..., :3] = SKIN
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        fill = np.zeros_like(mask); cv2.drawContours(fill, cnts, -1, 255, -1)
        rgba[fill > 0, 3] = 255
        rgba[thick > 0] = (*DARK, 255)
    else:
        rgba[..., :3] = COLORS[name]
        rgba[thick > 0, 3] = 255
    rgba[..., 3] = cv2.GaussianBlur(rgba[..., 3], (3, 3), 0)       # smooth edges
    return rgba


def preprocess(rgb):
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    bg = cv2.medianBlur(cv2.dilate(gray, np.ones((7, 7), np.uint8)), 21)   # paper estimate
    norm = cv2.divide(gray, bg, scale=255)                                  # flat lighting
    den = cv2.fastNlMeansDenoising(norm, None, 10, 7, 21)
    pre = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(den)
    return gray, norm, pre


def extract_sketch(pre, min_area=40):
    _, otsu = cv2.threshold(pre, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    adap = cv2.adaptiveThreshold(pre, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY_INV, 31, 10)
    sketch = cv2.bitwise_and(otsu, adap)
    sketch = cv2.morphologyEx(sketch, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(sketch, connectivity=8)
    keep = np.zeros_like(sketch)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            keep[lab == i] = 255
    return keep


def detect_contours(sketch, min_area=30):
    cnts, hier = cv2.findContours(sketch, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    keep = [i for i, c in enumerate(cnts) if cv2.contourArea(c) >= min_area or cv2.arcLength(c, False) > 40]
    return [cnts[i] for i in keep], hier


def segment_character(sketch):
    dil = cv2.dilate(sketch, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(dil)
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    region = (lab == idx).astype(np.uint8) * 255
    char = cv2.bitwise_and(sketch, region)
    bbox = cv2.boundingRect(char)                   # (x, y, w, h)
    return char, bbox


def detect_parts(char, bbox, band_ratio=0.05):
    x, y, w, h = bbox
    H, W = char.shape
    yy, xx = np.mgrid[0:H, 0:W]
    r = (yy - y) / float(h)                                    # relative height 0..1

    band_rows = (char[int(y + 0.30 * h): int(y + 0.55 * h)] > 0).sum(axis=0).astype(float)
    axis = int(np.argmax(np.convolve(band_rows, np.ones(5) / 5, mode="same")))   # body line x
    band = max(6, int(band_ratio * w))
    in_band = np.abs(xx - axis) <= band

    head_r  = r < 0.25
    torso_r = in_band & (r >= 0.25) & (r < 0.66)
    arm_rows = (r >= 0.25) & (r < 0.62) & ~in_band
    leg_rows = (r >= 0.62) & ~torso_r
    regions = {
        "head":  head_r,
        "torso": torso_r,
        "arm_l": arm_rows & (xx < axis),
        "arm_r": arm_rows & (xx >= axis),
        "leg_l": leg_rows & (xx < axis),
        "leg_r": leg_rows & (xx >= axis),
    }
    return regions, axis


def generate_masks(char, regions):
    masks = {}
    for name, reg in regions.items():
        m = ((char > 0) & reg).astype(np.uint8) * 255
        masks[name] = m
    return masks


def extract_parts(masks):
    out = {}
    for name, m in masks.items():
        rgba = make_part_rgba(name, m)
        ys, xs = np.where(rgba[..., 3] > 0)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        out[name] = Part(name, rgba[y0:y1, x0:x1].copy(), (int(x0), int(y0)),
                         parent=PARENT[name], z=Z_ORDER[name])
    return out


def _nearest(mask, ref, k=15):
    ys, xs = np.where(mask > 0)
    d = (xs - ref[0]) ** 2 + (ys - ref[1]) ** 2
    i = np.argsort(d)[:k]
    return int(np.median(xs[i])), int(np.median(ys[i]))


def _farthest(mask, ref, k=15):
    ys, xs = np.where(mask > 0)
    d = (xs - ref[0]) ** 2 + (ys - ref[1]) ** 2
    i = np.argsort(d)[-k:]
    return int(np.median(xs[i])), int(np.median(ys[i]))


def detect_joints(masks, axis, bbox):
    x, y, w, h = bbox
    ty, tx = np.where(masks["torso"] > 0)
    neck_y, torso_bot = int(ty.min()), int(ty.max())
    J = {"neck": (axis, neck_y)}
    for s in ("l", "r"):
        sh = _nearest(masks[f"arm_{s}"], (axis, neck_y + 0.08 * h))
        hp = _nearest(masks[f"leg_{s}"], (axis, torso_bot))
        J[f"shoulder_{s}"] = (axis, sh[1])            # pivot sits on the body axis
        J[f"hip_{s}"] = (axis, hp[1])
        J[f"hand_{s}"] = _farthest(masks[f"arm_{s}"], J[f"shoulder_{s}"])
        J[f"foot_{s}"] = _farthest(masks[f"leg_{s}"], J[f"hip_{s}"])
    J["torso_center"] = (axis, int(ty.mean()))
    return J


def build_character(parts, joints):
    pivots = {"torso": joints["torso_center"], "head": joints["neck"],
              "arm_l": joints["shoulder_l"], "arm_r": joints["shoulder_r"],
              "leg_l": joints["hip_l"], "leg_r": joints["hip_r"]}
    for name, p in parts.items():
        p.pivot = tuple(map(float, pivots[name]))
    return parts


def pose(animation, t):
    s = np.sin(2 * np.pi * t)
    if animation == "walk":
        return {"leg_l": 25 * s, "leg_r": -25 * s, "arm_l": -20 * s, "arm_r": 20 * s,
                "head": 4 * s}, -abs(s) * 6
    if animation == "wave":
        return {"arm_r": 70 + 20 * s, "head": 6 * s}, 0
    if animation == "dance":
        return {"arm_l": -(60 + 25 * s), "arm_r": 60 - 25 * s, "leg_l": 12 * s, "leg_r": 12 * s,
                "head": 10 * s}, -abs(np.sin(4 * np.pi * t)) * 8
    return {}, 0


def make_background(shape):
    H, W = shape[:2]
    top, bot = np.array([150, 205, 255.]), np.array([225, 245, 255.])
    g = np.linspace(0, 1, H)[:, None, None]
    bg = (top * (1 - g) + bot * g) * np.ones((1, W, 1))
    bg = bg.astype(np.uint8)
    cv2.circle(bg, (W - 80, 80), 42, (255, 220, 60), -1, cv2.LINE_AA)           # sun
    cv2.rectangle(bg, (0, H - 40), (W, H), (120, 200, 120), -1)                  # ground
    return bg


def _rot(pivot, angle):
    M = cv2.getRotationMatrix2D((float(pivot[0]), float(pivot[1])), angle, 1.0)
    return np.vstack([M, [0, 0, 1]])


def render_frame(parts, shape, angles, bob=0.0, bg=None):
    H, W = shape[:2]
    canvas = (bg if bg is not None else make_background(shape)).astype(np.float32)
    world = {}
    def get_world(name):                                   # accumulate parent transforms
        if name not in world:
            local = _rot(parts[name].pivot, angles.get(name, 0.0))
            par = parts[name].parent
            world[name] = (get_world(par) @ local) if par else local
        return world[name]
    for p in sorted(parts.values(), key=lambda q: q.z):
        layer = np.zeros((H, W, 4), np.uint8)
        x0, y0 = p.offset; h, w = p.rgba.shape[:2]
        layer[y0:y0 + h, x0:x0 + w] = p.rgba
        M = get_world(p.name)[:2].copy(); M[1, 2] += bob
        layer = cv2.warpAffine(layer, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        a = layer[..., 3:4] / 255.0
        canvas = canvas * (1 - a) + layer[..., :3] * a
    return canvas.astype(np.uint8)


def generate_animation(parts, shape, animation="walk", n_frames=24):
    bg = make_background(shape)
    frames = []
    for i in range(n_frames):
        angles, bob = pose(animation, i / n_frames)
        frames.append(render_frame(parts, shape, angles, bob, bg))
    return frames


def save_gif(frames, path, fps=15):
    pil = [PILImage.fromarray(f) for f in frames]
    pil[0].save(path, save_all=True, append_images=pil[1:], duration=int(1000 / fps), loop=0)
    return path


def run_pipeline(rgb, animation="walk", n_frames=24):
    gray, norm, pre = preprocess(rgb)
    sketch = extract_sketch(pre)
    char, bbox = segment_character(sketch)
    regions, axis = detect_parts(char, bbox)
    masks = generate_masks(char, regions)
    joints = detect_joints(masks, axis, bbox)
    parts = build_character(extract_parts(masks), joints)
    frames = generate_animation(parts, rgb.shape, animation, n_frames)
    return {"sketch": sketch, "char": char, "bbox": bbox, "masks": masks,
            "joints": joints, "parts": parts, "frames": frames}


def live_demo(camera=0):
    # c = capture drawing | w = wave | d = dance | a = walk | q = quit
    cap = cv2.VideoCapture(camera)
    parts, shape, anim, t, bg = None, None, "walk", 0.0, None
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        key = cv2.waitKey(30) & 0xFF
        if key == ord("c"):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                res = run_pipeline(rgb, n_frames=1)
                parts, shape = res["parts"], rgb.shape
                bg = make_background(shape)
            except Exception as e:
                print("capture failed:", e)
        elif key in (ord("w"), ord("d"), ord("a")):
            anim = {ord("w"): "wave", ord("d"): "dance", ord("a"): "walk"}[key]
        elif key == ord("q"):
            break
        if parts is not None:
            angles, bob = pose(anim, t % 1.0)
            out = render_frame(parts, shape, angles, bob, bg)
            cv2.imshow("Magic Sketchbook", cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
            t += 0.04
        cv2.imshow("Camera", frame)
    cap.release(); cv2.destroyAllWindows()


if __name__ == "__main__":
    live_demo()
