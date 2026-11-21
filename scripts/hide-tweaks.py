#!/usr/bin/env python3
# Script tạm thời ẩn hoặc hiển thị lại toàn bộ tweaks trên repo
# Sử dụng:
#   python3 scripts/hide-tweaks.py hide    -> Ẩn toàn bộ tweak
#   python3 scripts/hide-tweaks.py unhide  -> Khôi phục hiển thị lại toàn bộ tweak

import sys, os, shutil, subprocess, hashlib, gzip, json, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_conf(path: Path) -> dict[str, str]:
    conf = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf

def hide():
    conf = load_conf(ROOT / "repo.conf")
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S UTC")

    # Backup debs if not already backed up
    debs_dir = ROOT / "debs"
    backup_dir = ROOT / "debs_backup"
    if debs_dir.exists() and not backup_dir.exists():
        shutil.copytree(debs_dir, backup_dir)
        print("Đã sao lưu debs/ sang debs_backup/")

    # Xoá file deb trong debs/ nhưng giữ cấu trúc thư mục
    for d in ("rootful", "rootless", "roothide"):
        folder = debs_dir / d
        if folder.exists():
            for f in folder.glob("*.deb"):
                f.unlink()

    # 1. Packages rỗng
    pkg_file = ROOT / "Packages"
    pkg_file.write_text("", encoding="utf-8")
    with gzip.open(ROOT / "Packages.gz", "wt", encoding="utf-8") as gz:
        gz.write("")
    subprocess.check_call(["bzip2", "-kf", str(pkg_file)])

    pkg_bytes = pkg_file.read_bytes()
    gz_bytes = (ROOT / "Packages.gz").read_bytes()
    bz_bytes = (ROOT / "Packages.bz2").read_bytes()

    # 2. Release rỗng
    release = f"""Origin: {conf.get('ORIGIN', 'Jinken Repo')}
Label: {conf.get('LABEL', 'Jinken Repo')}
Suite: {conf.get('SUITE', 'stable')}
Version: {conf.get('VERSION', '1.0')}
Codename: {conf.get('CODENAME', 'ios')}
Date: {now}
Architectures: iphoneos-arm iphoneos-arm64 iphoneos-arm64e
Components: main
Description: {conf.get('DESCRIPTION', 'Jailbreak tweaks')}
MD5Sum:
 {hashlib.md5(pkg_bytes).hexdigest()} {len(pkg_bytes)} Packages
 {hashlib.md5(gz_bytes).hexdigest()} {len(gz_bytes)} Packages.gz
 {hashlib.md5(bz_bytes).hexdigest()} {len(bz_bytes)} Packages.bz2
SHA256:
 {hashlib.sha256(pkg_bytes).hexdigest()} {len(pkg_bytes)} Packages
 {hashlib.sha256(gz_bytes).hexdigest()} {len(gz_bytes)} Packages.gz
 {hashlib.sha256(bz_bytes).hexdigest()} {len(bz_bytes)} Packages.bz2
"""
    (ROOT / "Release").write_text(release, encoding="utf-8")

    # 3. dists
    dists = ROOT / "dists"
    if dists.exists():
        shutil.rmtree(dists)
    for suite in (conf.get("SUITE", "stable"), conf.get("CODENAME", "ios")):
        for arch in ("iphoneos-arm", "iphoneos-arm64", "iphoneos-arm64e"):
            bdir = dists / suite / "main" / f"binary-{arch}"
            bdir.mkdir(parents=True, exist_ok=True)
            (bdir / "Packages").write_text("", encoding="utf-8")
            with gzip.open(bdir / "Packages.gz", "wt", encoding="utf-8") as gz:
                gz.write("")
            subprocess.check_call(["bzip2", "-kf", str(bdir / "Packages")])
            (bdir / "Release").write_text(f"""Archive: {suite}
Origin: {conf.get('ORIGIN', 'Jinken Repo')}
Label: {conf.get('LABEL', 'Jinken Repo')}
Component: main
Architecture: {arch}
Description: {conf.get('DESCRIPTION', 'Jailbreak tweaks')}
""", encoding="utf-8")

        (dists / suite / "Release").write_text(release, encoding="utf-8")

    # 4. sileo-featured.json
    featured = {
        "class": "FeaturedBannersView",
        "itemSize": "{263, 148}",
        "itemCornerRadius": 12,
        "banners": []
    }
    (ROOT / "sileo-featured.json").write_text(json.dumps(featured, indent=2) + "\n", encoding="utf-8")

    # 5. catalog.json
    (ROOT / "catalog.json").write_text(json.dumps({"packages": []}, indent=2) + "\n", encoding="utf-8")

    # 6. index.html - cập nhật thông báo bảo trì / tạm ẩn
    index_html = ROOT / "index.html"
    if index_html.exists():
        content = index_html.read_text(encoding="utf-8")
        empty_notice = '<div class="grid" id="tweaks"><div class="card" style="text-align:center;padding:40px 20px;grid-column:1/-1;"><h3>🔒 Repo đang tạm ẩn toàn bộ tweak</h3><p style="color:#888;margin-top:10px;">Các gói tweak đang tạm thời bảo trì / cập nhật. Vui lòng quay lại sau!</p></div></div>\n\n  <h2>Ủng Hộ Tác Giả'
        content = re.sub(
            r'<div class="grid" id="tweaks">.*?</div>\s*<h2>Ủng Hộ Tác Giả',
            empty_notice,
            content,
            flags=re.DOTALL
        )
        index_html.write_text(content, encoding="utf-8")

    print("✅ ĐÃ ẨN TOÀN BỘ TWEAK THÀNH CÔNG!")
    print("- Packages, Release, dists: Đã xoá danh sách tweak")
    print("- sileo-featured.json, catalog.json: Đã làm rỗng")
    print("- debs/: File deb gốc đã được lưu an toàn trong debs_backup/")
    print("- index.html: Đã cập nhật trạng thái tạm ẩn")

def unhide():
    backup_dir = ROOT / "debs_backup"
    debs_dir = ROOT / "debs"
    if backup_dir.exists():
        for d in ("rootful", "rootless", "roothide"):
            src_folder = backup_dir / d
            dst_folder = debs_dir / d
            dst_folder.mkdir(parents=True, exist_ok=True)
            if src_folder.exists():
                for f in src_folder.glob("*.deb"):
                    shutil.copy2(f, dst_folder / f.name)
        shutil.rmtree(backup_dir)
        print("Đã phục hồi file deb từ debs_backup/")

    # Chạy lại script update-repo.py
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "update-repo.py")])
    print("✅ ĐÃ KHÔI PHỤC TOÀN BỘ TWEAK THÀNH CÔNG!")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("hide", "unhide"):
        print("Usage: python3 scripts/hide-tweaks.py [hide|unhide]")
        sys.exit(1)
    if sys.argv[1] == "hide":
        hide()
    elif sys.argv[1] == "unhide":
        unhide()
