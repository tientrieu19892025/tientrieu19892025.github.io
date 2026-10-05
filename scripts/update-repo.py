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

ARCH_DIR = {
    "iphoneos-arm": "rootful",
    "iphoneos-arm64": "rootless",
    "iphoneos-arm64e": "roothide",
}

KIND_GUIDES = [
    {
        "id": "rootless",
        "arch": "iphoneos-arm64",
        "title": "Rootless",
        "who": "Dopamine (mặc định), palera1n rootless",
        "how": "Máy có thư mục /var/jb. Đây là Dopamine thông thường, không phải RootHide.",
        "file": "file .deb kết thúc bằng _iphoneos-arm64.deb",
    },
    {
        "id": "rootful",
        "arch": "iphoneos-arm",
        "title": "Rootful",
        "who": "unc0ver, checkra1n, palera1n rootful, Taurine, Odyssey",
        "how": "Không có /var/jb. Tweak nằm ở /Library/MobileSubstrate.",
        "file": "file .deb kết thúc bằng _iphoneos-arm.deb",
    },
    {
        "id": "roothide",
        "arch": "iphoneos-arm64e",
        "title": "RootHide",
        "who": "Dopamine RootHide, RootHide Bootstrap",
        "how": "Jailbreak ẩn đường dẫn (jbroot). Sileo/Zebra của bản RootHide.",
        "file": "file .deb kết thúc bằng _iphoneos-arm64e.deb",
    },
]

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
        "Khung kính trên màn hình chính — status, icon, dock. Vuốt, màu chữ và kiểu icon chỉnh trong Cài đặt.",
        "Glass frames on the Home Screen. Swipe, label color and icon shape live in Settings.",
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
        "Ô tìm trên Home. YouTube phát ngay trên ô, nghe nền được. Có phòng chat chung — bấm Chat cạnh Tìm.",
        "Home Screen search, YouTube on the pill, background audio, and a shared chat next to Search.",
    ),
    "com.jinkennguyen.slapios": (
        "Vỗ, gõ, lắc máy thì kêu. Nhiều gói tiếng; chọn Rên thì chỉ rên.",
        "Slap, tap or shake the phone. Pick a sound pack — Groan stays groan-only.",
    ),
    "com.jinkennguyen.cpuboost": (
        "CPU chậm hơn cho pin, hoặc mạnh hơn một chút trên máy cũ. Ngủ sâu khi tắt màn hình, Eco / Boost / Turbo.",
        "Slow the CPU to save battery, or push it a bit on older phones. Deep sleep when locked, Eco / Boost / Turbo.",
    ),
    "com.jinkennguyen.haloframe": (
        "Màn khoá kính: mặt trời/mặt trăng theo giờ, pin, nhạc, báo thức.",
        "Glass lock screen: sun and moon by the hour, battery, music, next alarm.",
    ),
    "com.jinkennguyen.noxframe": (
        "Tắt màn vẫn chụp và quay. Trong Ảnh có nút lưu đúng khung hình video.",
        "Shoot with the screen off. In Photos, save the current video frame.",
    ),
    "com.jinkennguyen.settingsz": (
        "Sắp lại Cài đặt: kệ, màu đề mục, kéo đổi cỡ dòng.",
        "Rearrange Settings: shelves, title color, drag to resize rows.",
    ),
    "com.jinkennguyen.appsw": (
        "Vuốt lên đa nhiệm: cửa sổ lớn phía trên, năm app gần nhất phía dưới.",
        "App switcher: large window on top, five recents underneath.",
    ),
    "com.jinkennguyen.driveframe": (
        "Mọi app lên CarPlay, chia nhiều cửa sổ trên màn xe.",
        "Any app on CarPlay, split into panes on the car display.",
    ),
    "com.jinkennguyen.videoadsspeed": (
        "Tăng tốc quảng cáo video trong app, mỗi cái một công tắc.",
        "Speed up in-app video ads, each with its own switch.",
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
        "Nhám màn hình, e-ink như giấy. Không treo máy.",
        "Matte screen, paper e-ink. Does not freeze the phone.",
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
    "com.jinkennguyen.prankframe": (
        "100 trò khăm trên iPhone: sọc màn hình, kính vỡ, pin ảo, tiếng lạ, rung. Lắc để dừng.",
        "100 iPhone pranks: stripes, cracked glass, fake battery, odd sounds, haptics. Shake to stop.",
    ),
    "com.jinkennguyen.statusbarinfo": (
        "Chạm hoặc nhấn giữ thanh trạng thái ở Màn hình chính và trong mọi app. Hơn 78 thông số & dữ liệu Internet trực tiếp.",
        "Tap or long-press status bar on Home Screen and in every app. 78+ specs & live internet data.",
    ),
    "com.jinkennguyen.jinken": (
        "App trên Home: xem toàn bộ tweak trên repo, cách dùng, donate.",
        "Home Screen app: browse tweaks on repo, how-to, donate.",
    ),
    "com.jinken.listapp": (
        "Thay thế màn hình chính bằng danh sách ứng dụng kính lỏng 2/3 màn hình, thiết kế đa dạng, chỉ hiển thị app thật, mượt mà và chống treo máy.",
        "Modern Liquid Glass App Launcher replacing Home Screen. 2/3 width floating glass pills, real apps only, 5 designs & 7 colors.",
    ),
    "com.jinken.quickpass": (
        "Nút bấm đồ hoạ kính lỏng mở ngay bàn phím mật mã số trên Màn hình khoá cho thiết bị Face ID, hỗ trợ kéo thả tuỳ chỉnh vị trí tự do.",
        "Instant passcode keypad button on Lock Screen for Face ID devices with 3D Liquid Glass design and draggable custom positioning.",
    ),
    "com.jinken.disswipe": (
        "Khóa cử chỉ vuốt ngang cạnh đáy (Home bar) đổi app khi đang mở bàn phím gõ. Hỗ trợ bảo vệ cử chỉ vuốt về Home, ẩn Home bar khi gõ, rung phản hồi Haptic.",
        "Disable bottom Home bar horizontal app-switching gestures while the keyboard is open. Protect Home swipe, auto-hide Home bar, and haptics.",
    ),
    "com.jinken.freezebuster": (
        "Phát hiện và tự động giải cứu khi máy bị đơ cảm ứng hoặc nghẽn Main Thread, giải phóng RAM tức thì và tối ưu độ mượt cho thiết bị cấu hình yếu.",
        "Automatic unfreeze rescue when UI hangs or Main Thread freezes, instant RAM purge, and responsiveness optimization for low-end devices.",
    ),
    "com.jinken.orientflow": (
        "Gợi ý xoay màn hình thông minh khi khoá xoay. Giữ nguyên hướng xoay ngang sau khi ấn, tự khoá lại khi dựng dọc, thanh kéo tuỳ chọn vị trí tự do.",
        "Smart rotation suggestion prompt when orientation lock is active. Locks in landscape once tapped, auto-relocks on portrait, custom slider positioning.",
    ),
    "com.jinken.englishkids": (
        "Ứng dụng học tiếng Anh tương tác cho trẻ em: từ vựng, âm thanh, flashcard, mini-game và thanh chữ chạy.",
        "Interactive English learning app for kids: vocabulary, pronunciation, flashcards, games and live ticker.",
    ),
    "com.jinken.drawkids": (
        "Ứng dụng học vẽ và tô màu tương tác cho bé: hướng dẫn từng nét vẽ con vật, đồ vật, pha màu và bảng vẽ sáng tạo.",
        "Interactive drawing and coloring app for kids: step-by-step guides, coloring, color mixing and free canvas.",
    ),
    "com.jinkennguyen.aurahtml": (
        "Bộ widget HTML/CSS/JS đỉnh cao cho Màn hình khoá & Màn hình chính. Hơn 100 giao diện đẳng cấp, tuỳ chọn thêm bớt tự do, kéo thả vị trí và tự động giãn icon thông minh.",
        "Premium HTML/CSS/JS dynamic widgets for Lock Screen & Home Screen. 100+ luxury themes, bilingual details, free dragging and smart icon pushing.",
    ),
    "com.jinken.autobrightclamp": (
        "Tweak thông minh giới hạn biên độ sáng tự động (set độ sáng tối thiểu và tối đa), chống chói mắt trong bóng tối, chống quá nhiệt ngoài trời nắng và tiết kiệm pin.",
        "Smart Auto-Brightness Limiter: clamp minimum and maximum brightness boundaries to prevent eye strain at night, avoid overheating in sunlight, and maximize battery life.",
    ),
}

FEATURE_GUIDES = {
    "com.jinkennguyen.lookglass": {
        "tab": "Chat cộng đồng",
        "md": (
            "**Chat cộng đồng** là phòng chat chung của người dùng LookGlass trên máy jailbreak. "
            "Tin nhắn hiện realtime. Chỉ **chữ và link** — không gửi hình, không gửi video.\n\n"
            "**Cách vào chat**\n"
            "1. Cài LookGlass → **Respring**.\n"
            "2. Mở ô LookGlass trên màn hình chính → bấm nút **Chat** (cạnh **Tìm**).\n"
            "3. Đặt **username** một lần rồi vào phòng.\n"
            "4. Gõ tin hoặc dán link rồi gửi. Chat đã kết nối sẵn — không cần dán URL hay API key.\n"
            "5. Bấm vào tin của mình để **Chép** hoặc **Xoá**.\n\n"
            "**Community Chat** is a shared room for LookGlass users. Tap **Chat** next to Search, "
            "set a username, then send text or links. No photos, no video."
        ),
        "html": (
            "<h2>Chat cộng đồng</h2>"
            "<p><strong>Chat cộng đồng</strong> là phòng chat chung của người dùng LookGlass trên máy jailbreak. "
            "Tin nhắn hiện ngay. Chỉ chữ và link — không gửi hình, không gửi video.</p>"
            "<p><strong>Cách vào chat</strong></p>"
            "<ol>"
            "<li>Cài LookGlass → <strong>Respring</strong>.</li>"
            "<li>Mở ô LookGlass trên Home → bấm <strong>Chat</strong> (cạnh <strong>Tìm</strong>).</li>"
            "<li>Đặt <strong>username</strong> một lần rồi vào phòng.</li>"
            "<li>Gõ tin hoặc dán link rồi gửi. Không cần dán URL / API key.</li>"
            "<li>Bấm tin của mình để Chép hoặc Xoá.</li>"
            "</ol>"
            "<p class=\"en\">Tap Chat next to Search, set a username, send text or links. No photos.</p>"
        ),
    },
}

FEATURED = [
    "com.jinkennguyen.aurahtml",
    "com.jinkennguyen.duoframe",
    "com.jinkennguyen.lookglass",
    "com.jinkennguyen.slapios",
    "com.jinkennguyen.cpuboost",
    "com.jinkennguyen.noxframe",
    "com.jinkennguyen.settingsz",
    "com.jinkennguyen.appsw",
    "com.jinkennguyen.haloframe",
    "com.jinkennguyen.prankframe",
    "com.jinkennguyen.statusbarinfo",
    "com.jinkennguyen.adshield",
    "com.jinkennguyen.jinken",
    "com.jinken.listapp",
    "com.jinken.quickpass",
    "com.jinken.disswipe",
    "com.jinken.freezebuster",
    "com.jinken.orientflow",
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
    search_roots = list(CODE.glob("*/packages")) + [
        Path.home() / "StatusBarInfo" / "packages",
        Path.home() / "AuraHTML" / "packages",
        Path.home() / "ListApp" / "packages",
        Path.home() / "QuickPass" / "packages",
        Path.home() / "OrientFlow" / "packages",
        Path.home() / "dis-swipe" / "packages",
        Path.home() / "FreezeBuster" / "build_output" / "rootful",
        Path.home() / "FreezeBuster" / "build_output" / "rootless",
        Path.home() / "FreezeBuster" / "build_output" / "roothide",
        Path.home() / "AutoBrightClamp" / "build_output" / "rootful",
        Path.home() / "AutoBrightClamp" / "build_output" / "rootless",
        Path.home() / "AutoBrightClamp" / "build_output" / "roothide",
        ROOT / "debs" / "rootful",
        ROOT / "debs" / "rootless",
        ROOT / "debs" / "roothide",
        DESKTOP
    ]
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


REPO_ARCHES = ("iphoneos-arm", "iphoneos-arm64", "iphoneos-arm64e")


def write_packages_set(directory: Path, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    pkg_path = directory / "Packages"
    pkg_path.write_text(text, encoding="utf-8")
    with gzip.open(directory / "Packages.gz", "wt", encoding="utf-8") as gz:
        gz.write(text)
    subprocess.check_call(["bzip2", "-kf", str(pkg_path)])


def split_packages_by_arch(packages_text: str) -> dict[str, str]:
    buckets: dict[str, list[str]] = {a: [] for a in REPO_ARCHES}
    for block in packages_text.strip().split("\n\n"):
        if not block.strip():
            continue
        arch = ""
        for line in block.splitlines():
            if line.startswith("Architecture:"):
                arch = line.split(":", 1)[1].strip()
                break
        if arch in buckets:
            buckets[arch].append(block)
    return {arch: ("\n\n".join(blocks) + "\n") if blocks else "" for arch, blocks in buckets.items()}


def hash_lines(files: list[tuple[str, Path]]) -> tuple[str, str]:
    md5_rows = []
    sha_rows = []
    for rel, path in files:
        data = path.read_bytes()
        md5_rows.append(f" {hashlib.md5(data).hexdigest()} {len(data)} {rel}")
        sha_rows.append(f" {hashlib.sha256(data).hexdigest()} {len(data)} {rel}")
    return "\n".join(md5_rows), "\n".join(sha_rows)


def write_dists(conf: dict, now: str, by_arch: dict[str, str]) -> None:
    dists = ROOT / "dists"
    if dists.exists():
        shutil.rmtree(dists)
    suites: list[str] = []
    for name in (conf.get("SUITE", "stable"), conf.get("CODENAME", "stable")):
        if name and name not in suites:
            suites.append(name)
    for suite in suites:
        suite_dir = dists / suite
        hashed: list[tuple[str, Path]] = []
        for arch, text in by_arch.items():
            if not text.strip():
                continue
            binary = suite_dir / "main" / f"binary-{arch}"
            write_packages_set(binary, text)
            (binary / "Release").write_text(
                f"""Archive: {suite}
Origin: {conf['ORIGIN']}
Label: {conf['LABEL']}
Component: main
Architecture: {arch}
Description: {conf['DESCRIPTION']}
""",
                encoding="utf-8",
            )
            for fname in ("Packages", "Packages.gz", "Packages.bz2", "Release"):
                hashed.append((f"main/binary-{arch}/{fname}", binary / fname))
        md5s, shas = hash_lines(hashed)
        (suite_dir / "Release").write_text(
            f"""Origin: {conf['ORIGIN']}
Label: {conf['LABEL']}
Suite: {suite}
Version: {conf['VERSION']}
Codename: {suite}
Date: {now}
Architectures: iphoneos-arm iphoneos-arm64 iphoneos-arm64e
Components: main
Description: {conf['DESCRIPTION']}
MD5Sum:
{md5s}
SHA256:
{shas}
""",
            encoding="utf-8",
        )


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
    search_dirs = list(CODE.iterdir()) + [Path.home() / "StatusBarInfo", Path.home() / "ListApp"]
    for p in search_dirs:
        if not p.is_dir():
            continue
        control = p / "control"
        if control.is_file() and f"Package: {pkg}" in control.read_text(encoding="utf-8", errors="replace"):
            return p
    aliases = {
        "com.carsplit.tweak": "CarSplit",
        "com.t27.backport": "T27",
        "com.jinkennguyen.trungthulan": "TrungThuLan",
        "com.jinkennguyen.trungthuplay": "TrungThuPlay",
        "com.jinkennguyen.prankframe": "PrankFrame",
        "com.jinkennguyen.statusbarinfo": "StatusBarInfo",
        "com.jinken.listapp": "ListApp",
        "com.jinken.disswipe": "dis-swipe",
        "com.jinken.autobrightclamp": "AutoBrightClamp",
    }
    name = aliases.get(pkg)
    if name:
        for root in (CODE, Path.home()):
            if (root / name).is_dir():
                return root / name
    return None


def find_icon(pkg: str) -> Path | None:
    proj = project_dir_for(pkg)
    if not proj:
        return None
    for rel in (
        "Preferences/Resources/icon@3x.png",
        "Preferences/Resources/icon@2x.png",
        "Preferences/Resources/icon.png",
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


PUBLIC_LOG = {
    "com.jinken.disswipe": """**1.1.1**
Ẩn thanh Home Bar ngay lập tức khi mở bàn phím (không cần vuốt). Sửa lỗi vuốt ngang đổi app và vuốt 2 lần về Home. Sửa thanh trượt độ nhạy: hiện badge giá trị, không bị lẹm chữ.

**1.1.0**
Khóa cử chỉ vuốt ngang cạnh đáy (Home bar) đổi app khi đang mở bàn phím gõ. Hỗ trợ bảo vệ cử chỉ vuốt về Home, ẩn Home bar khi gõ, rung phản hồi Haptic.""",
    "com.jinkennguyen.duoframe": """**3.5.3**
Cài trên iOS 17/18 không còn báo thiếu thành phần.

**3.5.2**
Đổi màu chữ và icon trên Home.

**3.5.1**
Vuốt trang mượt hơn. Thêm vài kiểu icon.

**3.5.0**
Tắt cuộn liên tục nếu muốn vuốt trang trái/phải như iOS gốc.""",
    "com.jinkennguyen.lookglass": """**4.0.4**
Chat hiện tin ngay khi gửi.

**4.0.3**
Sửa Cài đặt LookGlass trên iOS 16 RootHide.

**4.0.0**
Phòng chat chung. Tìm YouTube rồi phát ngay trên ô, nghe nền được.""",
    "com.jinkennguyen.slapios": """**1.2.0**
Gói tiếng thu âm thật. Chọn Rên thì chỉ rên, không lẫn tiếng khác.""",
    "com.jinkennguyen.cpuboost": """**1.0.3**
Sửa Safe Mode khi chọn preset rồi Respring.

**1.0.2**
Cài được trên iOS 17/18.""",
    "com.jinkennguyen.noxframe": """**1.1.1**
Sửa Camera treo trên iOS 18.

**1.1.0**
Trong Ảnh, khi xem video có nút lưu đúng khung hình đó.""",
    "com.jinkennguyen.settingsz": """**1.0.11**
Cài đặt không còn tự thoát khi đang dùng.

**1.0.10**
Mở mục trong Cài đặt không còn bị thoát. Tweak hiện đủ trong danh sách và ô tìm.""",
    "com.jinkennguyen.appsw": """**1.0.4**
Vuốt lên đa nhiệm thì ra AppSw, che màn gốc — kể cả khi chưa có app gần đây.

**1.0.3**
Không nhảy nhầm lúc mở app.""",
    "com.jinkennguyen.haloframe": """**3.2.3**
Hẹn giờ lock đọc app Đồng hồ (countdown từng giây). Nhiệt độ đọc app Thời tiết. Cài đặt mượt, không khựng/thoát.

**3.2.1**
Giờ trên màn khoá đúng múi giờ máy.

**3.2.0**
Mặt trời / mặt trăng đổi theo ngày.""",
    "com.jinkennguyen.prankframe": """**1.0.0**
100 trò khăm trên iPhone (sọc, màn hình vỡ, giả pin, tiếng lạ, rung, lộn ngược…). Mặc định TẮT. Lắc mạnh để dừng.""",
    "com.jinkennguyen.statusbarinfo": """**1.2.0**
Chạm thanh trạng thái trên Màn hình chính và trong mọi app. Game không bị inject. Cài đặt kiểu kính.

**1.1.0**
Bảng điều khiển khi chạm Status Bar: hơn 68 thông số. Giao diện kính mờ, sao chép 1 chạm.""",
    "com.jinken.autobrightclamp": """**1.0.0**
Giới hạn biên độ sáng min/max tự động. Chống chói ban đêm, chống quá nhiệt ban ngày, tiết kiệm pin. Tương thích 100% RootHide, Rootless, Rootful.""",
    "com.jinken.freezebuster": """**1.2.0**
Biên dịch lại bằng Theos-RootHide chuẩn, khắc phục hoàn toàn lỗi Substrate crash trên RootHide. Tự động giải cứu khi UI treo cứng hoặc tràn RAM.

**1.1.0**
Sửa lỗi Safe Mode khi cài đặt. Cải tiến thuật toán phát hiện Watchdog timeout và giải phóng bộ nhớ tức thì.""",
    "com.jinken.orientflow": """**1.0.8**
Nâng cấp khả năng phản hồi cảm ứng, tối ưu kích thước nút xoay và hỗ trợ trọn vẹn RootHide.

**1.0.7**
Tối ưu nút xoay nổi trên iOS 16 & 17, thanh trượt toạ độ mượt mà.""",
    "com.jinkennguyen.jinken": """**1.1.0**
Cập nhật danh mục tweak mới nhất, vá giao diện Liquid Glass và hỗ trợ RootHide đầy đủ.

**1.0.0**
App trên Home. Mở để xem tweak trên repo, cách dùng, donate. Kéo xuống để lấy danh sách mới.""",
    "com.jinken.englishkids": """**1.7** (Build 13)
Ứng dụng học tiếng Anh tương tác cho trẻ em (English Kids). Khắc phục đường dẫn sandbox và tài nguyên trên RootHide, học từ vựng theo chủ đề, phát âm chuẩn, mini games câu đố tương tác, flashcards.""",
    "com.jinken.drawkids": """**1.6** (Build 7)
Ứng dụng học vẽ và tô màu tương tác cho bé (Bé học Vẽ). Sửa triệt để lỗi khởi động, nâng cấp bảo mật container, hỗ trợ uicache trên RootHide, hướng dẫn từng nét vẽ con vật, đồ vật, pha màu, bảng vẽ tự do, chạy offline 100%.""",
}


def public_changelog(pkg: str, text: str) -> str:
    if pkg in PUBLIC_LOG:
        return PUBLIC_LOG[pkg]
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
    guide = FEATURE_GUIDES.get(pkg, {})
    extra_html = guide.get("html", "")
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
h2{{font-size:17px;margin:16px 0 8px;color:#7dd3fc}}
ol{{padding-left:1.2em;margin:8px 0}}
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
{extra_html}
<div class="donate">
{thanks['html']}
</div>
</div>
<hr>
<p>Sileo tự cài đúng gói cho máy (rootless / rootful / RootHide). Sau khi cài: <strong>Respring</strong>, mở <strong>Cài đặt → {html_escape(name)}</strong>.</p>
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
    guide = FEATURE_GUIDES.get(pkg, {})
    md = (
        f"**{name}** — {vi}\n\n{en}\n\n"
        f"**Phiên bản / Version:** {ver}  \n"
        f"**Tác giả / Author:** {author}  \n"
        f"**iOS:** 14+  \n"
        f"**Gói:** rootless · rootful · RootHide (`iphoneos-arm64e`)\n\n"
        f"Sau khi cài: **Respring**, mở **Cài đặt → {name}**.\n\n"
        f"{thanks['vi']}\n\n{thanks['en']}"
    )
    if guide.get("md"):
        md = (
            f"**{name}** — {vi}\n\n{en}\n\n"
            + guide["md"]
            + f"\n\n**Phiên bản / Version:** {ver}  \n"
            f"**Tác giả / Author:** {author}  \n"
            f"**iOS:** 14+  \n"
            f"**Gói:** rootless · rootful · RootHide (`iphoneos-arm64e`)\n\n"
            f"Sau khi cài: **Respring**, mở **Cài đặt → {name}**."
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
    out = {
        "minVersion": "0.4",
        "class": "DepictionTabView",
        "tintColor": "#38BDF8",
        "headerImage": f"{conf['BASE_URL'].rstrip('/')}/assets/banner.jpg",
        "tabs": [
            {"tabname": "Details", "class": "DepictionStackView", "views": views},
        ],
    }
    if guide.get("md"):
        out["tabs"].append(
            {
                "tabname": guide.get("tab", "Chat cộng đồng"),
                "class": "DepictionStackView",
                "views": [
                    {"class": "DepictionHeaderView", "title": guide.get("tab", "Chat cộng đồng"), "useBoldText": True},
                    {
                        "class": "DepictionMarkdownView",
                        "markdown": guide["md"],
                        "useSpacing": True,
                        "useRawFormat": False,
                    },
                ],
            }
        )
    out["tabs"].extend(
        [
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
        ]
    )
    return out


SITE_CSS = """
:root {
  --bg: #07090e;
  --bg-gradient: radial-gradient(circle at 50% -20%, #1e293b 0%, #0a0f1d 45%, #05070b 100%);
  --card: rgba(16, 24, 39, 0.65);
  --card-hover: rgba(24, 36, 58, 0.85);
  --card-border: rgba(255, 255, 255, 0.08);
  --card-border-glow: rgba(56, 189, 248, 0.35);
  --text: #f8fafc;
  --text-secondary: #94a3b8;
  --muted: #64748b;
  --accent: #38bdf8;
  --accent-glow: rgba(56, 189, 248, 0.25);
  --good: #34d399;
  --gold: #fbbf24;
  --purple: #a855f7;
  --font: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif;
}
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font: 15px/1.6 var(--font);
  background: var(--bg);
  background-image: var(--bg-gradient);
  background-attachment: fixed;
  color: var(--text);
  min-height: 100vh;
}
a { color: var(--accent); text-decoration: none; transition: all 0.2s ease; }
a:hover { opacity: 0.85; }

/* Navbar */
.nav-bar {
  position: sticky; top: 0; z-index: 100;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  background: rgba(7, 9, 14, 0.75);
  border-bottom: 1px solid var(--card-border);
  padding: 12px 20px;
}
.nav-inner {
  max-width: 1080px; margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between;
}
.brand {
  display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 17px;
  color: var(--text);
}
.brand-icon {
  width: 32px; height: 32px; border-radius: 8px; box-shadow: 0 4px 12px rgba(56,189,248,0.25);
}
.nav-links { display: flex; gap: 16px; align-items: center; }
.nav-links a { font-size: 14px; font-weight: 500; color: var(--text-secondary); }
.nav-links a:hover, .nav-links a.active { color: var(--accent); }

/* Hero */
.hero {
  position: relative; padding: 48px 20px 36px;
  background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(56, 189, 248, 0.15), transparent 70%);
  text-align: center;
}
.hero-inner { max-width: 840px; margin: 0 auto; }
.badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 14px; border-radius: 999px;
  background: rgba(56, 189, 248, 0.1);
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: var(--accent); font-size: 12px; font-weight: 600;
  letter-spacing: 0.05em; text-transform: uppercase;
}
.badge-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--good);
  box-shadow: 0 0 8px var(--good);
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.9); } }
h1 {
  font-size: clamp(30px, 6vw, 52px); font-weight: 800;
  letter-spacing: -0.02em; margin: 16px 0 10px;
  background: linear-gradient(135deg, #ffffff 30%, #93c5fd 80%, #38bdf8 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.sub {
  color: var(--text-secondary); font-size: clamp(15px, 2.5vw, 18px);
  max-width: 680px; margin: 0 auto 24px; line-height: 1.6;
}

/* Action Buttons */
.hero-actions {
  display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; margin-top: 20px;
}
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 11px 20px; border-radius: 12px; font-weight: 600; font-size: 14px;
  background: rgba(255, 255, 255, 0.05); border: 1px solid var(--card-border);
  color: var(--text); cursor: pointer; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
.btn:hover {
  background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}
.btn.primary {
  background: linear-gradient(135deg, #38bdf8, #0284c7);
  color: #ffffff; border-color: transparent;
  box-shadow: 0 4px 16px rgba(56, 189, 248, 0.35);
}
.btn.primary:hover {
  background: linear-gradient(135deg, #60a5fa, #0369a1);
  box-shadow: 0 6px 24px rgba(56, 189, 248, 0.5);
}
.btn.gold {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff; border-color: transparent;
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.3);
}
.btn.gold:hover {
  background: linear-gradient(135deg, #fbbf24, #b45309);
  box-shadow: 0 6px 24px rgba(245, 158, 11, 0.45);
}

/* Wrap */
.wrap { max-width: 1080px; margin: 0 auto; padding: 0 20px 80px; }
h2 {
  font-size: 22px; font-weight: 700; margin: 44px 0 16px;
  display: flex; align-items: center; gap: 10px;
}
h2::before {
  content: ""; display: inline-block; width: 4px; height: 20px;
  background: var(--accent); border-radius: 2px;
}

/* Glass Card */
.card {
  background: var(--card);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--card-border);
  border-radius: 18px; padding: 22px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
  position: relative; overflow: hidden;
}
.card:hover {
  border-color: var(--card-border-glow);
  box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.35);
}
.grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 18px; margin-top: 18px;
}

/* Architecture Cards */
.arch-card {
  display: flex; flex-direction: column; justify-content: space-between;
}
.arch-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.arch-title { font-size: 20px; font-weight: 700; margin: 0; color: #fff; }
.arch-badge {
  font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 6px;
  background: rgba(255, 255, 255, 0.08); color: var(--muted); font-family: ui-monospace, monospace;
}
.arch-badge.roothide { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }
.arch-badge.rootless { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.arch-badge.rootful { background: rgba(168, 85, 247, 0.15); color: #a855f7; }
.arch-desc { color: var(--text-secondary); font-size: 14px; line-height: 1.5; margin: 0 0 12px; }
.arch-hint {
  font-size: 12px; color: var(--muted); font-family: ui-monospace, monospace;
  background: rgba(0, 0, 0, 0.3); padding: 8px 10px; border-radius: 8px; margin-bottom: 16px;
  border-left: 2px solid var(--accent);
}

/* Search & Filters */
.search-container {
  margin: 28px 0 20px; display: flex; flex-direction: column; gap: 14px;
}
.search-bar-wrap { position: relative; }
.search-input {
  width: 100%; padding: 14px 18px 14px 44px; font-size: 15px;
  background: rgba(16, 24, 39, 0.7);
  border: 1px solid var(--card-border); border-radius: 14px;
  color: #fff; outline: none; transition: all 0.25s ease;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}
.search-input:focus {
  border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow);
}
.search-icon {
  position: absolute; left: 16px; top: 50%; transform: translateY(-50%);
  color: var(--muted); pointer-events: none; width: 18px; height: 18px;
}
.filter-pills { display: flex; flex-wrap: wrap; gap: 8px; }
.filter-pill {
  padding: 7px 14px; font-size: 13px; font-weight: 500; border-radius: 999px;
  background: rgba(255, 255, 255, 0.05); border: 1px solid var(--card-border);
  color: var(--text-secondary); cursor: pointer; transition: all 0.2s ease;
}
.filter-pill:hover, .filter-pill.active {
  background: var(--accent); color: #042033; font-weight: 600; border-color: transparent;
}

/* Tweak Card */
.tweak-card {
  display: flex; flex-direction: column; justify-content: space-between;
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.tweak-card:hover {
  transform: translateY(-4px); border-color: rgba(56, 189, 248, 0.4);
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4);
}
.tweak-top { margin-bottom: 12px; }
.tweak-head {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px;
}
.tweak-title { font-size: 18px; font-weight: 700; margin: 0; color: #fff; }
.tweak-ver {
  font-size: 12px; font-weight: 600; padding: 2px 7px; border-radius: 6px;
  background: rgba(56, 189, 248, 0.15); color: var(--accent);
}
.tweak-tag {
  display: inline-block; font-size: 11px; font-weight: 600;
  color: var(--muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em;
}
.tweak-desc {
  font-size: 14px; color: var(--text-secondary); line-height: 1.5; margin: 0 0 8px;
}
.tweak-en { font-size: 13px; color: var(--muted); margin: 0 0 14px; font-style: italic; }
.tweak-downloads {
  display: flex; flex-wrap: wrap; gap: 6px; margin-top: auto; padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.dl-chip {
  font-size: 12px; font-weight: 600; padding: 5px 10px; border-radius: 8px;
  background: rgba(255, 255, 255, 0.06); border: 1px solid var(--card-border);
  color: var(--text); display: inline-flex; align-items: center; gap: 4px;
}
.dl-chip:hover {
  background: rgba(56, 189, 248, 0.2); border-color: var(--accent); color: #fff;
}
.dl-chip.roothide { border-color: rgba(56, 189, 248, 0.3); color: #7dd3fc; }
.dl-chip.ipa { border-color: rgba(52, 211, 153, 0.4); color: #6ee7b7; background: rgba(52, 211, 153, 0.1); }
.dl-chip.apk { border-color: rgba(251, 191, 36, 0.4); color: #fde047; background: rgba(251, 191, 36, 0.1); }
.tweak-actions {
  display: flex; align-items: center; justify-content: space-between; margin-top: 12px;
}

/* Code Snippet */
.code-box {
  position: relative; background: #050811; border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px; padding: 14px 16px; margin: 10px 0 16px;
  display: flex; align-items: center; justify-content: space-between;
}
.code-box code { color: #7dd3fc; font-family: ui-monospace, monospace; font-size: 14px; }
.copy-btn {
  background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3);
  color: var(--accent); padding: 5px 12px; border-radius: 8px; font-size: 12px;
  font-weight: 600; cursor: pointer; transition: all 0.2s ease;
}
.copy-btn:hover { background: var(--accent); color: #042033; }

/* Steps */
ol.steps { padding-left: 1.3em; margin: 8px 0; }
ol.steps li { margin: 8px 0; color: var(--text-secondary); }
ol.steps strong { color: #fff; }

/* Donate Section */
.donate-grid {
  display: grid; grid-template-columns: 200px 1fr; gap: 24px; align-items: center;
}
.donate-qr {
  width: 200px; height: 200px; background: #fff; border-radius: 16px;
  padding: 8px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4); object-fit: contain;
}
.donate-info h3 { margin: 0 0 8px; font-size: 20px; color: #fff; }
.donate-info p { color: var(--text-secondary); margin: 0 0 14px; line-height: 1.6; }
.donate-table {
  background: rgba(0, 0, 0, 0.25); border-radius: 12px; padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.donate-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); font-size: 14px;
}
.donate-row:last-child { border-bottom: none; }
.donate-label { color: var(--muted); }
.donate-val { font-weight: 600; color: #fff; }

/* Footer */
footer {
  text-align: center; color: var(--muted); font-size: 13px;
  padding: 40px 20px; border-top: 1px solid var(--card-border);
}

@media (max-width: 768px) {
  .donate-grid { grid-template-columns: 1fr; text-align: center; }
  .donate-qr { margin: 0 auto; }
  .donate-row { flex-direction: column; gap: 4px; align-items: center; }
  .hero-actions { flex-direction: column; }
  .btn { width: 100%; }
}
"""


def write_kind_pages(packages: dict[str, dict], conf: dict) -> None:
    for kind in KIND_GUIDES:
        cards = []
        for pkg, info in sorted(packages.items(), key=lambda kv: kv[1]["Name"].lower()):
            href = info.get("files", {}).get(kind["arch"])
            if not href:
                continue
            vi, en = BLURBS.get(pkg, (info.get("blurb", ""), ""))
            fname = href.rsplit("/", 1)[-1]
            cards.append(
                f"""
<article class="card tweak-card">
  <div class="tweak-top">
    <div class="tweak-head">
      <h3 class="tweak-title">{html_escape(info['Name'])}</h3>
      <span class="tweak-ver">{html_escape(info['Version'])}</span>
    </div>
    <p class="tweak-desc">{html_escape(vi)}</p>
    <div class="code-box" style="margin:8px 0;padding:8px 12px;">
      <code style="font-size:12px;">{html_escape(fname)}</code>
    </div>
  </div>
  <div class="tweak-actions">
    <a class="btn primary" style="padding:7px 14px;font-size:13px;" href="../{html_escape(href)}">Tải .deb</a>
    <a class="btn" style="padding:7px 14px;font-size:13px;" href="../depictions/{html_escape(pkg)}/">Chi tiết →</a>
  </div>
</article>"""
            )
        (ROOT / kind["id"]).mkdir(parents=True, exist_ok=True)
        (ROOT / "debs" / kind["id"]).mkdir(parents=True, exist_ok=True)
        (ROOT / "debs" / kind["id"] / "README.md").write_text(
            f"""# {kind['title']}

Chỉ tải file trong thư mục này nếu máy của bạn là **{kind['title']}**.

- Dùng cho: {kind['who']}
- Nhận biết: {kind['how']}
- File: {kind['file']}

Cài: tải `.deb` → Filza → mở file → Cài đặt → Respring.

Sileo/Zebra: thêm `{conf['BASE_URL']}` — app tự chọn đúng loại, không cần tải tay.

Credit: Jinken Nguyen - 1989
""",
            encoding="utf-8",
        )
        html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_escape(kind['title'])} — Jinken Repo</title>
<link rel="icon" href="../CydiaIcon.png">
<style>{SITE_CSS}</style>
</head>
<body>
<nav class="nav-bar">
  <div class="nav-inner">
    <a class="brand" href="../">
      <img class="brand-icon" src="../CydiaIcon.png" alt="Icon">
      <span>Jinken Repo</span>
    </a>
    <div class="nav-links">
      <a href="../">Trang chủ</a>
      <a href="../rootless/" class="{'active' if kind['id']=='rootless' else ''}">Rootless</a>
      <a href="../rootful/" class="{'active' if kind['id']=='rootful' else ''}">Rootful</a>
      <a href="../roothide/" class="{'active' if kind['id']=='roothide' else ''}">RootHide</a>
    </div>
  </div>
</nav>

<header class="hero">
  <div class="hero-inner">
    <span class="badge"><span class="badge-dot"></span> {html_escape(kind['title'])} · {html_escape(kind['arch'])}</span>
    <h1>Kho Tweak {html_escape(kind['title'])}</h1>
    <p class="sub">Tối ưu chính xác cho nền tảng {html_escape(kind['title'])}. Không gây xung đột hay văng SpringBoard.</p>
    <div class="hero-actions">
      <a class="btn primary" href="#files">Xem danh sách tweak</a>
      <a class="btn" href="../">← Về trang chủ</a>
    </div>
  </div>
</header>

<main class="wrap">
  <h2>Khả năng tương thích</h2>
  <div class="card">
    <p style="margin:0 0 10px;"><strong>Thiết bị &amp; Bản jailbreak:</strong> {html_escape(kind['who'])}</p>
    <p style="margin:0 0 10px;"><strong>Dấu hiệu nhận biết:</strong> {html_escape(kind['how'])}</p>
    <div class="arch-hint" style="margin-bottom:0;">Tên tệp chuẩn: <strong>{html_escape(kind['file'])}</strong></div>
  </div>

  <h2>Hướng dẫn cài đặt nhanh (Filza)</h2>
  <div class="card">
    <ol class="steps">
      <li>Xác nhận máy đúng chuẩn <strong>{html_escape(kind['title'])}</strong>.</li>
      <li>Bấm <strong>Tải .deb</strong> của tweak bên dưới (mở bằng Safari trên iPhone).</li>
      <li>Mở ứng dụng <strong>Filza File Manager</strong> → chọn tệp vừa tải → <strong>Cài đặt (Install)</strong>.</li>
      <li>Khởi động lại SpringBoard (<strong>Respring</strong>) và mở <strong>Cài đặt (Settings)</strong> để cấu hình tweak.</li>
    </ol>
  </div>

  <h2 id="files">Danh sách Tweak {html_escape(kind['title'])}</h2>
  <div class="grid">{''.join(cards) if cards else '<p>Chưa có gói cho kiến trúc này.</p>'}</div>

  <footer>
    Credit: Jinken Nguyen - 1989 · Donate: {html_escape(conf['DONATE_BANK'])} {html_escape(conf['DONATE_ACCOUNT'])} {html_escape(conf['DONATE_NAME'])}
  </footer>
</main>
</body>
</html>
"""
        (ROOT / kind["id"] / "index.html").write_text(html, encoding="utf-8")


def write_index(packages: dict[str, dict], conf: dict) -> None:
    write_kind_pages(packages, conf)
    
    # Load tags from catalog.json if available
    tweak_tags = {}
    cat_file = ROOT / "catalog.json"
    if cat_file.is_file():
        try:
            with cat_file.open(encoding="utf-8") as f:
                cat_data = json.load(f)
                for t in cat_data.get("tweaks", []):
                    tweak_tags[t["id"]] = t.get("tag", "Tiện ích")
        except Exception:
            pass

    kind_cards = []
    for kind in KIND_GUIDES:
        n = sum(1 for info in packages.values() if kind["arch"] in info.get("files", {}))
        badge_cls = kind["id"]
        kind_cards.append(
            f"""
<article class="card arch-card">
  <div>
    <div class="arch-header">
      <h3 class="arch-title">{html_escape(kind['title'])}</h3>
      <span class="arch-badge {badge_cls}">{html_escape(kind['arch'])} · {n} tweak</span>
    </div>
    <p class="arch-desc"><strong>Dành cho:</strong> {html_escape(kind['who'])}</p>
    <p class="arch-desc">{html_escape(kind['how'])}</p>
    <div class="arch-hint">{html_escape(kind['file'])}</div>
  </div>
  <a class="btn" style="margin-top:10px;width:100%;" href="{html_escape(kind['id'])}/">Mở thư mục {html_escape(kind['title'])} →</a>
</article>"""
        )

    tweak_cards = []
    for pkg, info in sorted(packages.items(), key=lambda kv: kv[1]["Name"].lower()):
        vi, en = BLURBS.get(pkg, (info.get("blurb", ""), ""))
        tag = tweak_tags.get(pkg, "Tiện ích")
        links = []
        for kind in KIND_GUIDES:
            href = info.get("files", {}).get(kind["arch"])
            if href:
                cls = "roothide" if kind["id"] == "roothide" else ""
                links.append(f'<a class="dl-chip {cls}" href="{html_escape(href)}">{html_escape(kind["title"])}</a>')
        
        ipa_file = None
        if pkg == "com.jinken.englishkids":
            ipa_file = ROOT / "extras" / "EnglishKids.ipa"
        elif pkg == "com.jinken.drawkids":
            ipa_file = ROOT / "extras" / "BeHocVe.ipa"
        ipa_link = f' <a class="dl-chip ipa" href="{ipa_file.relative_to(ROOT)}">IPA (iOS)</a>' if ipa_file and ipa_file.is_file() else ""

        apk_file = None
        if pkg == "com.jinken.englishkids":
            apk_file = ROOT / "extras" / "EnglishKids.apk"
        elif pkg == "com.jinken.drawkids":
            apk_file = ROOT / "extras" / "BeHocVe.apk"
        apk_link = f' <a class="dl-chip apk" href="{apk_file.relative_to(ROOT)}">APK (Android)</a>' if apk_file and apk_file.is_file() else ""

        is_app = 1 if (ipa_link or apk_link or "com.jinkennguyen.jinken" in pkg) else 0

        tweak_cards.append(
            f"""
<article class="card tweak-card" data-name="{html_escape(info['Name'].lower())}" data-pkg="{html_escape(pkg.lower())}" data-desc="{html_escape(vi.lower())}" data-isapp="{is_app}">
  <div class="tweak-top">
    <div class="tweak-head">
      <div>
        <h3 class="tweak-title">{html_escape(info['Name'])}</h3>
        <span class="tweak-tag">{html_escape(tag)}</span>
      </div>
      <span class="tweak-ver">v{html_escape(info['Version'])}</span>
    </div>
    <p class="tweak-desc">{html_escape(vi)}</p>
    <p class="tweak-en">{html_escape(en)}</p>
    <div class="tweak-downloads">
      {' '.join(links)}{ipa_link}{apk_link}
    </div>
  </div>
  <div class="tweak-actions">
    <a class="btn" style="padding:6px 14px;font-size:13px;width:100%;" href="depictions/{html_escape(pkg)}/">Xem chi tiết &amp; Hướng dẫn →</a>
  </div>
</article>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jinken Repo — Jinken Nguyen - 1989</title>
<meta name="description" content="Official Cydia, Sileo, Zebra repository by Jinken Nguyen - 1989. Fully compatible with Rootless, Rootful, and RootHide (Dopamine & Bootstrap).">
<link rel="icon" href="CydiaIcon.png">
<style>{SITE_CSS}</style>
</head>
<body>

<nav class="nav-bar">
  <div class="nav-inner">
    <a class="brand" href="#">
      <img class="brand-icon" src="CydiaIcon.png" alt="Jinken Repo Icon">
      <span>Jinken Repo</span>
    </a>
    <div class="nav-links">
      <a href="#install">Cài đặt Source</a>
      <a href="#tweaks">Kho Tweak ({len(packages)})</a>
      <a href="#apps">Ứng dụng</a>
      <a href="#donate">Ủng hộ</a>
    </div>
  </div>
</nav>

<header class="hero">
  <div class="hero-inner">
    <div class="badge">
      <span class="badge-dot"></span> Sileo · Zebra · Cydia · TrollStore
    </div>
    <h1>Kho Tweak &amp; Ứng Dụng Jailbreak</h1>
    <p class="sub">Phát triển bởi <strong>Jinken Nguyen - 1989</strong>. Tương thích 100% trên cả 3 nền tảng <strong>Rootless</strong>, <strong>Rootful</strong> và <strong>RootHide</strong> (Dopamine &amp; RootHide Bootstrap).</p>
    <div class="hero-actions">
      <a class="btn primary" id="add-sileo" href="#">⚡ Thêm vào Sileo</a>
      <a class="btn" id="add-zebra" href="#">Thêm vào Zebra</a>
      <a class="btn" href="roothide/">RootHide (arm64e)</a>
      <a class="btn" href="rootless/">Rootless (arm64)</a>
      <a class="btn" href="rootful/">Rootful (arm)</a>
      <a class="btn gold" href="#donate">✨ Donate</a>
    </div>
  </div>
</header>

<main class="wrap">
  <h2 id="install">1. Chọn Nền Tảng Thiết Bị Của Bạn</h2>
  <p style="color:var(--text-secondary);margin:0 0 16px;">Để tránh lỗi cài đặt, vui lòng chọn đúng kiến trúc thiết bị nếu bạn tải file thủ công (.deb).</p>
  <div class="grid">{''.join(kind_cards)}</div>

  <h2>Cách Phân Biệt Nhanh Thiết Bị</h2>
  <div class="card">
    <ol class="steps">
      <li><strong>RootHide (Dopamine RootHide / RootHide Bootstrap)</strong>: Jailbreak ẩn triệt để đường dẫn jbroot, định dạng file <code>iphoneos-arm64e</code>. Toàn bộ tweak trên repo đều đã được vá chuẩn liên kết <code>libroothide</code> và <code>libsubstrate</code>.</li>
      <li><strong>Rootless (Dopamine chuẩn, palera1n rootless)</strong>: Máy có thư mục <code>/var/jb</code>, định dạng file kết thúc bằng <code>_iphoneos-arm64.deb</code>.</li>
      <li><strong>Rootful (unc0ver, checkra1n, Taurine, palera1n rootful)</strong>: Không có <code>/var/jb</code>, thư mục tweak nằm tại <code>/Library/MobileSubstrate</code>, định dạng <code>_iphoneos-arm.deb</code>.</li>
    </ol>
    <p style="color:var(--accent);margin:12px 0 0;font-size:14px;">💡 <em>Mẹo hay: Thêm trực tiếp đường dẫn nguồn vào Sileo hoặc Zebra, ứng dụng sẽ tự động chọn đúng bản vá phù hợp nhất cho máy bạn!</em></p>
  </div>

  <h2>Đường Dẫn Source APT</h2>
  <div class="code-box">
    <code id="source-url">{html_escape(conf['BASE_URL'])}</code>
    <button class="copy-btn copy" data-copy="{html_escape(conf['BASE_URL'])}">Sao chép URL</button>
  </div>

  <div class="search-container" id="tweaks">
    <div style="display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:10px;">
      <h2 style="margin:0;">Kho Tweak &amp; Ứng Dụng ({len(packages)})</h2>
      <span style="font-size:13px;color:var(--muted);" id="tweak-count">Đang hiển thị {len(packages)} mục</span>
    </div>
    <div class="search-bar-wrap">
      <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
      </svg>
      <input type="text" id="search-box" class="search-input" placeholder="Tìm kiếm tweak theo tên, tính năng hoặc package ID...">
    </div>
    <div class="filter-pills">
      <button class="filter-pill active" data-filter="all">Tất cả ({len(packages)})</button>
      <button class="filter-pill" data-filter="app">Ứng dụng độc lập (IPA/deb)</button>
      <button class="filter-pill" data-filter="tweak">Tweak hệ thống</button>
      <button class="filter-pill" data-filter="roothide">Đã vá RootHide 100%</button>
    </div>
  </div>

  <div class="grid" id="tweaks-grid">{''.join(tweak_cards)}</div>

  <h2 id="apps">Ứng Dụng Trực Tiếp (IPA cho iOS &amp; APK cho Android)</h2>
  <div class="grid" style="grid-template-columns:repeat(auto-fill, minmax(320px, 1fr));">
    <div class="card" style="border-color:rgba(52,211,153,0.3);">
      <div class="tweak-head">
        <h3 class="tweak-title">Bé học Vẽ</h3>
        <span class="tweak-ver" style="background:rgba(52,211,153,0.15);color:var(--good);">v1.6 (Build 7)</span>
      </div>
      <p class="tweak-desc">Ứng dụng học vẽ và tô màu tương tác cho bé: hướng dẫn từng nét vẽ con vật, đồ vật, pha màu, bảng vẽ tự do, chạy offline 100%.</p>
      <p class="tweak-en">Đã vá hoàn toàn lỗi sandbox RootHide, nạp tài nguyên an toàn không lo văng màn hình trắng.</p>
      <div class="tweak-downloads">
        <a class="btn primary" style="padding:8px 14px;font-size:13px;width:100%;margin-bottom:6px;" href="extras/BeHocVe.ipa">🍏 Tải file BeHocVe.ipa (7.5MB - iOS)</a>
        <a class="btn" style="padding:8px 14px;font-size:13px;width:100%;" href="extras/BeHocVe.apk">🤖 Tải file BeHocVe.apk (7.5MB - Android)</a>
      </div>
    </div>

    <div class="card" style="border-color:rgba(56,189,248,0.3);">
      <div class="tweak-head">
        <h3 class="tweak-title">English Kids</h3>
        <span class="tweak-ver">v1.7 (Build 13)</span>
      </div>
      <p class="tweak-desc">Ứng dụng học tiếng Anh tương tác cho trẻ em: từ vựng, âm thanh chuẩn bản ngữ, flashcard, mini-game, chạy offline 100%.</p>
      <p class="tweak-en">Đã nâng cấp quyền WebKit bundleURL, hiển thị tức thì trên RootHide, Rootless và TrollStore.</p>
      <div class="tweak-downloads">
        <a class="btn primary" style="padding:8px 14px;font-size:13px;width:100%;margin-bottom:6px;" href="extras/EnglishKids.ipa">🍏 Tải file EnglishKids.ipa (47MB - iOS)</a>
        <a class="btn" style="padding:8px 14px;font-size:13px;width:100%;" href="extras/EnglishKids.apk">🤖 Tải file EnglishKids.apk (50MB - Android)</a>
      </div>
    </div>
  </div>

  <h2>Ủng Hộ Tác Giả (Donate)</h2>
  <div class="card" id="donate">
    <div class="donate-grid">
      <img class="donate-qr" src="assets/vietqr.png" alt="VietQR MB Bank 0345140889 Nguyễn Tiến Triều">
      <div class="donate-info">
        <h3>✨ Repo này sống nhờ sự ủng hộ của bạn</h3>
        <p>Cảm ơn bạn đã tin dùng tweak miễn phí do mình tự tay phát triển. Mọi tweak đều miễn phí 100%, không quảng cáo, không mã độc hại. Một ly cà phê nhỏ sẽ tiếp thêm động lực để mình tiếp tục cập nhật và duy trì repo chạy ổn định lâu dài.</p>
        <div class="donate-table">
          <div class="donate-row">
            <span class="donate-label">Ngân hàng</span>
            <span class="donate-val">{html_escape(conf['DONATE_BANK'])}</span>
          </div>
          <div class="donate-row">
            <span class="donate-label">Chủ tài khoản</span>
            <span class="donate-val">{html_escape(conf['DONATE_NAME'])}</span>
          </div>
          <div class="donate-row">
            <span class="donate-label">Số tài khoản</span>
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="donate-val">{html_escape(conf['DONATE_ACCOUNT'])}</span>
              <button class="copy-btn copy" data-copy="{html_escape(conf['DONATE_ACCOUNT'])}">Copy STK</button>
            </div>
          </div>
          <div class="donate-row">
            <span class="donate-label">Nội dung chuyển khoản</span>
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="donate-val">Donate Jinken Nguyen {html_escape(conf['YEAR'])}</span>
              <button class="copy-btn copy" data-copy="Donate Jinken Nguyen {html_escape(conf['YEAR'])}">Copy ND</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <footer>
    <strong>Jinken Repo</strong> · Tác giả: <strong>Jinken Nguyen - 1989</strong><br>
    Được tối ưu chuẩn hoá cho iOS 14 – 18 · Rootless, Rootful &amp; RootHide.<br>
    Donate: MB Bank {html_escape(conf['DONATE_ACCOUNT'])} ({html_escape(conf['DONATE_NAME'])})
  </footer>
</main>

<script>
const base = location.origin + location.pathname.replace(/index\\.html$/, "").replace(/\\/$/, "");
const src = base + "/";
const srcBox = document.getElementById("source-url");
if (srcBox) srcBox.textContent = src;

const sBtn = document.getElementById("add-sileo");
if (sBtn) sBtn.href = "sileo://source/" + src;

const zBtn = document.getElementById("add-zebra");
if (zBtn) zBtn.href = "zbr://sources/add/" + src;

// Copy button logic with smooth feedback
document.querySelectorAll(".copy").forEach(el => {{
  el.addEventListener("click", async () => {{
    const text = el.dataset.copy || src;
    try {{
      await navigator.clipboard.writeText(text);
      const originalText = el.textContent;
      el.textContent = "✓ Đã copy!";
      el.style.background = "var(--good)";
      el.style.color = "#042033";
      setTimeout(() => {{
        el.textContent = originalText;
        el.style.background = "";
        el.style.color = "";
      }}, 2000);
    }} catch (e) {{
      alert(text);
    }}
  }});
}});

// Interactive search and filtering
const searchBox = document.getElementById("search-box");
const filterPills = document.querySelectorAll(".filter-pill");
const tweakCards = document.querySelectorAll("#tweaks-grid .tweak-card");
const counter = document.getElementById("tweak-count");

let activeFilter = "all";

function filterTweaks() {{
  const query = (searchBox ? searchBox.value : "").trim().toLowerCase();
  let visible = 0;

  tweakCards.forEach(card => {{
    const name = card.dataset.name || "";
    const pkg = card.dataset.pkg || "";
    const desc = card.dataset.desc || "";
    const isApp = card.dataset.isapp === "1";

    const matchesQuery = !query || name.includes(query) || pkg.includes(query) || desc.includes(query);
    let matchesCategory = true;
    if (activeFilter === "app") matchesCategory = isApp;
    else if (activeFilter === "tweak") matchesCategory = !isApp;
    else if (activeFilter === "roothide") matchesCategory = true; // All 20 are RootHide patched!

    if (matchesQuery && matchesCategory) {{
      card.style.display = "";
      visible++;
    }} else {{
      card.style.display = "none";
    }}
  }});

  if (counter) counter.textContent = "Đang hiển thị " + visible + " mục";
}}

if (searchBox) searchBox.addEventListener("input", filterTweaks);

filterPills.forEach(pill => {{
  pill.addEventListener("click", () => {{
    filterPills.forEach(p => p.classList.remove("active"));
    pill.classList.add("active");
    activeFilter = pill.dataset.filter;
    filterTweaks();
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

Chọn **đúng thư mục** rồi tải. Cài nhầm loại thì tweak không chạy.

| Thư mục | File | Máy |
| --- | --- | --- |
| [rootless/](rootless/) | `_iphoneos-arm64.deb` | Dopamine, palera1n rootless (`/var/jb`) |
| [rootful/](rootful/) | `_iphoneos-arm.deb` | unc0ver, checkra1n, palera1n rootful |
| [roothide/](roothide/) | `_iphoneos-arm64e.deb` | Dopamine RootHide / RootHide Bootstrap |

Deb files: [`debs/rootless/`](debs/rootless/), [`debs/rootful/`](debs/rootful/), [`debs/roothide/`](debs/roothide/).

Sileo/Zebra vẫn tự chọn gói khi thêm source — không cần tải tay.

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

1. Drop files into `debs/rootless/`, `debs/rootful/` or `debs/roothide/`
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
        folder = ARCH_DIR.get(arch, arch)
        dest = debs_dir / folder / dest_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        keep_debs.add(f"{folder}/{dest_name}")
        info = packages.setdefault(
            pkg,
            {
                "Name": fields.get("Name", pkg),
                "Version": ver,
                "Section": fields.get("Section", "Tweaks"),
                "archs": [],
                "files": {},
                "blurb": fields.get("Description", "").split("\n", 1)[0],
                "fields": fields,
            },
        )
        if arch not in info["archs"]:
            info["archs"].append(arch)
        info["archs"].sort()
        info["files"][arch] = f"debs/{folder}/{dest_name}"

        icon = find_icon(pkg)
        if icon:
            try:
                ensure_png(icon, icons_dir / f"{pkg}.png", 120)
            except Exception as exc:
                print(f"icon skip {pkg}: {exc}")

    for leftover in debs_dir.rglob("*.deb"):
        rel = leftover.relative_to(debs_dir).as_posix()
        if rel not in keep_debs:
            leftover.unlink()
    # keep extras/*.ipa if present
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
        changelog = public_changelog(pkg, read_changelog(pkg))
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

    # Packages index — scan each jailbreak folder so Filename is debs/rootless/...
    scan_out = []
    for folder in ("rootful", "rootless", "roothide"):
        scan_dir = debs_dir / folder
        if not scan_dir.is_dir() or not any(scan_dir.glob("*.deb")):
            continue
        proc = subprocess.run(
            ["dpkg-scanpackages", "-m", f"debs/{folder}", "/dev/null"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        scan_out.append(proc.stdout.strip())
    blocks = [b for b in "\n\n".join(scan_out).split("\n\n") if b.strip()]
    rewritten = []
    for block in blocks:
        lines = []
        pkg = None
        skip_desc = False
        for line in block.splitlines():
            if line.startswith("Package:"):
                pkg = line.split(":", 1)[1].strip()
            if line.startswith("Description:"):
                skip_desc = True
                continue
            if skip_desc and (line[:1] in " \t"):
                continue
            skip_desc = False
            if line.startswith(("Depiction:", "SileoDepiction:", "Sileodepiction:", "Homepage:", "Icon:")):
                continue
            lines.append(line)
        if pkg:
            vi, _en = BLURBS.get(pkg, ("", ""))
            if vi:
                lines.append(f"Description: {vi}")
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
    write_dists(conf, now, split_packages_by_arch(packages_text))

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
    jcat = CODE / "Jinken" / "app" / "Resources" / "catalog.json"
    if jcat.is_file():
        shutil.copy2(jcat, ROOT / "catalog.json")
    write_readme(packages, conf)

    print(f"Packages: {len(packages)}")
    for pkg, info in sorted(packages.items()):
        print(f"  {info['Name']:20} {info['Version']:8} {','.join(info['archs'])}")
    print(f"BASE_URL={base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
