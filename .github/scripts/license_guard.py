#!/usr/bin/env python3
"""
License Guard
Scans a git diff (and, for known copyrighted artwork, the whole tree) for changes that would strip or replace ANY upstream copyright
notice (Dortania, Dhinak G / Mykola Grymalyuk, ASentientBot, dosdude1, Apple, ...)
or the license text itself, e.g.
    - Copyright (c) 2020-2026 Dortania
    + Copyright (c) 2020-2026 Albert
Year bumps are ignored. Adding your own copyright *next to* an existing one is fine
and only reported as info.

Usage: license_guard.py <git-diff-range>     e.g. "abc123...pr-head"
Env:   UPSTREAM_HOLDER (default "Dortania"), REPORT_PATH (default license-report.md)
"""
import fnmatch
import io
import os
import re
import subprocess
import sys
from collections import Counter

HOLDER = os.environ.get("UPSTREAM_HOLDER", "Dortania")
REPORT = os.environ.get("REPORT_PATH", "license-report.md")
MARKER = "<!-- license-guard -->"
DIFF_RANGE = sys.argv[1]

# A copyright *notice*: "©", "(c) 2020", or the word "Copyright" followed by a year or a name
# ("Copyright 2020 ...", "Copyright (c) Apple", "Copyright © Dortania"). Prose like "copyright label",
# comments like "Text: Copyright" and identifiers like AuthorizationCopyRights don't count.
COPYRIGHT_RE = re.compile(
    r"©|\([cC]\)\s*\d|(?<![A-Za-z_])(?i:copyright)(?![A-Za-z_])\s*(?:\([cC]\)|©)?\s*(?:\d{4}|[A-Z][A-Za-z])")
SPDX_RE = re.compile(r"SPDX-License-Identifier:\s*(.+?)\s*(?:\*/|-->|$)", re.I)
LICENSE_FILE_RE = re.compile(r"(^|/)(LICEN[CS]E|COPYING|NOTICE)(\.(txt|md|rst))?$", re.I)
# The guards' own files (this script and the workflows, incl. attribution-guard.yml) quote
# copyright notices in their patterns and docs - don't scan them.
def is_self(path):
    return (path in (".github/scripts/license_guard.py", RELOCATED_FILE)
            or path.startswith(".github/workflows/"))


# Reviewed deletions: paths (glob patterns) listed here don't raise the "file with an upstream
# copyright notice was deleted" warning. Only that warning - violations are never suppressed.
# Read from the checked-out base branch, so a PR can't allowlist its own changes.
ALLOW_FILE = ".github/license-guard-allow.txt"


def load_allow():
    try:
        with open(ALLOW_FILE, encoding="utf-8") as fh:
            return [l.split("#", 1)[0].strip() for l in fh if l.split("#", 1)[0].strip()]
    except FileNotFoundError:
        return []
# Relocated notices: files deleted here because they (and their notices) now live elsewhere,
# e.g. the website that moved to its own repo. "<glob> -> <destination>" per line. Only full
# deletions of matching files are accepted; edits to notices are still checked as usual.
RELOCATED_FILE = ".github/relocated-notices.txt"


def load_relocated():
    entries = []
    try:
        with open(RELOCATED_FILE, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.split("#", 1)[0].strip()
                if "->" not in line:
                    continue
                pattern, dest = (part.strip() for part in line.split("->", 1))
                if pattern and dest:
                    entries.append((pattern, dest))
    except FileNotFoundError:
        pass
    return entries


# Known copyrighted artwork. Unlike the checks above, this scans EVERY file in the audited
# tree (not just the diff), so an old copy anywhere in the fork is found too.
# Only fingerprints are stored here, never the images themselves.
# Fingerprint = 256-bit dHash (16x16) of the image composited on grey, white and black,
# so resized, recompressed or flattened copies still match.
KNOWN_ART = {
    "dortania-oclp-icon": {
        "name": "Dortania's OpenCore Legacy Patcher icon",
        "holder": "Dortania",
        "embedded": True,  # also searched for INSIDE larger images (screenshots, banners)
        "hashes": [
            "2002461d90f6233b0e0f18a718f71967196718e71ae70f8f271b90f6469c2002",
            "2002469d90fe233b0e0f18a718f7196719671ce71be70d8f233b10f60c0c0000",
            "2002471d88ce33332e0b0a271cf7186719671ce71aa70fcf231b90f60e8c0000",
            "20284e8030f063384e0cd8a498f6996699669ce4dbe4cd8ce33870f1bc02417c",
            "20304e1c90f6233b0e0f18a718f61966196618e61ae54f8d271bd0f26e840030",
            "3002471c88ce33332e0b1a271cf7186799669ce6daa4cfcce31870f13e820024",
            "4004371068c9d334ee08da24dcf4d864d964dce4daa4cfccc31c70f13e800000",
            "40043e8070f1e338ce0cd8a4d8f4d964d964d8e4dae4cf8ce71870f13e804004",
            "4004be8270f1e338ce0cd8a4d8f4d964d964dce4dbe4cd8ce33870f1bc024004",
        ],
    },
    "apple-system-settings-icon": {
        "name": "Apple's System Settings icon",
        "holder": "Apple",
        "embedded": True,
        "hashes": [
            "200243bd8cce30f3231b2b4b09af1c8f1c8f09af2b4b231b30f38cc6001c2002",
            "300243bc9cce30f3231b2b4b09af5c8d5c8d49adcb49e319f0f17cc038000040",
            "40043b607cc1e0f0e31ccb4cc9acdc8cdc8cc9accb4cc31cc0f87cc138004004",
        ],
    },
    # Apple's macOS wallpaper release banners ("macOS <name>" on the release wallpaper) are NOT
    # listed here on purpose: the maintainer decided to keep them on the drop pages, as Dortania
    # and most other sites do, to identify the macOS version.
}
# Hamming distance (of 256 bits). Measured on this repo: copies 0-17, icons that embed
# the logo 39-51, unrelated icons 59+.
ART_COPY_MAX = 30      # -> violation
ART_DERIVED_MAX = 52   # -> warning (probably contains the artwork, check by hand)
# Embedded search (icon somewhere inside a screenshot/banner). Measured on this repo:
# screenshots that show the icon 26-40, everything else 54+.
EMBED_COPY_MAX = 44    # -> violation
EMBED_WARN_MAX = 50    # -> warning
EMBED_MIN_PX = 40      # smallest icon size searched for (after downscaling, see below)
EMBED_MAX_DIM = 1400   # large screenshots are downscaled to this first (speed)
# Dortania's app and main-menu button icons shown INSIDE screenshots - often small, dimmed behind
# a dialog, or on a coloured background (Dock, window). The dHash search above misses those, so
# each icon is also searched with OpenCV template matching: the whole icon, masked by its own
# transparency (so the background around it doesn't matter), in greyscale with normalised
# correlation (so dimming and brightness don't matter), at every size from ICON_MIN_PX up.
# The references are read from Dortania's tree at run time (the left side of the audit range),
# so no copy of the artwork is stored in this repository.
UPSTREAM_ICONS = {
    "dortania-oclp-icon": ("payloads/Icon/AppIcons/OC-Patcher.icns", "Dortania's OpenCore Legacy Patcher icon"),
    "dortania-build-icon": ("payloads/Icon/AppIcons/OC-Build.icns",
                            "Dortania's \"Build and Install OpenCore\" icon (logo with screwdriver)"),
    "dortania-installer-icon": ("payloads/Icon/AppIcons/OC-Installer.icns",
                                "Dortania's \"Create macOS Installer\" icon (mac OS disc with arrow)"),
    "dortania-support-icon": ("payloads/Icon/AppIcons/OC-Support.icns", "Dortania's \"Support\" icon (Dortania manual)"),
    # Volume icons Dortania's app copies onto the EFI partition, so they show up in the boot picker
    # ("EFI Boot"), in Finder and on the Desktop: the OpenCore logo with a drive in front of it.
    "dortania-external-drive-icon": ("payloads/Icon/DriveIcons/External/.VolumeIcon.icns",
                                     "Dortania's external drive icon (OpenCore logo with a gold drive)"),
    "dortania-internal-drive-icon": ("payloads/Icon/DriveIcons/Internal/.VolumeIcon.icns",
                                     "Dortania's internal drive icon (OpenCore logo with a hard disk)"),
    "dortania-sd-card-drive-icon": ("payloads/Icon/DriveIcons/SD-Card/.VolumeIcon.icns",
                                    "Dortania's SD card drive icon (OpenCore logo with an SD card)"),
    "dortania-ssd-drive-icon": ("payloads/Icon/DriveIcons/SSD/.VolumeIcon.icns",
                                "Dortania's SSD drive icon (OpenCore logo with an NVMe SSD)"),
}
ICON_VERSION = 1        # bump to invalidate cached results after changing the settings below
ICON_T = 48             # template size (px)
ICON_MIN_PX = 40        # smallest icon searched for, in the image's own pixels
ICON_STEP = 1.12        # size step between searches
ICON_MAX_WORK = 2400    # longest side of a scaled copy; tinier icons in huge images are skipped (speed)
# Correlation, measured on this repo: screenshots with the icons 0.79-0.93 (dimmed behind a dialog,
# in the Dock, on a banner); synthetic copies 48-160px, dimmed or not, 0.74-0.98; everything else
# at most 0.70 (BridgePatcher's own icons 0.67).
ICON_VIOLATION = 0.76
ICON_WARNING = 0.72
# Per-icon (warning, violation) where the defaults above don't fit. Drive icons, measured on this repo:
# the boot picker screenshot with the external drive icon 0.97, synthetic copies 96px+ 0.79-0.98;
# everything else at most 0.65 - except for the SSD icon, whose plain dark card shape also scores
# up to 0.77 on unrelated screenshots and charts, so it needs a stricter threshold.
ICON_THRESHOLDS = {"dortania-ssd-drive-icon": (0.80, 0.88)}
# Results per blob, so the second scan of a PR (base branch) doesn't redo every image.
ART_CACHE = os.environ.get("ART_CACHE", ".license-guard-art-cache.json")
ART_MAX_BYTES = 20_000_000
IMAGE_EXT = (".png", ".icns", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff", ".bmp", ".ico")
TEXT_EXT = (".md", ".markdown", ".html", ".htm", ".js", ".mjs", ".jsx", ".ts", ".mts", ".tsx", ".vue", ".css",
            ".scss", ".py", ".plist", ".json", ".yml", ".yaml", ".txt", ".rst")
# The project's former name. "OpenCore Legacy Patcher T2" / "OpenCore Patcher T2" / "OCLP-T2"
# now counts as a typosquat of BridgePatcher (and of Dortania's project), so it must not appear
# in page text any more. The spelled-out forms match in any case and with or without "Legacy";
# "OCLP-T2"/"OCLPT2" is case-sensitive on purpose: lowercase URLs, anchors and storage keys
# (oclp-t2/...) are fine. Without "Legacy" only spaces count as separators, because
# "OpenCore-Patcher-T2" is the old app bundle name (LEGACY_APP_RE below).
OLD_NAME_RE = re.compile(
    r"(?<![\w/#.-])(?:(?i:Open[ -]?Core[ -]+Legacy[ -]+Patcher[ -]+T2|Open\s?Core[ \t]+Patcher[ \t-]+T2)"
    r"|OCLP[- ]?T2)(?![\w])")
# The app bundle/executable was called OpenCore-Patcher-T2 before the rename; it is BridgePatcher.app
# (executable BridgePatcher) now. Telling users to run, find or allow "OpenCore-Patcher-T2" is out of
# date. Still correct and never matched: the install directory (.../OpenCore-Patcher-T2/), the legacy
# installer asset OpenCore-Patcher-T2.pkg, and lines that talk about builds from before the rename.
LEGACY_APP_RE = re.compile(
    r"OpenCore-Patcher-T2\.app(?![\w-])"
    r"|/MacOS/OpenCore-Patcher-T2(?![\w.-])"
    r"|(?<![\w/#.'\"-])OpenCore-Patcher-T2(?![\w./-])")
LEGACY_APP_OK_RE = re.compile(
    r"(?i)before the rename|pre-rename|legacy|older (?:build|release|version)s?"
    r"|vor der Umbenennung|ältere[nrs]? (?:Build|Version|Release)")
# Dortania's app name used as the name of THIS project in page text, titles or config
# ("With OpenCore Legacy Patcher 2.0.0 we ...", a window title, a nav label). BSD licence:
# the upstream name must not be used to endorse or promote the fork. Allowed only where the
# line clearly refers to Dortania's project: copyright/credit lines, lines that name Dortania,
# the licence's own title, and "based on"/"fork of" statements. Slugs and URLs without
# spaces (OpenCore-Legacy-Patcher) are literal names and never matched.
UPSTREAM_NAME_RE = re.compile(r"(?i)(?<![\w/#.-])Open\s?Core[ \t]+Legacy[ \t]+Patcher(?![\w-])")
UPSTREAM_NAME_OK_RE = re.compile(
    r"(?i)dortania|©|\(c\)\s*\d|copyright|contributors|mitwirkende"
    r"|OpenCore Legacy Patcher Licen[sc]e|Lizenz von OpenCore Legacy Patcher"
    r"|\b(?:based on|fork of|forked from|derived from|basiert auf|Fork von|abgeleitet von)\b")
OLD_NAME_EXT = (".md", ".markdown", ".html", ".htm", ".vue", ".mts", ".ts", ".js", ".json", ".webmanifest", ".xsl")
# URLs and Markdown link/image targets are removed before the name rules below are matched:
# Dortania's repo and file names (./images/OCLP-GUI-...png) keep their names.
URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+|\]\([^)\s]*\)|\bsrc=\"[^\"]*\"")
# The abbreviation "OCLP" used for THIS project ("With OCLP v0.2.5, we've added ..."): Dortania's
# name for its own app. Not matched: OCLP-* / OCLP_* identifiers (NVRAM keys such as OCLP-Version,
# the OCLP-Installer volume), lowercase identifiers and paths, names of other forks (OCLP-Mod, ...).
# Fine where the line makes clear Dortania's project is meant ("Dortania's OCLP 0.2.5").
OCLP_RE = re.compile(r"(?<![\w./$-])OCLP(?![\w-])")
OCLP_OTHER_RE = re.compile(r"(?i)OCLP[ -](?:Plus|Mod|R|GUI)\b|OCLP Self Signed")
OCLP_OK_RE = re.compile(r"(?i)dortania|upstream|formerly|former names?|früher|ehemals|typosquat|©|copyright")
# Dortania's app bundle and executable (OpenCore-Patcher.app/Contents/MacOS/OpenCore-Patcher). Telling
# users to run, open or allow it presents Dortania's app as BridgePatcher (BridgePatcher.app now).
UPSTREAM_APP_RE = re.compile(r"(?<![\w-])OpenCore-Patcher\.app(?![\w-])|/MacOS/OpenCore-Patcher(?![\w.-])")
UPSTREAM_APP_OK_RE = re.compile(r"(?i)dortania")
# Dortania's release numbers presented as BridgePatcher's ("starting from BridgePatcher version 2.1.0",
# a window title "BridgePatcher (0.6.8)", a banner "... with BridgePatcher 0.5.1"). BridgePatcher's own
# versions start at 3.0.0 alpha 4.1, so 0.x, 1.x and 2.x after the name are always Dortania's releases
# (OpenCore Legacy Patcher 0.6.8, 2.1.0, ...) claimed for this project. Used for page text and for the
# text read in images.
OWN_NAME_OLD_VERSION_RE = re.compile(
    r"(?i)\bBridge\s?Patcher(?:'s)?(?:[ \t-]+(?:version|release|Versions?|Release))?[ \t]*[(\[]?[ \t]*v?\.?[ \t]?"
    r"([0-2]\.\d{1,2}(?:\.\d{1,2})?)(?![\d.]*\s?(?:GB|MB|KB|%))")

# Invite links to the upstream project's Discord server (OpenCore Patcher Paradise, the server
# Dortania's OCLP docs send users to). Pointing BridgePatcher users there for support implies
# the upstream project endorses or supports the fork - send them to our own channels instead.
# Invite codes are case-sensitive, so the code is matched exactly.
UPSTREAM_DISCORD_CODES = ("rqdPgH8xSN",)
UPSTREAM_DISCORD_RE = re.compile(
    r"(?i:(?:https?://)?(?:www\.)?(?:discord\.gg/|discord(?:app)?\.com/invite/))(?:"
    + "|".join(map(re.escape, UPSTREAM_DISCORD_CODES)) + r")(?![A-Za-z0-9])")

# Dortania's images used directly from their repo or website (e.g. the old README logo).
HOTLINK_RE = re.compile(
    r"(?:raw\.githubusercontent\.com/dortania/|github\.com/dortania/[^\s\"'()<>]*/(?:raw|blob)/"
    r"|dortania\.github\.io/)[^\s\"'()<>]*\.(?:png|icns|svg|jpe?g|gif|webp)", re.I)


def dhash256(data, bg):
    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        im = im.convert("RGBA")
    base = Image.new("RGBA", im.size, bg + (255,))
    base.alpha_composite(im)
    g = base.convert("L").resize((17, 16), Image.LANCZOS).tobytes()
    bits = 0
    for r in range(16):
        for c in range(16):
            bits = (bits << 1) | (g[r * 17 + c] > g[r * 17 + c + 1])
    return bits


def icon_template(data):
    """Greyscale template of an icon, cropped to its visible part, plus a mask of its opaque pixels."""
    import numpy as np
    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        im = im.convert("RGBA")
    ys, xs = np.where(np.array(im)[..., 3] > 10)
    im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    f = ICON_T / max(im.size)
    im = im.resize((max(8, round(im.width * f)), max(8, round(im.height * f))), Image.LANCZOS)
    arr = np.array(im).astype(np.float32)
    grey = arr[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
    return grey, (arr[..., 3] > 200).astype(np.float32)


def icon_scores(data, templates):
    """Best match of each icon anywhere in the image: {key: [score, size_px, x, y]}."""
    import cv2
    import numpy as np
    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        im = im.convert("RGBA")
    base = Image.new("RGBA", im.size, (128, 128, 128, 255))
    base.alpha_composite(im)
    grey = np.array(base.convert("L")).astype(np.float32)
    H, W = grey.shape
    out = {}
    for key, (tpl, mask) in templates.items():
        best, d = [-1.0, 0, 0, 0], float(ICON_MIN_PX)
        while d <= min(H, W):
            f = ICON_T / d
            if max(W, H) * f <= ICON_MAX_WORK:
                small = cv2.resize(grey, (max(tpl.shape[1], round(W * f)), max(tpl.shape[0], round(H * f))),
                                   interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_LINEAR)
                r = cv2.matchTemplate(small, tpl, cv2.TM_CCOEFF_NORMED, mask=mask)
                r[~np.isfinite(r)] = -1
                _, v, _, loc = cv2.minMaxLoc(r)
                if v > best[0]:
                    best = [round(float(v), 3), round(d), round(loc[0] / f), round(loc[1] / f)]
            d *= ICON_STEP
        out[key] = best
    return out


def load_icon_templates(add):
    """Templates of Dortania's icons from the upstream tree, or {} (with a warning) if unavailable."""
    try:
        import cv2  # noqa: F401
    except ImportError:
        add("warning", "-", "Icon-in-screenshot check skipped: opencv-python-headless is not installed")
        return {}
    upstream = os.environ.get("ICON_REF") or re.split(r"\.\.\.?", DIFF_RANGE)[0].split(":")[0]
    templates, missing = {}, []
    for key, (ref_path, _) in UPSTREAM_ICONS.items():
        ref = subprocess.run(["git", "show", f"{upstream}:{ref_path}"], capture_output=True)
        try:
            templates[key] = icon_template(ref.stdout) if ref.returncode == 0 else None
        except Exception:
            templates[key] = None
        if templates[key] is None:
            del templates[key]
            missing.append(ref_path)
    if missing:
        add("warning", "-", f"Icon-in-screenshot check incomplete: not found in {upstream}",
            [f"  {p}" for p in missing])
    return templates


def _bits(h):
    import numpy as np
    return np.array([(h >> (255 - i)) & 1 for i in range(256)], dtype=np.float32)


def find_embedded(data, known_bits):
    """Search for known icons INSIDE an image: a dHash over sliding windows at many sizes
    (coarse pass), then a fine search around the promising spots. Returns
    {key: (distance, size_px, x, y)} with the best match per artwork."""
    import numpy as np
    from numpy.lib.stride_tricks import sliding_window_view
    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        im = im.convert("RGBA")
    scale = 1.0
    if max(im.size) > EMBED_MAX_DIM:
        scale = EMBED_MAX_DIM / max(im.size)
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    base = Image.new("RGBA", im.size, (128, 128, 128, 255))
    base.alpha_composite(im)
    gray = base.convert("L")
    W, H = gray.size

    def dists(s, x0, y0, x1, y1):
        cw, ch = s / 17, s / 16
        w, h = int((x1 - x0) / cw), int((y1 - y0) / ch)
        if w < 17 or h < 16:
            return {}
        g = np.asarray(gray.resize((w, h), Image.BILINEAR, box=(x0, y0, x0 + w * cw, y0 + h * ch),
                                   reducing_gap=2.0), dtype=np.int16)
        win = sliding_window_view(g[:, :-1] > g[:, 1:], (16, 16))
        shape = win.shape[:2]
        flat = win.reshape(-1, 256).astype(np.float32)
        ones = flat.sum(1)
        out = {}
        for key, kb in known_bits.items():
            # Hamming distance to every known hash at once: |a| + |b| - 2 a.b
            d = (ones[:, None] + kb.sum(1)[None, :] - 2 * (flat @ kb.T)).min(1).reshape(shape)
            i = np.unravel_index(np.argmin(d), shape)
            out[key] = (int(d[i]), s, x0 + i[1] * cw, y0 + i[0] * ch)
        return out

    best, cands = {}, []
    s = float(EMBED_MIN_PX)
    while s <= min(W, H):
        for key, r in dists(s, 0, 0, W, H).items():
            if r[0] <= EMBED_WARN_MAX + 12:
                cands.append((key, r))
            if key not in best or r[0] < best[key][0]:
                best[key] = r
        s *= 1.15
    for key, (_, s, x, y) in cands:
        for s2 in np.geomspace(s / 1.12, s * 1.12, 7):
            for fx in np.linspace(-0.5, 0.5, 5):
                for fy in np.linspace(-0.5, 0.5, 5):
                    x0 = max(0.0, x + fx * s2 / 8 - s2 / 17)
                    y0 = max(0.0, y + fy * s2 / 8 - s2 / 16)
                    r = dists(s2, x0, y0, min(W, x0 + s2 * 1.25), min(H, y0 + s2 * 1.25)).get(key)
                    if r and r[0] < best[key][0]:
                        best[key] = r
    return {k: (d, round(sz / scale), round(x / scale), round(y / scale)) for k, (d, sz, x, y) in best.items()}


# The upstream app's NAME shown inside an image (screenshots of Dortania's app, banners):
# "OpenCore Legacy Patcher" (also "... T2" / "...-T2"). Found with OCR (tesseract), so it only runs
# where tesseract is installed. Lines with a copyright notice are skipped on purpose - the upstream
# notice ("Copyright © 2020-2026 Dortania and OpenCore Legacy Patcher contributors") must stay.
# Technical identifiers written without spaces (OCLP-Version, Dortania's URLs) are not matched here;
# folder/volume names such as "OpenCore-Legacy-Patcher" are covered by IMG_FOLDER_RE below.
IMG_NAME_RE = re.compile(r"(?i)\bOpen\s?Core\s+Legacy\s+Patcher\b")
IMG_NAME_WRAP = (re.compile(r"(?i)\bOpen\s?Core(\s+Legacy)?\s*$"), re.compile(r"(?i)^\s*(Legacy\s+)?Patcher\b"))
IMG_COPYRIGHT_RE = re.compile(r"(?i)(©|\(c\))\s*\d|copyright|contributors")
OCR_VERSION = 3   # bump to invalidate cached OCR results after changing the OCR settings


def ocr_lines(data):
    """Text lines in an image (normal + inverted pass, so light-on-dark text is read too, plus a
    binarized pass for dim text such as a dark-mode window title: grey ~80 on ~33 is too faint
    for tesseract otherwise)."""
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        im = im.convert("RGBA")
    base = Image.new("RGBA", im.size, (255, 255, 255, 255))
    base.alpha_composite(im)   # translucent dialogs: read them as shown on a light page
    g = base.convert("L")
    s = 3 if max(g.size) <= 1200 else 2 if max(g.size) <= 1800 else 1   # small UI text needs upscaling
    if s > 1:
        g = g.resize((g.width * s, g.height * s), Image.LANCZOS)
    images = [g, ImageOps.invert(g)]
    hist = g.histogram()
    half, acc, median = sum(hist) / 2, 0, 0
    for median, n in enumerate(hist):
        acc += n
        if acc >= half:
            break
    if median < 100:     # dark UI: anything clearly brighter than the background is text
        images.append(g.point(lambda v: 0 if v > median + 25 else 255))
    elif median > 160:   # light UI: anything clearly darker than the background is text
        images.append(g.point(lambda v: 0 if v < median - 40 else 255))
    # Local-contrast passes: text is what is clearly darker (or brighter) than its own surroundings,
    # not than the whole image. Needed for dim text on a grey band, e.g. the title of an inactive
    # window ("OpenCore Legacy Patcher T2 ..." in grey ~136 on a ~202 title bar in a mostly white
    # screenshot): tesseract's global threshold and the median pass above both turn the whole bar
    # black and lose the title.
    import numpy as np
    from PIL import ImageFilter
    a = np.asarray(g, np.int16)
    local = np.asarray(g.filter(ImageFilter.BoxBlur(12 * s)), np.int16)
    images.append(Image.fromarray(np.where(a < local - 20, 0, 255).astype(np.uint8)))   # dark on light
    images.append(Image.fromarray(np.where(a > local + 20, 0, 255).astype(np.uint8)))   # light on dark
    passes = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, "PNG")
        r = subprocess.run(["tesseract", "stdin", "stdout", "--psm", "11", "tsv"], input=buf.getvalue(),
                           capture_output=True, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
        lines = {}
        for row in r.stdout.decode("utf-8", "replace").splitlines()[1:]:
            c = row.split("\t")
            if len(c) == 12 and c[0] == "5" and c[11].strip() and float(c[10]) > 0:
                lines.setdefault((int(c[2]), int(c[3]), int(c[4])), []).append(c[11].strip())
        passes.append([" ".join(v) for _, v in sorted(lines.items())])
    return passes


def find_old_name_in_image(passes):
    hits = []
    for lines in passes:
        for i, line in enumerate(lines):
            if IMG_COPYRIGHT_RE.search(line):
                continue
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if IMG_NAME_RE.search(line) or (IMG_NAME_WRAP[0].search(line) and IMG_NAME_WRAP[1].search(nxt)
                                            and not IMG_COPYRIGHT_RE.search(nxt)):
                if line not in hits:
                    hits.append(line)
    return hits


# Dortania's project name used as a FOLDER or VOLUME name in a screenshot: the Finder sidebar
# ("Opencore-Legacy-Pat..."), path bars and Terminal ("~/Developer/OpenCore-Legacy-Patcher"),
# "Apple-Binaries-OCLP". BridgePatcher is cloned into a "BridgePatcher" folder, so these are
# Dortania's screenshots. Not matched: URLs (github.com/dortania/OpenCore-Legacy-Patcher), file names
# (OpenCore-Legacy-Patcher.plist) and the OCLP-* identifiers BridgePatcher itself still uses
# (NVRAM keys OCLP-Version/-Settings/..., the OCLP-Installer volume) - a screenshot showing those is accurate.
IMG_FOLDER_RE = re.compile(r"(?i)(?<![\w/.-])Open\s?Core[-_]Legacy(?:[-_][A-Za-z]*)?(?![\w-])(?!\.[A-Za-z])")
IMG_OCLP_TOKEN_RE = re.compile(r"(?<![\w/.-])((?:[A-Za-z0-9]+[-_\u2013\u2014])*OCLP(?:[-_\u2013\u2014][A-Za-z0-9]+)*)(?![\w/-])")
# "Install(er)" also matches an OCR read that drops the last letter(s) at the end of a line
# ("... with name OCLP-Installe").
IMG_OCLP_OK_RE = re.compile(r"^OCLP-(?:Version|Settings|Model|Spoofed-\w+|Install(?:er?)?|Helper|MOD)$")


def find_upstream_folder_in_image(passes):
    hits = []
    for lines in passes:
        for line in lines:
            if IMG_COPYRIGHT_RE.search(line) or line in hits:
                continue
            tokens = [re.sub("[\u2013\u2014_]", "-", m.group(1)) for m in IMG_OCLP_TOKEN_RE.finditer(line)]
            if IMG_FOLDER_RE.search(line) or any(t != "OCLP" and not IMG_OCLP_OK_RE.match(t) for t in tokens):
                hits.append(line)
    return hits


# Mykola Grymalyuk (Dortania's co-author) named inside an image. Dortania's screenshots were taken
# on his Mac, so they show his macOS user ("mykolagrymalyuk" in Finder, Terminal titles and prompts),
# "Mykola's MacBook Pro" / "Mykola's iMac" in Finder and Displays, or "Mykola Monterey" in password
# prompts. Such an image is Dortania's screenshot, and clause 4 of the licence forbids using his name
# to promote a derived product. Tolerates common OCR misreads (Nykola, Mykole, a truncated
# "mykolagryma..."). Copyright/licence lines are skipped: that notice must stay, see the attribution guard.
IMG_AUTHOR_RE = re.compile(r"(?i)[mn][yv]k[o0][l1][aeo]|gr[yi]ma[l1]|gyumurluk")


def find_author_in_image(passes):
    hits = []
    for lines in passes:
        for line in lines:
            if IMG_AUTHOR_RE.search(line) and not IMG_COPYRIGHT_RE.search(line) and line not in hits:
                hits.append(line)
    return hits


# Dortania's own screenshots with the app or folder name edited to "BridgePatcher". The website started
# as a copy of Dortania's docs/ folder; an image that is (almost) one of Dortania's docs images but now
# reads "BridgePatcher" is Dortania's screenshot (Dortania's Mac, Dortania's app and releases) passed
# off as BridgePatcher's. Found by comparing every image with the images in Dortania's docs tree (the
# left side of the audit range, read at run time) - no copy of them is stored here. Byte-identical
# copies are left alone: they don't claim to show BridgePatcher.
# dHash distance (of 256), measured on this repo: Dortania's screenshots with edited names 1-27,
# BridgePatcher's own screenshots and artwork 40+.
RELABEL_MAX = 30
OWN_NAME_IMG_RE = re.compile(r"(?i)bridge\s?patcher")


def upstream_image_hashes(cache):
    """{blob sha: dHash} of every image in the upstream tree (left side of the audit range)."""
    upstream = re.split(r"\.\.\.?", DIFF_RANGE)[0]
    out = {}
    try:
        rows = git("ls-tree", "-r", "-l", upstream).splitlines()
    except subprocess.CalledProcessError:
        return out
    for row in rows:
        meta, path = row.split("\t", 1)
        _, kind, sha, size = meta.split()
        if kind != "blob" or size == "-" or int(size) > ART_MAX_BYTES or not path.lower().endswith(IMAGE_EXT):
            continue
        key = f"dhash:{sha}"
        if key not in cache:
            data = subprocess.run(["git", "cat-file", "blob", sha], capture_output=True, check=True).stdout
            try:
                cache[key] = format(dhash256(data, (128, 128, 128)), "064x")
            except Exception:
                cache[key] = None
        if cache[key]:
            out[sha] = int(cache[key], 16)
    return out


def find_old_version_in_image(passes):
    hits = []
    for lines in passes:
        for line in lines:
            if OWN_NAME_OLD_VERSION_RE.search(line) and not IMG_COPYRIGHT_RE.search(line) and line not in hits:
                hits.append(line)
    return hits


def tesseract_available():
    try:
        return subprocess.run(["tesseract", "--version"], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def _load_cache():
    import json
    try:
        with open(ART_CACHE, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError):
        return {}


def _save_cache(cache):
    import json
    try:
        with open(ART_CACHE, "w", encoding="utf-8") as fh:
            json.dump(cache, fh)
    except OSError:
        pass


def scan_artwork(head, add):
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 50_000_000
    except ImportError:
        add("warning", "-", "Artwork check skipped: Pillow is not installed")
        return
    known = {k: [int(h, 16) for h in v["hashes"]] for k, v in KNOWN_ART.items()}
    try:
        import numpy  # noqa: F401
        embedded_bits = {k: numpy.stack([_bits(h) for h in known[k]])
                         for k, v in KNOWN_ART.items() if v.get("embedded")}
    except ImportError:
        embedded_bits = {}
        add("warning", "-", "Embedded artwork check skipped: numpy is not installed")
    cache = _load_cache()
    rows = git("ls-tree", "-r", "-l", head).splitlines()
    upstream_hashes = upstream_image_hashes(cache)
    ocr_on = tesseract_available()
    if not ocr_on:
        add("warning", "-", "Image text check skipped: tesseract is not installed")
    else:
        # OCR is slow, so run all uncached images in parallel up front (tesseract is a subprocess).
        from concurrent.futures import ThreadPoolExecutor
        todo = {}
        for row in rows:
            meta, path = row.split("\t", 1)
            _, kind, sha, size = meta.split()
            if (kind == "blob" and not is_self(path) and size != "-" and int(size) <= ART_MAX_BYTES
                    and path.lower().endswith(IMAGE_EXT) and f"ocr{OCR_VERSION}:{sha}" not in cache):
                todo[sha] = path

        def run(sha):
            data = subprocess.run(["git", "cat-file", "blob", sha], capture_output=True, check=True).stdout
            try:
                return sha, ocr_lines(data)
            except Exception:
                return sha, [[], []]

        with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
            for sha, passes in ex.map(run, todo):
                cache[f"ocr{OCR_VERSION}:{sha}"] = passes
    # Dortania's icons inside screenshots: also slow, so all uncached images in parallel up front
    # (OpenCV releases the GIL while matching).
    icon_tpls = load_icon_templates(add)
    icon_ck = lambda sha: f"icon{ICON_VERSION}:{','.join(sorted(icon_tpls))}:{sha}"
    if icon_tpls:
        from concurrent.futures import ThreadPoolExecutor
        todo = {}
        for row in rows:
            meta, path = row.split("\t", 1)
            _, kind, sha, size = meta.split()
            if (kind == "blob" and not is_self(path) and size != "-" and int(size) <= ART_MAX_BYTES
                    and path.lower().endswith(IMAGE_EXT) and icon_ck(sha) not in cache):
                todo[sha] = path

        def run_icons(sha):
            data = subprocess.run(["git", "cat-file", "blob", sha], capture_output=True, check=True).stdout
            try:
                return sha, icon_scores(data, icon_tpls)
            except Exception:
                return sha, {}

        with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
            for sha, scores in ex.map(run_icons, todo):
                cache[icon_ck(sha)] = scores
    for row in rows:
        meta, path = row.split("\t", 1)
        _, kind, sha, size = meta.split()
        if kind != "blob" or is_self(path) or size == "-" or int(size) > ART_MAX_BYTES:
            continue
        low = path.lower()
        if low.endswith(IMAGE_EXT):
            data = subprocess.run(["git", "cat-file", "blob", sha], capture_output=True, check=True).stdout
            try:
                h = dhash256(data, (128, 128, 128))
            except Exception:
                continue  # not a decodable image
            whole = set()
            for key, hashes in known.items():
                d = min(bin(h ^ x).count("1") for x in hashes)
                art = KNOWN_ART[key]
                if d <= ART_COPY_MAX:
                    whole.add(key)
                    add("violation", path, f"Copyrighted artwork: {art['name']}",
                        [f"  Matches {art['holder']}'s artwork (distance {d}/256).",
                         "  Replace it with your own artwork."])
                elif d <= ART_DERIVED_MAX:
                    whole.add(key)
                    add("warning", path, f"Probably contains {art['name']}",
                        [f"  Similar to {art['holder']}'s artwork (distance {d}/256).",
                         "  Check by hand; if it embeds the artwork, replace it."])
            if ocr_on:
                names = find_old_name_in_image(cache.get(f"ocr{OCR_VERSION}:{sha}", [[], []]))
                if names:
                    add("violation", path, "Upstream app name in image (OpenCore Legacy Patcher)",
                        [f"  Text read in the image: {show(n)}" for n in names[:3]] +
                        ["  Screenshots/banners must show BridgePatcher, not Dortania's app name.",
                         "  Retake the screenshot or edit the text. Copyright lines are not affected."])
                folders = find_upstream_folder_in_image(cache.get(f"ocr{OCR_VERSION}:{sha}", [[], []]))
                if folders:
                    add("violation", path, "Upstream project name as a folder/volume name in image (OpenCore-Legacy-Patcher / OCLP)",
                        [f"  Text read in the image: {show(n)}" for n in folders[:3]] +
                        ["  A folder or volume in this screenshot is named after Dortania's project",
                         "  (e.g. \"Opencore-Legacy-Pat...\" in the Finder sidebar, \"Apple-Binaries-OCLP\").",
                         "  Rename it (BridgePatcher, PatcherSupportPkg, ...) and retake the screenshot, or edit the name."])
                authors = find_author_in_image(cache.get(f"ocr{OCR_VERSION}:{sha}", [[], []]))
                if authors:
                    add("violation", path, "Upstream author's name in image (Mykola Grymalyuk)",
                        [f"  Text read in the image: {show(n)}" for n in authors[:3]] +
                        ["  This is a screenshot from Mykola Grymalyuk's Mac (his user name, Mac or account name).",
                         "  The licence forbids using his name to promote BridgePatcher: retake the",
                         "  screenshot on your own Mac or edit the name out. Copyright lines are not affected."])
                versions = find_old_version_in_image(cache.get(f"ocr{OCR_VERSION}:{sha}", [[], []]))
                if versions:
                    add("violation", path, "Dortania's release shown as BridgePatcher's in image",
                        [f"  Text read in the image: {show(n)}" for n in versions[:3]] +
                        ["  BridgePatcher's own versions start at 3.0.0 alpha 4.1; 0.x/1.x/2.x are releases of",
                         "  Dortania's OpenCore Legacy Patcher. This is Dortania's screenshot or banner with the",
                         "  name changed. Use a screenshot of BridgePatcher itself, or remove the image."])
                own_name = [l for ps in cache.get(f"ocr{OCR_VERSION}:{sha}", [[], []]) for l in ps
                            if OWN_NAME_IMG_RE.search(l) and not IMG_COPYRIGHT_RE.search(l)]
                if own_name and upstream_hashes and sha not in upstream_hashes:
                    d, _ = min((bin(h ^ uh).count("1"), us) for us, uh in upstream_hashes.items())
                    if d <= RELABEL_MAX:
                        add("warning", path, "Dortania's screenshot edited to show BridgePatcher",
                            [f"  Nearly identical to an image in Dortania's docs (distance {d}/256), but it reads:",
                             f"  {show(own_name[0])}",
                             "  Dortania's screenshot with the name changed is still Dortania's app, Mac and release.",
                             "  Take a new screenshot of BridgePatcher, or use Dortania's image unchanged and say so."])
            # Best match first; similar icons (the drive icons share the logo) found at the same spot
            # are one finding, not one per icon.
            reported = []
            for key, (score, size_px, x, y) in sorted((cache.get(icon_ck(sha)) or {}).items() if icon_tpls else (),
                                                      key=lambda kv: -kv[1][0]):
                warn_at, violation_at = ICON_THRESHOLDS.get(key, (ICON_WARNING, ICON_VIOLATION))
                if key in whole or score < warn_at:
                    continue
                if any(abs(x - rx) < rs / 2 and abs(y - ry) < rs / 2 for rx, ry, rs in reported):
                    continue
                reported.append((x, y, size_px))
                whole.add(key)  # don't report the same icon again from the dHash search below
                name = UPSTREAM_ICONS[key][1]
                where = f"  Found at x={x}, y={y}, about {size_px}px (match {score:.2f})."
                if score >= violation_at:
                    add("violation", path, f"Contains {name}",
                        [where, "  Dortania's artwork is part of this screenshot/graphic, e.g. small, dimmed or in the Dock.",
                         "  Retake the screenshot with BridgePatcher's own icons, or replace the icon."])
                else:
                    add("warning", path, f"Might contain {name}",
                        [where, "  Check by hand; if it shows the icon, replace it."])
            if not embedded_bits:
                continue
            if sha in cache:
                hits = {k: tuple(v) for k, v in cache[sha].items()}
            else:
                try:
                    hits = find_embedded(data, embedded_bits)
                except Exception:
                    hits = {}
                cache[sha] = hits
            for key, (d, size_px, x, y) in hits.items():
                if key in whole or d > EMBED_WARN_MAX:
                    continue
                art = KNOWN_ART[key]
                where = f"  Found inside the image at x={x}, y={y}, about {size_px}px (distance {d}/256)."
                if d <= EMBED_COPY_MAX:
                    add("violation", path, f"Contains copyrighted artwork: {art['name']}",
                        [where, f"  {art['holder']}'s artwork is part of this screenshot/graphic.",
                         "  Retake the screenshot with your own icon, crop it out or remove the image."])
                else:
                    add("warning", path, f"Might contain {art['name']}",
                        [where, "  Check by hand; if it shows the artwork, replace it."])
        elif low.endswith(TEXT_EXT):
            text = git("cat-file", "blob", sha)
            urls = sorted(set(m.group(0) for m in HOTLINK_RE.finditer(text)))
            if urls:
                add("violation", path, "Dortania artwork used from Dortania's servers",
                    [f"- {u}" for u in urls[:10]])
            invites = [(n, l) for n, l in enumerate(text.splitlines(), 1) if UPSTREAM_DISCORD_RE.search(l)]
            if invites:
                add("violation", path, "Link to Dortania's Discord server (OpenCore Patcher Paradise)",
                    [f"  line {n}: {show(l)}" for n, l in invites[:5]] + (["  …"] if len(invites) > 5 else []) +
                    ["  Don't send BridgePatcher users to the upstream project's Discord for support.",
                     "  Link our GitHub Discussions (https://github.com/bridgepatcher/BridgePatcher/discussions) instead."])
            # The licence pages themselves name Dortania's project on purpose - they must stay as they are.
            if low.endswith(OLD_NAME_EXT) and not LICENSE_FILE_RE.search(path):
                old, upstream, legacy_app, abbrev, upstream_app, old_version = [], [], [], [], [], []
                for n, l in enumerate(text.splitlines(), 1):
                    bare = URL_RE.sub(" ", l)
                    if OLD_NAME_RE.search(l):
                        old.append((n, l))
                    # Exemptions are checked without URLs too: a link to Dortania's repo on the line
                    # doesn't make "the OpenCore Legacy Patcher app" mean Dortania's project.
                    elif UPSTREAM_NAME_RE.search(l) and not UPSTREAM_NAME_OK_RE.search(bare):
                        upstream.append((n, l))
                    if LEGACY_APP_RE.search(l) and not LEGACY_APP_OK_RE.search(l):
                        legacy_app.append((n, l))
                    if OCLP_RE.search(OCLP_OTHER_RE.sub(" ", bare)) and not OCLP_OK_RE.search(bare):
                        abbrev.append((n, l))
                    if UPSTREAM_APP_RE.search(l) and not UPSTREAM_APP_OK_RE.search(bare):
                        upstream_app.append((n, l))
                    if OWN_NAME_OLD_VERSION_RE.search(bare):
                        old_version.append((n, l))
                if abbrev:
                    add("violation", path, "Abbreviation OCLP used for this project",
                        [f"  line {n}: {show(l)}" for n, l in abbrev[:5]] + (["  …"] if len(abbrev) > 5 else []) +
                        ["  OCLP is Dortania's name for its app. Say BridgePatcher, or \"Dortania's OCLP 0.2.5\" when",
                         "  Dortania's release is meant. Identifiers like OCLP-Version are fine."])
                if upstream_app:
                    add("violation", path, "Dortania's app (OpenCore-Patcher.app) presented as this app",
                        [f"  line {n}: {show(l)}" for n, l in upstream_app[:5]] +
                        (["  …"] if len(upstream_app) > 5 else []) +
                        ["  The app is /Applications/BridgePatcher.app (executable Contents/MacOS/BridgePatcher)."])
                if old_version:
                    add("violation", path, "Dortania's release numbers presented as BridgePatcher's",
                        [f"  line {n}: {show(l)}" for n, l in old_version[:5]] +
                        (["  …"] if len(old_version) > 5 else []) +
                        ["  BridgePatcher's own versions start at 3.0.0 alpha 4.1; 0.x/1.x/2.x are releases of",
                         "  Dortania's OpenCore Legacy Patcher. Say \"Dortania's OpenCore Legacy Patcher 2.1.0\"."])
                if old:
                    add("violation", path, "Former project name (OpenCore (Legacy) Patcher T2 / OCLP-T2)",
                        [f"  line {n}: {show(l)}" for n, l in old[:5]] + (["  …"] if len(old) > 5 else []) +
                        ["  Use BridgePatcher instead; the old name is treated as a typosquat."])
                if legacy_app:
                    add("warning", path, "Former app name (OpenCore-Patcher-T2)",
                        [f"  line {n}: {show(l)}" for n, l in legacy_app[:5]] +
                        (["  …"] if len(legacy_app) > 5 else []) +
                        ["  The app is BridgePatcher.app (executable BridgePatcher) now. The install folder",
                         "  .../OpenCore-Patcher-T2/ and OpenCore-Patcher-T2.pkg keep their names."])
                if upstream:
                    add("violation", path, "Dortania's app name used for this project (OpenCore Legacy Patcher)",
                        [f"  line {n}: {show(l)}" for n, l in upstream[:5]] + (["  …"] if len(upstream) > 5 else []) +
                        ["  Say BridgePatcher, or make clear it is Dortania's project",
                         "  (e.g. \"Dortania's OpenCore Legacy Patcher 2.0.0\"). Copyright/credit lines are fine."])
    _save_cache(cache)


YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, check=True,
                          encoding="utf-8", errors="replace").stdout


def norm(line):
    """Normalise whitespace and years so a pure year bump isn't reported."""
    return YEAR_RE.sub("YYYY", " ".join(line.split())).lower()


def core(line):
    """The notice itself, from where it starts up to the end of the string/tag it sits in,
    so `str = "Copyright © 2020 X"` and `<string>Copyright © X</string>` reduce to the notice."""
    m = COPYRIGHT_RE.search(line)
    return norm(re.split(r"[\"'<]", line[m.start():] if m else line)[0])


def show(line):
    line = line.strip().replace("`", "'")
    return line if len(line) <= 200 else line[:200] + "…"


def parse_diff(text):
    files, cur, in_hunk = [], None, False
    for line in text.splitlines():
        if line.startswith("diff --git "):
            cur = {"old": None, "new": None, "add": [], "rem": [], "deleted": False}
            files.append(cur)
            in_hunk = False
        elif cur is None:
            continue
        elif line.startswith("@@"):
            in_hunk = True
        elif not in_hunk:
            if line.startswith("deleted file mode"):
                cur["deleted"] = True
            elif line.startswith("--- "):
                cur["old"] = None if line[4:] == "/dev/null" else line[6:]
            elif line.startswith("+++ "):
                cur["new"] = None if line[4:] == "/dev/null" else line[6:]
        elif line.startswith("+"):
            cur["add"].append(line[1:])
        elif line.startswith("-"):
            cur["rem"].append(line[1:])
    return files


def main():
    diff = git("diff", "-M", "-U0", "--no-color", "--no-ext-diff", DIFF_RANGE)
    findings = []  # (severity, path, title, [detail lines])
    allow = load_allow()
    relocated = load_relocated()

    def add(sev, path, title, details=()):
        findings.append((sev, path, title, list(details)))

    for f in parse_diff(diff):
        path = f["new"] or f["old"]
        if not path or is_self(path):
            continue
        is_license = bool(LICENSE_FILE_RE.search(path))
        rem_cr = [l for l in f["rem"] if COPYRIGHT_RE.search(l)]
        add_cr = [l for l in f["add"] if COPYRIGHT_RE.search(l)]

        if f["deleted"]:
            dest = next((d for p, d in relocated if fnmatch.fnmatch(path, p)), None)
            if dest:
                if is_license or rem_cr:
                    add("info", path, "Deleted here, notices relocated", [f"  Now at: {dest}"])
                continue
            if is_license:
                add("violation", path, "License file deleted")
            elif rem_cr and not any(fnmatch.fnmatch(path, a) for a in allow):
                add("warning", path, "File with an upstream copyright notice was deleted",
                    ["  Fine if the code is really gone. Not fine if it was moved",
                     "  or re-added elsewhere without the notice.",
                     f"  If the deletion is intentional, add the path to {ALLOW_FILE}."])
            continue

        # 1) Upstream copyright notice removed or replaced (any holder; year bumps ignored)
        # A notice counts as kept if its text still appears in some added line, so
        # "© 2020 Dortania" -> "© 2020 Dortania · fork © 2026 Albert" is fine.
        added_n = [norm(l) for l in f["add"]]
        removed_n = [norm(l) for l in f["rem"]]
        lost = [l for l in rem_cr if not any(core(l) in a for a in added_n)]
        new = [l for l in add_cr if not any(core(l) in r for r in removed_n)]
        if lost:
            add("violation", path,
                f"Upstream copyright notice {'replaced' if new else 'removed'}",
                [f"- {show(l)}" for l in lost] + [f"+ {show(l)}" for l in new])
        elif new:
            add("info", path, "Additional copyright added (upstream notice kept)",
                [f"+ {show(l)}" for l in new])

        # 2) SPDX identifier changed or removed
        rem_ids = Counter(m.group(1) for l in f["rem"] if (m := SPDX_RE.search(l)))
        add_ids = Counter(m.group(1) for l in f["add"] if (m := SPDX_RE.search(l)))
        if rem_ids - add_ids:
            add("violation", path, "SPDX license identifier changed or removed",
                [f"- {i}" for i in rem_ids - add_ids] + [f"+ {i}" for i in add_ids - rem_ids])

        # 3) License text itself changed (year bumps are ignored)
        if is_license:
            body = lambda ls: [l for l in ls if l.strip() and not COPYRIGHT_RE.search(l)]
            rem_n = Counter(norm(l) for l in body(f["rem"]))
            add_n = Counter(norm(l) for l in body(f["add"]))
            gone = [l for l in body(f["rem"]) if (rem_n - add_n)[norm(l)]]
            if gone:
                add("violation", path, "License text removed or altered",
                    [f"- {show(l)}" for l in gone[:15]] + (["  …"] if len(gone) > 15 else []))
            elif add_n - rem_n:
                add("info", path, "Lines added to license file",
                    [f"+ {show(l)}" for l in f["add"] if l.strip()][:15])


    # 4) Known copyrighted artwork anywhere in the audited tree
    scan_artwork(re.split(r"\.\.\.?", DIFF_RANGE)[-1], add)

    v = [x for x in findings if x[0] == "violation"]
    w = [x for x in findings if x[0] == "warning"]
    i = [x for x in findings if x[0] == "info"]

    # One line per violation, so the workflow can tell which ones a PR adds vs. which are
    # already on the base branch (only PR-added violations may auto-close a fork PR).
    if os.environ.get("VIOLATIONS_LIST"):
        with open(os.environ["VIOLATIONS_LIST"], "w", encoding="utf-8") as fh:
            fh.write("".join(f"{title} — {path}\n" for _, path, title, _ in v))

    out = [MARKER, "## 🛡️ License Guard", ""]
    if not v and not w:
        out.append(f"✅ No changes found that would affect upstream copyright notices or license text (`{DIFF_RANGE}`), and no known copyrighted artwork.")
    else:
        out.append(f"Checked `{DIFF_RANGE}`: **{len(v)} violation(s)**, {len(w)} warning(s), {len(i)} info.")
    def section(items):
        res = []
        for _, path, title, details in items:
            res.append(f"**{title}** — `{path}`")
            if details:
                res += ["```diff", *details, "```"]
        return res

    for sev, emoji, items in (("Violations", "❌", v), ("Warnings", "⚠️", w)):
        if items:
            out += ["", f"### {emoji} {sev}", *section(items)]
    if i:
        # Info is your own additions next to kept notices and relocated files - collapsed, nothing to fix.
        out += ["", f"<details><summary>ℹ️ Info ({len(i)}): copyright lines you added next to kept "
                "upstream notices, relocated files - nothing to fix</summary>", "", *section(i), "", "</details>"]
    out += ["", "<details><summary>Why this matters</summary>", "",
            f"{HOLDER}'s code is under licenses that require keeping every existing copyright notice and "
            "the license text in redistributed source (e.g. BSD 3-Clause, clause 1). Adding your own "
            "copyright line *alongside* the existing ones is fine; replacing or removing them is not. "
            "Year bumps like `2020-2024` → `2020-2026` are ignored.", "",
            "Artwork such as Dortania's OpenCore Legacy Patcher icon or Apple's System Settings icon "
            "is not covered by the code license and must not be shipped or hotlinked; use your "
            "own artwork. Screenshots and banners must not show Dortania's app name or icons either (including "
            "the main-menu button icons such as \"Build and Install OpenCore\").", "",
            "The licence also forbids using the upstream name to endorse or promote the fork, so pages, titles and "
            "screenshots must say BridgePatcher, not \"OpenCore Legacy Patcher\" (or the former name OCLP-T2). "
            "Naming Dortania's project when crediting it or referring to its releases is fine. Calling Dortania's "
            "app or releases BridgePatcher's is not: \"OCLP\" for this project, Dortania's OpenCore-Patcher.app, "
            "\"BridgePatcher 0.6.8\" (a Dortania version number) or Dortania's screenshots with the name "
            "edited to BridgePatcher.", "",
            "For the same reason, pages must not send users to Dortania's Discord server (OpenCore Patcher "
            "Paradise) for help with BridgePatcher; link BridgePatcher's own support channels instead.",
            "", "</details>"]

    report = "\n".join(out) + "\n"
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write(report)
    print(report)
    for var, text in (("GITHUB_OUTPUT", f"violations={len(v)}\nwarnings={len(w)}\n"),
                      ("GITHUB_STEP_SUMMARY", report)):
        if os.environ.get(var):
            with open(os.environ[var], "a", encoding="utf-8") as fh:
                fh.write(text)


if __name__ == "__main__":
    main()
