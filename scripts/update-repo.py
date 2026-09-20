#!/usr/bin/env python3
"""Build a Cydia / Sileo / Zebra APT repo from local Theos packages.

Credit: Jinken Nguyen - 1989
Donate: MB Bank - 0345140889 - Nguyễn Tiến Triều
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CODE = Path.home() / "Documents" / "code"
DESKTOP = Path.home() / "Desktop"
SESSION_IMAGES = Path.home() / ".grok/sessions/%2FUsers%2Fjinkennguyen/01a0a918-7167-7450-a825-d48dee73e4af/images"
VIETQR_SRC = Path("/tmp/jinken-assets/vietqr.png")

ARCH_LABEL = {
    "iphoneos-arm": "rootful",
    "iphoneos-arm64": "rootless",
    "iphoneos-arm64e": "RootHide",
}

BLURBS = {
    "com.jinkennguyen.adshield": (
        "Chặn quảng cáo toàn hệ thống: app, Safari, WebView và video.",
        "System-wide ad blocker for apps, Safari, WebViews and video ads.",
    ),
    "com.jinkennguyen.adveil": (
        "Chặn quảng cáo toàn hệ thống cho máy jailbreak.",
        "System-wide ad blocker for jailbroken iOS.",
    ),
    "com.jinkennguyen.aether": (
        "Tùy biến iOS: thanh trạng thái, Home, Dock, Lock Screen, Control Center — 110+ tuỳ chọn.",
        "Customize jailbroken iOS: status bar, Home, Dock, Lock Screen, Control Center — 110+ options.",
    ),
    "com.carsplit.tweak": (
        "Chia đôi màn hình CarPlay cho mọi app iOS.",
        "Split-screen CarPlay for every iOS app.",
    ),
    "com.jinkennguyen.duocompare": (
        "So sánh iPhone Duo với mọi máy gập trên thị trường.",
        "iPhone Duo vs every foldable on the market.",
    ),
    "com.jinkennguyen.duoframe": (
        "Màn hình chính iOS 27: khung kính lỏng cho status, icon grid và dock.",
        "iOS 27 Home Screen: liquid-glass frames for status, icon grid and dock.",
    ),
    "com.jinkennguyen.haven": (
        "Whitelist app để tweak khác không inject vào. App trong danh sách chạy kiểu safe mode.",
        "Whitelist apps so other tweaks never inject into them.",
    ),
    "com.jinkennguyen.isleglass": (
        "Giả lập Dynamic Island kích thước iPhone 18 Pro. Ghim app, nhạc, sạc, hẹn giờ.",
        "Simulated Dynamic Island at iPhone 18 Pro size. Pin apps, music, charging, timer.",
    ),
    "com.jinkennguyen.lookglass": (
        "Ô tìm kính lỏng trên Home. Google, Wikipedia, nhạc, phim. YouTube tự phát, nghe nền, mở lại bằng nút trên Home.",
        "Liquid-glass Home search. Google, Wikipedia, music, films. YouTube autoplays; background audio restores from Home.",
    ),
    "com.jinkennguyen.slapios": (
        "Vỗ, gõ, lắc iPhone thì máy kêu vui. 120 hiệu ứng, 8 gói tiếng.",
        "Slap, tap, shake the iPhone and it groans. 120 effects, 8 sound packs.",
    ),
    "com.jinkennguyen.noxframe": (
        "Chụp hình và quay phim khi màn hình tắt. Nút nguồn làm màn đen, Camera vẫn chạy.",
        "Take photos and record video with the screen off. Side button blanks the display; Camera stays live.",
    ),
    "com.jinkennguyen.snowglass": (
        "Theme Snowboard kính lỏng: icon squircle iOS 26, viền sáng.",
        "Liquid-glass SnowBoard icon theme with iOS 26 squircles.",
    ),
    "com.jinkennguyen.luminacc": (
        "Studio Control Center: module, layout, kính lỏng.",
        "Control Center studio: modules, layout, liquid glass.",
    ),
    "com.jinkennguyen.matteglass": (
        "Hiệu ứng màn hình: matte, e-ink, giấy, gập trang iPhone Duo.",
        "Screen looks: matte, e-ink, paper, iPhone Duo page fold.",
    ),
    "com.jinkennguyen.miraos": (
        "Desktop kiểu macOS trên iPhone. App mở bên trong MiraOS.",
        "macOS-style desktop on iPhone. Apps open inside MiraOS.",
    ),
    "com.jinkennguyen.newsbar": (
        "Ticker tin tức sống trên thanh trạng thái jailbreak.",
        "Live news ticker on the jailbreak status bar.",
    ),
    "com.jinkennguyen.pitchbar": (
        "Tỷ số bóng đá sống trên thanh trạng thái. BXH, thống kê, nhắc trận.",
        "Live football scores on the status bar. Tables, stats, reminders.",
    ),
    "com.t27.backport": (
        "Mang tính năng iOS 27 xuống máy jailbreak cũ. Bật/tắt từng mục.",
        "Bring iOS 27 features to older jailbroken iOS. Toggle each feature.",
    ),
    "com.jinkennguyen.trungthulan": (
        "Diễu hành lân Trung Thu chân thực trên iOS jailbreak.",
        "Photoreal Vietnamese Mid-Autumn lion-dance parade on jailbroken iOS.",
    ),
    "com.jinkennguyen.trungthuplay": (
        "Mini-game Trung Thu arcade. Nhân vật retro, nhạc chiptune, hướng dẫn từng trò.",
        "Arcade Mid-Autumn mini-games. Retro characters, chiptune SFX, how-to before each game.",
    ),
}

FEATURED = [
    "com.jinkennguyen.duoframe",
    "com.jinkennguyen.lookglass",
    "com.jinkennguyen.slapios",
]

DEB_NAME_RE = re.compile(
    r"^(?P<pkg>.+)_(?P<ver>[^_]+)_(?P<arch>iphoneos-arm(?:64e?)?)\.deb$"
)


def load_conf(path: Path) -> dict[str, str]:
    conf: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        conf[k.strip()] = v.strip()
    return conf


def version_key(ver: str) -> tuple:
    parts = []
    for chunk in re.split(r"[.-]", ver):
        parts.append((0, int(chunk)) if chunk.isdigit() else (1, chunk))
    return tuple(parts)


def parse_control(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    key = None
    for line in text.splitlines():
        if not line:
            continue
        if line[0] in " \t" and key:
            fields[key] += "\n" + line[1:]
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            fields[key] = val.strip()
    return fields


def dpkg_fields(deb: Path) -> dict[str, str]:
    out = subprocess.check_output(["dpkg-deb", "-f", str(deb)], text=True, errors="replace")
    return parse_control(out)


def collect_latest_debs(allow: set[str] | None = None) -> dict[tuple[str, str], Path]:
    latest: dict[tuple[str, str], tuple] = {}
    search_roots = list(CODE.glob("*/packages")) + [DESKTOP]
    for folder in search_roots:
        if not folder.is_dir():
            continue
        for deb in folder.glob("*.deb"):
            m = DEB_NAME_RE.match(deb.name)
            if m:
                pkg, ver, arch = m.group("pkg"), m.group("ver"), m.group("arch")
            else:
                try:
                    fields = dpkg_fields(deb)
                except subprocess.CalledProcessError:
                    continue
                pkg = fields.get("Package")
                ver = fields.get("Version")
                arch = fields.get("Architecture")
                if not (pkg and ver and arch):
                    continue
            if allow and pkg not in allow:
                continue
            key = (pkg, arch)
            cand = (version_key(ver), deb.stat().st_mtime, deb)
            if key not in latest or cand > latest[key]:
                latest[key] = cand
    return {k: v[2] for k, v in latest.items()}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_png(src: Path, dest: Path, size: int | None = None, crop_frac: float = 0.0) -> None:
    im = Image.open(src).convert("RGBA")
    if crop_frac:
        w, h = im.size
        dx, dy = int(w * crop_frac), int(h * crop_frac)
        im = im.crop((dx, dy, w - dx, h - dy))
    if size:
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "PNG", optimize=True)


def copy_banner(src: Path, dest: Path, size: tuple[int, int]) -> None:
    im = Image.open(src).convert("RGB")
    im = im.resize(size, Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=90, optimize=True)


def project_dir_for(pkg: str) -> Path | None:
    for p in CODE.iterdir():
        control = p / "control"
        if control.is_file() and f"Package: {pkg}" in control.read_text(encoding="utf-8", errors="replace"):
            return p
    aliases = {
        "com.carsplit.tweak": "CarSplit",
        "com.t27.backport": "T27",
        "com.jinkennguyen.trungthulan": "TrungThuLan",
        "com.jinkennguyen.trungthuplay": "TrungThuPlay",
    }
    name = aliases.get(pkg)
    if name and (CODE / name).is_dir():
        return CODE / name
    return None


def find_icon(pkg: str) -> Path | None:
    proj = project_dir_for(pkg)
    if not proj:
        return None
    for rel in (
        "prefs/Resources/icon@3x.png",
        "prefs/Resources/icon@2x.png",
        "prefs/Resources/icon.png",
        "layout/Library/PreferenceBundles/*/icon@3x.png",
    ):
        hits = list(proj.glob(rel))
        if hits:
            return hits[0]
    return None


def read_changelog(pkg: str) -> str:
    proj = project_dir_for(pkg)
    if not proj:
        return ""
    for name in ("CHANGELOG.md", "HUONG_DAN.txt"):
        p = proj / name
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            return text.strip()[:8000]
    return ""


def donate_thanks(conf: dict) -> dict[str, str]:
    bank = f"{conf['DONATE_BANK']} · {conf['DONATE_ACCOUNT']} · {conf['DONATE_NAME']}"
    vi = (
        "Cảm ơn bạn đã tin dùng tweak miễn phí. Nếu thấy hữu ích, một chút ủng hộ "
        "giúp mình giữ repo chạy và ra bản mới — không bắt buộc, chỉ khi bạn vui lòng."
    )
    en = (
        "Thank you for using this free tweak. If it helped, a small donation keeps "
        "the repo online and updates coming. No pressure — using it already means a lot."
    )
    md = (
        f"{vi}\n\n{en}\n\n"
        f"- Ngân hàng: **{conf['DONATE_BANK']}**\n"
        f"- STK: **{conf['DONATE_ACCOUNT']}**\n"
        f"- Chủ TK: **{conf['DONATE_NAME']}**\n"
        f"- Nội dung: `Donate Jinken Nguyen {conf['YEAR']}`\n\n"
        f"Quét VietQR trên [trang repo]({conf['BASE_URL']}#donate). Cảm ơn bạn rất nhiều."
    )
    html_block = (
        f"<strong>Cảm ơn bạn</strong><br>{html_escape(vi)}<br><br>"
        f"{html_escape(en)}<br><br>"
        f"{html_escape(bank)}<br>"
        "Quét VietQR trên trang repo hoặc chuyển khoản MB Bank."
    )
    return {"vi": vi, "en": en, "bank": bank, "md": md, "html": html_block}


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def depiction_html(pkg: str, meta: dict, conf: dict, vi: str, en: str, changelog: str) -> str:
    name = meta.get("Name", pkg)
    ver = meta.get("Version", "")
    author = conf["AUTHOR"]
    thanks = donate_thanks(conf)
    log_html = ""
    if changelog:
        log_html = "<pre>" + html_escape(changelog[:4000]) + "</pre>"
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_escape(name)} {html_escape(ver)}</title>
<style>
body{{margin:0;padding:16px;font:16px/1.5 -apple-system,BlinkMacSystemFont,sans-serif;background:#07080f;color:#eef2ff}}
h1{{font-size:22px;margin:0 0 4px}}
.sub{{color:#93c5fd;margin:0 0 12px}}
.card{{background:#111827;border-radius:16px;padding:16px;border:1px solid rgba(255,255,255,.08)}}
.donate{{margin-top:12px;padding:12px 14px;border-radius:12px;background:#0b1220;border:1px solid rgba(56,189,248,.35)}}
.donate strong{{color:#7dd3fc}}
pre{{white-space:pre-wrap;font-size:13px;color:#cbd5e1}}
a{{color:#7dd3fc}}
hr{{border:0;border-top:1px solid #1f2937;margin:18px 0}}
</style>
</head>
<body>
<div class="card">
<h1>{html_escape(name)} {html_escape(ver)}</h1>
<p class="sub">Credit: {html_escape(author)} · iOS 14+ · {html_escape(meta.get("Section","Tweaks"))}</p>
<p>{html_escape(vi)}</p>
<p>{html_escape(en)}</p>
<div class="donate">
{thanks['html']}
</div>
</div>
<hr>
<p>Gói: rootless · rootful · RootHide (khi có <code>iphoneos-arm64e</code>).</p>
<p>Sau khi cài: <strong>Respring</strong>, mở <strong>Cài đặt → {html_escape(name)}</strong>.</p>
{log_html}
<p><a href="../../#donate">← Jinken Repo · Donate</a></p>
</body>
</html>
"""


def sileo_json(pkg: str, meta: dict, conf: dict, vi: str, en: str, changelog: str) -> dict:
    name = meta.get("Name", pkg)
    ver = meta.get("Version", "")
    author = conf["AUTHOR"]
    thanks = donate_thanks(conf)
    md = (
        f"**{name}** — {vi}\n\n{en}\n\n"
        f"**Phiên bản / Version:** {ver}  \n"
        f"**Tác giả / Author:** {author}  \n"
        f"**iOS:** 14+  \n"
        f"**Gói:** rootless · rootful · RootHide (`iphoneos-arm64e`)\n\n"
        f"Sau khi cài: **Respring**, mở **Cài đặt → {name}**.\n\n"
        f"{thanks['vi']}\n\n{thanks['en']}"
    )
    views = [
        {"class": "DepictionHeaderView", "title": name, "useBoldText": True},
        {"class": "DepictionSubheaderView", "title": author, "useBoldText": False},
        {"class": "DepictionSeparatorView"},
        {
            "class": "DepictionMarkdownView",
            "markdown": md,
            "useSpacing": True,
            "useRawFormat": False,
        },
        {"class": "DepictionSpacerView", "spacing": 8},
        {"class": "DepictionTableTextView", "title": "Version", "text": ver},
        {"class": "DepictionTableTextView", "title": "iOS", "text": "14.0+"},
        {"class": "DepictionTableTextView", "title": "Author", "text": author},
        {"class": "DepictionTableTextView", "title": "Section", "text": meta.get("Section", "Tweaks")},
        {"class": "DepictionTableTextView", "title": "Price", "text": "Free"},
        {"class": "DepictionSpacerView", "spacing": 12},
        {
            "class": "DepictionMarkdownView",
            "markdown": f"**Cảm ơn bạn / Thank you**  \n{thanks['vi']}  \n\n{thanks['en']}  \n\n{thanks['bank']}",
            "useSpacing": True,
        },
    ]
    changelog_views = [
        {"class": "DepictionHeaderView", "title": f"{ver}", "useBoldText": True},
        {
            "class": "DepictionMarkdownView",
            "markdown": changelog[:3500] if changelog else "Xem GitHub repo / see the GitHub repo.",
            "useSpacing": True,
            "useRawFormat": False,
        },
    ]
    return {
        "minVersion": "0.4",
        "class": "DepictionTabView",
        "tintColor": "#38BDF8",
        "headerImage": f"{conf['BASE_URL'].rstrip('/')}/assets/banner.jpg",
        "tabs": [
            {"tabname": "Details", "class": "DepictionStackView", "views": views},
            {"tabname": "Changelog", "class": "DepictionStackView", "views": changelog_views},
            {
                "tabname": "Donate",
                "class": "DepictionStackView",
                "views": [
                    {"class": "DepictionHeaderView", "title": "Cảm ơn bạn", "useBoldText": True},
                    {"class": "DepictionSubheaderView", "title": author, "useBoldText": False},
                    {
                        "class": "DepictionMarkdownView",
                        "markdown": thanks["md"],
                        "useSpacing": True,
                    },
                ],
            },
        ],
    }


def write_index(packages: dict[str, dict], conf: dict) -> None:
    cards = []
    for pkg, info in sorted(packages.items(), key=lambda kv: kv[1]["Name"].lower()):
        arches = " · ".join(ARCH_LABEL.get(a, a) for a in info["archs"])
        vi, en = BLURBS.get(pkg, (info.get("blurb", ""), ""))
        cards.append(
            f"""
<article class="card">
  <h3>{html_escape(info['Name'])}</h3>
  <p class="meta">{html_escape(info['Version'])} · {html_escape(arches)}</p>
  <p>{html_escape(vi)}</p>
  <p class="en">{html_escape(en)}</p>
  <a class="more" href="depictions/{html_escape(pkg)}/">Chi tiết</a>
</article>"""
        )
    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jinken Repo — Jinken Nguyen - 1989</title>
<meta name="description" content="Cydia / Sileo / Zebra repo. Credit: Jinken Nguyen - 1989. Donate: MB Bank 0345140889 Nguyễn Tiến Triều.">
<link rel="icon" href="CydiaIcon.png">
<style>
:root {{
  --bg:#07080f; --card:#101826cc; --line:rgba(255,255,255,.1);
  --text:#eef2ff; --muted:#93c5fd; --accent:#38bdf8; --good:#34d399;
}}
* {{box-sizing:border-box}}
body {{
  margin:0; font:16px/1.5 -apple-system,BlinkMacSystemFont,"SF Pro Text",sans-serif;
  background:var(--bg); color:var(--text);
}}
.hero {{
  position:relative; min-height:280px; padding:48px 20px 32px;
  background:url("assets/banner.jpg") center/cover no-repeat;
}}
.hero::after {{
  content:""; position:absolute; inset:0;
  background:linear-gradient(180deg, rgba(7,8,15,.25), rgba(7,8,15,.92));
}}
.hero-inner {{position:relative; z-index:1; max-width:980px; margin:0 auto}}
.badge {{
  display:inline-block; padding:4px 10px; border-radius:999px;
  border:1px solid rgba(56,189,248,.4); color:var(--accent); font-size:12px;
  letter-spacing:.08em; text-transform:uppercase;
}}
h1 {{font-size:clamp(28px,5vw,44px); margin:12px 0 6px}}
.sub {{color:var(--muted); max-width:640px}}
.wrap {{max-width:980px; margin:0 auto; padding:0 20px 64px}}
.row {{display:flex; flex-wrap:wrap; gap:10px; margin:18px 0 8px}}
.btn {{
  display:inline-flex; align-items:center; justify-content:center;
  padding:12px 16px; border-radius:12px; text-decoration:none; font-weight:650;
  border:1px solid var(--line); color:var(--text); background:#0b1220aa;
}}
.btn.primary {{background:var(--accent); color:#042033; border-color:transparent}}
.grid {{display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:14px; margin-top:18px}}
.card {{
  background:var(--card); backdrop-filter:blur(16px);
  border:1px solid var(--line); border-radius:16px; padding:16px;
}}
.card h3 {{margin:0 0 4px; font-size:18px}}
.meta {{color:var(--muted); font-size:13px; margin:0 0 8px}}
.en {{color:#cbd5e1; font-size:14px}}
.more {{color:var(--accent); text-decoration:none; font-weight:600}}
.donate {{
  display:grid; grid-template-columns:180px 1fr; gap:20px; align-items:center;
}}
.donate img {{width:180px; background:#fff; border-radius:12px}}
.copy {{
  cursor:pointer; border:1px dashed rgba(56,189,248,.5); border-radius:10px;
  padding:8px 10px; display:inline-block; margin:4px 0; color:var(--accent);
}}
h2 {{margin:36px 0 10px}}
footer {{color:#64748b; font-size:13px; margin-top:40px}}
code.src {{
  display:block; background:#0b1220; border-radius:10px; padding:10px 12px;
  overflow:auto; color:#7dd3fc; margin:8px 0 16px;
}}
@media (max-width:640px) {{
  .donate {{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
<header class="hero">
  <div class="hero-inner">
    <span class="badge">Cydia · Sileo · Zebra</span>
    <h1>Jinken Repo</h1>
    <p class="sub">Tweaks jailbreak bởi <strong>Jinken Nguyen - 1989</strong>. Rootless, rootful và RootHide. Miễn phí — cảm ơn bạn đã dùng. Nếu thích, một chút ủng hộ giúp mình làm tiếp.</p>
    <div class="row">
      <a class="btn primary" id="add-sileo" href="#">Thêm vào Sileo</a>
      <a class="btn" id="add-zebra" href="#">Thêm vào Zebra</a>
      <a class="btn" href="#donate">Donate</a>
    </div>
  </div>
</header>
<main class="wrap">
  <h2>Thêm source</h2>
  <p>Sileo / Zebra / Cydia → Sources → + → dán URL:</p>
  <code class="src" id="source-url">{html_escape(conf['BASE_URL'])}</code>
  <p class="en">Add this URL as a package source, then install one package per tweak matching your jailbreak (rootless / rootful / RootHide).</p>

  <h2>Tweaks</h2>
  <div class="grid">
    {''.join(cards)}
  </div>

  <h2 id="credit">Credit</h2>
  <div class="card">
    <p><strong>Tác giả / Author:</strong> Jinken Nguyen - 1989</p>
    <p><strong>Maintainer:</strong> Jinken Nguyen - 1989</p>
    <p>Mọi tweak trong repo này do Jinken Nguyen - 1989 phát triển. Không liên kết với Apple.</p>
    <p class="en">All tweaks in this repo are by Jinken Nguyen - 1989. Not affiliated with Apple.</p>
  </div>

  <h2 id="donate">Donate</h2>
  <div class="card donate">
    <img src="assets/vietqr.png" alt="VietQR MB Bank 0345140889 Nguyễn Tiến Triều">
    <div>
      <p>Cảm ơn bạn đã tin dùng tweak miễn phí. Nếu thấy hữu ích, một chút ủng hộ giúp mình giữ repo chạy và ra bản mới — không bắt buộc, chỉ khi bạn vui lòng.</p>
      <p class="en">Thank you for using these free tweaks. A small donation keeps the repo online. No pressure — using them already means a lot.</p>
      <p><strong>Ngân hàng:</strong> {html_escape(conf['DONATE_BANK'])}<br>
      <strong>Chủ TK:</strong> {html_escape(conf['DONATE_NAME'])}<br>
      <strong>STK:</strong> <span class="copy" data-copy="{html_escape(conf['DONATE_ACCOUNT'])}">{html_escape(conf['DONATE_ACCOUNT'])} · copy</span><br>
      <strong>Nội dung:</strong> <span class="copy" data-copy="Donate Jinken Nguyen {html_escape(conf['YEAR'])}">Donate Jinken Nguyen {html_escape(conf['YEAR'])} · copy</span></p>
      <p class="en">MB Bank · {html_escape(conf['DONATE_ACCOUNT'])} · {html_escape(conf['DONATE_NAME_ASCII'])}</p>
    </div>
  </div>

  <footer>
    Credit: Jinken Nguyen - 1989 · Donate: {html_escape(conf['DONATE_BANK'])} {html_escape(conf['DONATE_ACCOUNT'])} {html_escape(conf['DONATE_NAME'])}<br>
    MIT License · iOS 14+ · rootless / rootful / RootHide
  </footer>
</main>
<script>
const base = location.origin + location.pathname.replace(/index\\.html$/, "").replace(/\\/$/, "");
const src = base + "/";
document.getElementById("source-url").textContent = src;
document.getElementById("add-sileo").href = "sileo://source/" + src;
document.getElementById("add-zebra").href = "zbra://sources/add/" + src;
document.querySelectorAll(".copy").forEach(el => {{
  el.addEventListener("click", async () => {{
    try {{
      await navigator.clipboard.writeText(el.dataset.copy);
      el.textContent = el.dataset.copy + " · đã copy";
    }} catch (e) {{
      alert(el.dataset.copy);
    }}
  }});
}});
</script>
</body>
</html>
"""
    (ROOT / "index.html").write_text(html, encoding="utf-8")


def write_readme(packages: dict[str, dict], conf: dict) -> None:
    rows = []
    for pkg, info in sorted(packages.items(), key=lambda kv: kv[1]["Name"].lower()):
        arches = ", ".join(ARCH_LABEL.get(a, a) for a in info["archs"])
        rows.append(f"| {info['Name']} | `{pkg}` | {info['Version']} | {arches} |")
    table = "\n".join(rows)
    text = f"""# Jinken Repo

Cydia / Sileo / Zebra repository for jailbreak tweaks.

**Credit: Jinken Nguyen - 1989**  
Cảm ơn bạn đã dùng tweak. Nếu thấy hữu ích, một chút ủng hộ giúp giữ repo miễn phí.

**Donate: {conf['DONATE_BANK']} `{conf['DONATE_ACCOUNT']}` — {conf['DONATE_NAME']}**

## Add source

```
{conf['BASE_URL']}
```

- Sileo: Sources → + → paste URL, or open `sileo://source/{conf['BASE_URL']}/`
- Zebra: `zbra://sources/add/{conf['BASE_URL']}/`
- Cydia: Sources → Edit → Add

Install **one** package per tweak that matches your jailbreak:

| File suffix | Jailbreak |
| --- | --- |
| `iphoneos-arm64` | Rootless (Dopamine, palera1n rootless) |
| `iphoneos-arm` | Rootful (unc0ver, checkra1n, palera1n rootful) |
| `iphoneos-arm64e` | RootHide (Dopamine-roothide / RootHide Bootstrap) |

## Packages

| Name | Package | Version | Builds |
| --- | --- | --- | --- |
{table}

## Credit

- Author / Maintainer: **Jinken Nguyen - 1989**
- Not affiliated with Apple.

## Donate

Cảm ơn bạn đã tin dùng tweak miễn phí. Nếu thấy hữu ích, một chút ủng hộ giúp mình giữ repo chạy và ra bản mới — không bắt buộc.

Thank you for using these free tweaks. A small donation keeps the repo online. No pressure.

| | |
| --- | --- |
| Ngân hàng | {conf['DONATE_BANK']} |
| STK | `{conf['DONATE_ACCOUNT']}` |
| Chủ TK | {conf['DONATE_NAME']} |
| Nội dung | `Donate Jinken Nguyen {conf['YEAR']}` |

VietQR: scan the code on the [homepage]({conf['BASE_URL']}/#donate).

## Upload a new `.deb`

1. Drop files into `debs/` using `package_version_architecture.deb`
2. Run `python3 scripts/update-repo.py`
3. `git add -A && git commit -m "Add tweak" && git push`

Or rebuild from local Theos trees in `~/Documents/code/*/packages`.

## License

MIT — Jinken Nguyen - 1989
"""
    (ROOT / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()
    conf = load_conf(ROOT / "repo.conf")
    if args.base_url:
        conf["BASE_URL"] = args.base_url.rstrip("/")
    base = conf["BASE_URL"].rstrip("/")
    allow = {p.strip() for p in conf.get("PACKAGES", "").split(",") if p.strip()} or None

    debs_dir = ROOT / "debs"
    dep_dir = ROOT / "depictions"
    assets = ROOT / "assets"
    extras = ROOT / "extras"
    icons_dir = ROOT / "icons"
    for d in (debs_dir, dep_dir, assets, extras, icons_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Brand assets
    icon_src = SESSION_IMAGES / "1.jpg"
    banner_src = SESSION_IMAGES / "2.jpg"
    if icon_src.is_file():
        ensure_png(icon_src, ROOT / "CydiaIcon.png", 256, crop_frac=0.08)
        ensure_png(icon_src, ROOT / "CydiaIcon@2x.png", 120, crop_frac=0.08)
        ensure_png(icon_src, ROOT / "CydiaIcon@3x.png", 180, crop_frac=0.08)
        ensure_png(icon_src, assets / "icon.png", 512, crop_frac=0.08)
    if banner_src.is_file():
        copy_banner(banner_src, assets / "banner.jpg", (1600, 900))
        copy_banner(banner_src, assets / "featured.jpg", (830, 466))
    if VIETQR_SRC.is_file():
        shutil.copy2(VIETQR_SRC, assets / "vietqr.png")

    latest = collect_latest_debs(allow)
    print(f"Found {len(latest)} latest package/arch debs")
    keep_debs = set()

    packages: dict[str, dict] = {}
    for (pkg, arch), src in sorted(latest.items()):
        fields = dpkg_fields(src)
        ver = fields["Version"]
        dest_name = f"{pkg}_{ver}_{arch}.deb"
        dest = debs_dir / dest_name
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        keep_debs.add(dest_name)
        info = packages.setdefault(
            pkg,
            {
                "Name": fields.get("Name", pkg),
                "Version": ver,
                "Section": fields.get("Section", "Tweaks"),
                "archs": [],
                "blurb": fields.get("Description", "").split("\n", 1)[0],
                "fields": fields,
            },
        )
        if arch not in info["archs"]:
            info["archs"].append(arch)
        info["archs"].sort()

        icon = find_icon(pkg)
        if icon:
            try:
                ensure_png(icon, icons_dir / f"{pkg}.png", 120)
            except Exception as exc:
                print(f"icon skip {pkg}: {exc}")

    for leftover in debs_dir.glob("*.deb"):
        if leftover.name not in keep_debs:
            leftover.unlink()
    for leftover in extras.glob("*"):
        leftover.unlink()
    for leftover in icons_dir.glob("*.png"):
        pkg = leftover.stem
        if allow and pkg not in allow:
            leftover.unlink()
    for leftover in dep_dir.iterdir():
        if leftover.is_dir() and allow and leftover.name not in allow:
            shutil.rmtree(leftover)

    # Depictions
    for pkg, info in packages.items():
        vi, en = BLURBS.get(pkg, (info["blurb"], info["blurb"]))
        changelog = read_changelog(pkg)
        folder = dep_dir / pkg
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(
            depiction_html(pkg, info["fields"], conf, vi, en, changelog), encoding="utf-8"
        )
        (folder / "sileo.json").write_text(
            json.dumps(sileo_json(pkg, info["fields"], conf, vi, en, changelog), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

    # Packages index
    proc = subprocess.run(
        ["dpkg-scanpackages", "-m", "debs", "/dev/null"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    raw = proc.stderr
    if raw:
        sys.stderr.write(raw)

    blocks = [b for b in proc.stdout.strip().split("\n\n") if b.strip()]
    rewritten = []
    for block in blocks:
        lines = []
        pkg = None
        for line in block.splitlines():
            if line.startswith("Package:"):
                pkg = line.split(":", 1)[1].strip()
            if line.startswith(("Depiction:", "SileoDepiction:", "Homepage:", "Icon:")):
                continue
            lines.append(line)
        if pkg:
            lines.append(f"Depiction: {base}/depictions/{pkg}/index.html")
            lines.append(f"SileoDepiction: {base}/depictions/{pkg}/sileo.json")
            lines.append(f"Homepage: {base}/#donate")
            icon_path = icons_dir / f"{pkg}.png"
            if icon_path.is_file():
                lines.append(f"Icon: {base}/icons/{pkg}.png")
            if "Author:" not in block:
                lines.append(f"Author: {conf['AUTHOR']}")
            if "Maintainer:" not in block:
                lines.append(f"Maintainer: {conf['AUTHOR']}")
        rewritten.append("\n".join(lines))
    packages_text = "\n\n".join(rewritten) + "\n"
    (ROOT / "Packages").write_text(packages_text, encoding="utf-8")
    with gzip.open(ROOT / "Packages.gz", "wt", encoding="utf-8") as gz:
        gz.write(packages_text)
    subprocess.check_call(["bzip2", "-kf", str(ROOT / "Packages")])

    pkg_bytes = packages_text.encode("utf-8")
    gz_bytes = (ROOT / "Packages.gz").read_bytes()
    bz_bytes = (ROOT / "Packages.bz2").read_bytes()
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S UTC")
    release = f"""Origin: {conf['ORIGIN']}
Label: {conf['LABEL']}
Suite: {conf['SUITE']}
Version: {conf['VERSION']}
Codename: {conf['CODENAME']}
Date: {now}
Architectures: iphoneos-arm iphoneos-arm64 iphoneos-arm64e
Components: main
Description: {conf['DESCRIPTION']}
MD5Sum:
 {md5_file(ROOT / 'Packages')} {len(pkg_bytes)} Packages
 {hashlib.md5(gz_bytes).hexdigest()} {len(gz_bytes)} Packages.gz
 {hashlib.md5(bz_bytes).hexdigest()} {len(bz_bytes)} Packages.bz2
SHA256:
 {hashlib.sha256(pkg_bytes).hexdigest()} {len(pkg_bytes)} Packages
 {hashlib.sha256(gz_bytes).hexdigest()} {len(gz_bytes)} Packages.gz
 {hashlib.sha256(bz_bytes).hexdigest()} {len(bz_bytes)} Packages.bz2
"""
    (ROOT / "Release").write_text(release, encoding="utf-8")

    banners = []
    for pkg in FEATURED:
        if pkg in packages:
            banners.append(
                {
                    "url": f"{base}/assets/featured.jpg",
                    "title": packages[pkg]["Name"],
                    "package": pkg,
                    "hideShadow": False,
                }
            )
    featured = {
        "class": "FeaturedBannersView",
        "itemSize": "{263, 148}",
        "itemCornerRadius": 12,
        "banners": banners,
    }
    (ROOT / "sileo-featured.json").write_text(
        json.dumps(featured, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    write_index(packages, conf)
    write_readme(packages, conf)

    print(f"Packages: {len(packages)}")
    for pkg, info in sorted(packages.items()):
        print(f"  {info['Name']:20} {info['Version']:8} {','.join(info['archs'])}")
    print(f"BASE_URL={base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
