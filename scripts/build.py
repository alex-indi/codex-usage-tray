from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
STAGING = ROOT / "build" / "release-staging"


def main() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_assets.py")], check=True)
    if STAGING.exists():
        shutil.rmtree(STAGING)
    pyinstaller_dist = STAGING / "pyinstaller-dist"
    pyinstaller_work = STAGING / "pyinstaller-work"
    subprocess.run(
        [
            sys.executable,
            "-X",
            "frozen_modules=off",
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--windowed",
            "--name",
            "CodexUsageTray",
            "--distpath",
            str(pyinstaller_dist),
            "--workpath",
            str(pyinstaller_work),
            "--specpath",
            str(STAGING),
            "--icon",
            str(ROOT / "assets" / "icon.ico"),
            "--manifest",
            str(ROOT / "packaging" / "CodexUsageTray.manifest"),
            str(ROOT / "src" / "codex_usage_tray" / "__main__.py"),
        ],
        cwd=ROOT,
        check=True,
    )
    built_executable = pyinstaller_dist / "CodexUsageTray.exe"
    release = STAGING / "CodexUsageTray-windows-x64"
    release.mkdir(parents=True)
    shutil.copy2(built_executable, release / "CodexUsageTray.exe")
    shutil.copy2(ROOT / "LICENSE", release / "LICENSE")
    digest = hashlib.sha256(built_executable.read_bytes()).hexdigest()
    checksum = release / "SHA256SUMS.txt"
    checksum.write_text(f"{digest}  CodexUsageTray.exe\n", encoding="ascii")
    DIST.mkdir(exist_ok=True)
    archive = shutil.make_archive(str(DIST / "CodexUsageTray-windows-x64"), "zip", root_dir=release)
    shutil.copy2(checksum, DIST / "SHA256SUMS.txt")
    destination = DIST / "CodexUsageTray.exe"
    try:
        shutil.copy2(built_executable, destination)
    except PermissionError:
        destination = DIST / "CodexUsageTray.new.exe"
        shutil.copy2(built_executable, destination)
        print(f"The running app kept the old EXE locked. New EXE: {destination}")
    print(archive)


if __name__ == "__main__":
    main()
