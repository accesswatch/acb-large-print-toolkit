"""Cross-platform build script for PyInstaller one-directory executables.

Detects the current OS and architecture, then builds a self-contained
directory named:
    acb-large-print-{os}-{arch}/

Supported targets (must be built natively -- PyInstaller cannot
cross-compile):
    Windows x64   (win-x64)     -- GitHub Actions: windows-latest
    Windows ARM64 (win-arm64)   -- GitHub Actions: windows-11-arm
    macOS x64     (macos-x64)   -- GitHub Actions: macos-13
    macOS ARM64   (macos-arm64) -- GitHub Actions: macos-latest (M1+)
    Linux x64     (linux-x64)   -- GitHub Actions: ubuntu-latest
    Linux ARM64   (linux-arm64) -- GitHub Actions: ubuntu-24.04-arm

Usage:
    python build.py              # Build for current platform
    python build.py --version-info  # Generate Windows version info only
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
ICON = ROOT / "installer" / "acb-large-print.ico"


def _detect_platform() -> tuple[str, str]:
    """Return (os_label, arch_label) for the current platform."""
    os_map = {"Windows": "win", "Darwin": "macos", "Linux": "linux"}
    arch_map = {
        "x86_64": "x64",
        "AMD64": "x64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    os_label = os_map.get(platform.system(), platform.system().lower())
    arch_label = arch_map.get(platform.machine(), platform.machine().lower())
    return os_label, arch_label


def _exe_name(os_label: str, arch_label: str, variant: str = "") -> str:
    """Build the output executable filename.

    variant: "" for GUI, "-cli" for CLI-only.
    """
    ext = ".exe" if os_label == "win" else ""
    return f"acb-large-print{variant}-{os_label}-{arch_label}{ext}"


def _build_one(
    *,
    entry_point: Path,
    name: str,
    os_label: str,
    arch_label: str,
    hidden: list[str],
    console: bool = True,
) -> Path:
    """Run PyInstaller for a single executable. Returns output path."""
    stem = name.rsplit(".", 1)[0] if os_label == "win" else name

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", stem,
        "--onedir",
        "--noconfirm",
        "--distpath", str(DIST),
        "--workpath", str(BUILD / "pyinstaller"),
        "--specpath", str(BUILD),
        "--paths", str(SRC),
    ]

    if os_label == "win" and console:
        cmd.append("--console")
    if os_label == "win" and not console:
        cmd.append("--windowed")

    # Windows-specific: version info and icon
    if os_label == "win":
        vi = ROOT / "installer" / "version_info.txt"
        if vi.exists():
            cmd.extend(["--version-file", str(vi)])
        if ICON.exists():
            cmd.extend(["--icon", str(ICON)])

    for mod in hidden:
        cmd.extend(["--hidden-import", mod])

    cmd.append(str(entry_point))

    print(f"\nBuilding: {name}")
    print(f"Entry:    {entry_point.name}")
    print(f"Command:  {' '.join(cmd)}")
    print()
    subprocess.run(cmd, check=True)

    # --onedir produces DIST/<stem>/<stem>[.exe]
    out_dir = DIST / stem
    exe_path = out_dir / name
    if exe_path.exists():
        total = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
        size_mb = total / (1024 * 1024)
        print(f"Built: {out_dir} ({size_mb:.1f} MB total)")
    else:
        print(f"Warning: Expected output not found at {exe_path}")
    return out_dir


def _zip_dir(directory: Path) -> Path:
    """Create a .zip archive of a --onedir output folder.

    Returns path to the .zip file (placed alongside the folder in DIST).
    """
    zip_path = directory.with_suffix(".zip")
    print(f"Packaging: {zip_path.name}")
    # shutil.make_archive wants the base name without .zip
    shutil.make_archive(str(directory), "zip", root_dir=str(DIST), base_dir=directory.name)
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Packaged: {zip_path.name} ({size_mb:.1f} MB)")
    return zip_path


def build_exe(*, os_label: str | None = None, arch_label: str | None = None) -> list[Path]:
    """Build both CLI and GUI executables with PyInstaller.

    Returns list of paths to built output directories.
    """
    if os_label is None or arch_label is None:
        os_label, arch_label = _detect_platform()

    print(f"Platform: {os_label}-{arch_label}")
    print(f"Python:   {sys.version}")

    # -- Shared hidden imports (CLI) --
    cli_hidden = [
        "acb_large_print",
        "acb_large_print.cli",
        "acb_large_print.auditor",
        "acb_large_print.fixer",
        "acb_large_print.exporter",
        "acb_large_print.template",
        "acb_large_print.reporter",
        "acb_large_print.constants",
        "mammoth",
        "mammoth.transforms",
        "mammoth.writers",
        "docx",
    ]

    # -- GUI hidden imports (superset of CLI) --
    has_wx = False
    try:
        import wx  # noqa: F401
        has_wx = True
    except ImportError:
        pass

    gui_hidden = list(cli_hidden)
    if has_wx:
        gui_hidden.extend([
            "acb_large_print.gui",
            "wx",
            "wx.adv",
        ])

    results: list[Path] = []

    # 1. CLI executable (console mode, no wxPython dependency)
    cli_entry = SRC / "acb_large_print" / "cli_main.py"
    cli_name = _exe_name(os_label, arch_label, "-cli")
    results.append(_build_one(
        entry_point=cli_entry,
        name=cli_name,
        os_label=os_label,
        arch_label=arch_label,
        hidden=cli_hidden,
        console=True,
    ))

    # 2. GUI executable (windowed mode, includes wxPython)
    if has_wx:
        gui_entry = SRC / "acb_large_print" / "__main__.py"
        gui_name = _exe_name(os_label, arch_label)
        results.append(_build_one(
            entry_point=gui_entry,
            name=gui_name,
            os_label=os_label,
            arch_label=arch_label,
            hidden=gui_hidden,
            console=False,
        ))
    else:
        print("\nwxPython not installed -- skipping GUI build")

    # Package each output directory as a portable .zip
    zips: list[Path] = []
    for p in results:
        if p.is_dir():
            zips.append(_zip_dir(p))

    print(f"\n{'='*50}")
    print(f"Build complete: {len(results)} build(s)")
    for p in results:
        if p.is_dir():
            total = sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
            print(f"  {p.name}/ ({total / (1024*1024):.1f} MB)")
    for z in zips:
        if z.exists():
            print(f"  {z.name} ({z.stat().st_size / (1024*1024):.1f} MB)")

    return results


def generate_version_info() -> None:
    """Generate PyInstaller version info file (Windows only)."""
    sys.path.insert(0, str(SRC))
    from acb_large_print import __version__

    parts = __version__.split(".")
    major = int(parts[0]) if len(parts) > 0 else 1
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0

    version_info_dir = ROOT / "installer"
    version_info_dir.mkdir(parents=True, exist_ok=True)

    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, 0),
    prodvers=({major}, {minor}, {patch}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'BITS - Blind Information Technology Solutions'),
            StringStruct(u'FileDescription', u'ACB Large Print Compliance Tool'),
            StringStruct(u'FileVersion', u'{__version__}'),
            StringStruct(u'InternalName', u'acb-large-print'),
            StringStruct(u'OriginalFilename', u'acb-large-print.exe'),
            StringStruct(u'ProductName', u'ACB Large Print Tool'),
            StringStruct(u'ProductVersion', u'{__version__}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    (version_info_dir / "version_info.txt").write_text(content, encoding="utf-8")
    print("Version info generated.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build ACB Large Print Tool executable")
    parser.add_argument(
        "--version-info", action="store_true",
        help="Generate Windows version info file only (no build)",
    )
    args = parser.parse_args()

    os_label, arch_label = _detect_platform()
    print(f"Detected platform: {os_label}-{arch_label}")

    if os_label == "win":
        generate_version_info()

    if not args.version_info:
        build_exe(os_label=os_label, arch_label=arch_label)
