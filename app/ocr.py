# app/ocr.py (FULLY REPLACEABLE - NO MISSING FUNCTIONS)
import os
import re
import certifi
import cv2
import easyocr

# Fix SSL for first-time model download (Windows)
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader

# India phone pattern
PHONE_RE = re.compile(r"(\+91\s*)?\d{5}\s*\d{5}|\b\d{10}\b")

JUNK_KEYS = [
    "hey there", "i am using", "using wh", "available", "always happy",
    "destroy", "struggle", "online", "last seen"
]

TILDE_VARIANTS = ["~", "∼", "〜", "～", "﹋", "﹏", "˜"]

def _norm_tilde(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    for v in TILDE_VARIANTS[1:]:
        s = s.replace(v, "~")
    return s

def _is_junk(s: str) -> bool:
    t = (s or "").lower()
    return any(k in t for k in JUNK_KEYS)

def _clean_phone(raw: str) -> str:
    raw = (raw or "").replace(" ", "")
    digits = re.sub(r"\D", "", raw)

    if len(digits) == 10:
        return "+91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits
    if raw.startswith("+91") and len(digits) >= 12:
        return "+91" + digits[-10:]
    return ""

def _looks_like_name(s: str) -> bool:
    if not s or _is_junk(s):
        return False
    return len(re.findall(r"[A-Za-z]", s)) >= 2

def _clean_name_from_tilde(raw: str) -> str:
    """
    STRICT: accept only if contains "~"
    """
    raw = _norm_tilde(raw)
    raw = (raw or "").replace("|", " ").replace("_", " ").strip()
    if "~" not in raw:
        return ""
    raw = raw.split("~", 1)[1].strip()
    raw = re.sub(r"\+91\s*\d{5}\s*\d{5}", " ", raw)
    raw = re.sub(r"\b\d{10}\b", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw if _looks_like_name(raw) else ""

def _clean_name_fallback(raw: str) -> str:
    """
    Fallback if "~" OCR misses; still tries to keep only name-like text.
    """
    raw = _norm_tilde(raw)
    raw = (raw or "").replace("|", " ").replace("_", " ").strip()
    raw = re.sub(r"\+91\s*\d{5}\s*\d{5}", " ", raw)
    raw = re.sub(r"\b\d{10}\b", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw if _looks_like_name(raw) else ""

def _group_into_lines(items, y_tol: int):
    """
    items: [{text, x1, cy}]
    returns: [{cy, text}]
    """
    items.sort(key=lambda a: (a["cy"], a["x1"]))
    lines = []
    for it in items:
        placed = False
        for ln in lines:
            if abs(ln["cy"] - it["cy"]) <= y_tol:
                ln["items"].append(it)
                ln["cy"] = sum(x["cy"] for x in ln["items"]) / len(ln["items"])
                placed = True
                break
        if not placed:
            lines.append({"cy": it["cy"], "items": [it]})

    out = []
    for ln in lines:
        ln["items"].sort(key=lambda a: a["x1"])
        text = " ".join([x["text"] for x in ln["items"]]).strip()
        out.append({"cy": ln["cy"], "text": text})
    out.sort(key=lambda x: x["cy"])
    return out

def extract_contacts(image_path: str):
    """
    Robust alignment:
    - Phones from right crop (with cy positions)
    - Names from left crop (tilde preferred, fallback allowed)
    - Pair each phone with nearest NAME line above (within threshold)
    - Filters out 'Search' header etc.
    """
    reader = get_reader()
    img = cv2.imread(image_path)
    if img is None:
        return []

    h, w = img.shape[:2]
    max_w = 1100
    if w > max_w:
        scale = max_w / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        h, w = img.shape[:2]

    left_end = int(w * 0.78)
    right_start = int(w * 0.68)
    left = img[:, :left_end].copy()
    right = img[:, right_start:].copy()

    # ---------- RIGHT OCR (phones with cy) ----------
    right_ocr = reader.readtext(right, detail=1, workers=0)
    r_items = []
    for box, text, conf in right_ocr:
        t = (text or "").strip()
        if not t:
            continue
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        r_items.append({"text": t, "x1": min(xs), "cy": (min(ys) + max(ys)) / 2.0})

    r_lines = _group_into_lines(r_items, y_tol=26)

    phones = []
    for ln in r_lines:
        joined = re.sub(r"\s+", "", ln["text"])
        m = PHONE_RE.search(joined)
        if not m:
            continue
        phone = _clean_phone(m.group(0))
        if not phone:
            continue
        digits = re.sub(r"\D", "", phone)
        if phone.startswith("+91") and len(digits) == 12:
            phones.append({"cy": ln["cy"], "phone": phone})

    phones.sort(key=lambda x: x["cy"])
    seen = set()
    phones2 = []
    for p in phones:
        if p["phone"] in seen:
            continue
        seen.add(p["phone"])
        phones2.append(p)
    phones = phones2

    if not phones:
        return []

    # ---------- LEFT OCR (name lines with cy) ----------
    left_ocr = reader.readtext(left, detail=1, workers=0)
    l_items = []
    for box, text, conf in left_ocr:
        t = _norm_tilde((text or "").strip())
        if not t:
            continue
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        l_items.append({"text": t, "x1": min(xs), "cy": (min(ys) + max(ys)) / 2.0})

    l_lines = _group_into_lines(l_items, y_tol=24)

    name_lines = []
    for ln in l_lines:
        txt = _norm_tilde(ln["text"])
        if not txt:
            continue

        low = txt.lower().strip()
        # remove top header like "Search"
        if low.startswith("search"):
            continue
        if _is_junk(txt):
            continue

        nm = _clean_name_from_tilde(txt)
        if nm:
            name_lines.append({"cy": ln["cy"], "name": nm, "strong": True})
        else:
            nm2 = _clean_name_fallback(txt)
            if nm2:
                name_lines.append({"cy": ln["cy"], "name": nm2, "strong": False})

    if not name_lines:
        return []

    name_lines.sort(key=lambda x: x["cy"])

    # ---------- Pair each phone with nearest name ABOVE ----------
    results = []
    used_name_lines = set()

    MAX_GAP = 170  # tuneable; works for WhatsApp spacing

    for p in phones:
        candidates = [n for n in name_lines if n["cy"] <= p["cy"] and (p["cy"] - n["cy"]) <= MAX_GAP]
        if not candidates:
            continue

        candidates.sort(key=lambda n: (0 if n["strong"] else 1, (p["cy"] - n["cy"])))

        chosen = candidates[0]
        key = round(chosen["cy"] / 5)

        # prevent reusing same name-line for many phones
        if key in used_name_lines and len(candidates) > 1:
            chosen = candidates[1]
            key = round(chosen["cy"] / 5)

        used_name_lines.add(key)

        results.append({"Name": chosen["name"], "Mobile": p["phone"]})

    return results
