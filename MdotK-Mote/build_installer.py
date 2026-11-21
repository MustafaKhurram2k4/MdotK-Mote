"""Build a standalone Mote desktop app on the current native OS.

PyInstaller is not a cross-compiler. Run this script on Windows, macOS, or Linux
for that platform's output. GitHub Actions release builds zip the output.
"""
from __future__ import annotations
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main() -> None:
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 or newer is required.")
    system = platform.system()
    if system not in {"Windows", "Darwin", "Linux"}:
        raise SystemExit(f"Unsupported build OS: {system}")
    args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--name", "Mote"]
    if system == "Windows":
        args.append("--onefile")
    elif system == "Linux":
        args.append("--onefile")
    else:
        # macOS --windowed creates a .app bundle. Onedir is more reliable for
        # native app bundles than onefile; the release workflow zips the bundle.
        args.append("--onedir")
    sep = ";" if system == "Windows" else ":"
    args += ["--add-data", f"{ROOT / 'static'}{sep}static", "--collect-all", "keyring", "--collect-all", "zeroconf", "--collect-all", "qrcode"]
    args.append(str(ROOT / "desktop_app.py"))
    print(f"Building Mote for {system} on this machine...")
    subprocess.run(args, cwd=ROOT, check=True)
    if system == "Darwin":
        print(f"App bundle created in {ROOT / 'dist' / 'Mote.app'}")
    elif system == "Windows":
        print(f"Executable created in {ROOT / 'dist' / 'Mote.exe'}")
    else:
        print(f"Executable created in {ROOT / 'dist' / 'Mote'}")

if __name__ == "__main__":
    main()
