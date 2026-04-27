from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


def generate_image_and_pdf(out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    image_path = out_dir / "vision_text.png"
    pdf_path = out_dir / "vision_text.pdf"

    img = Image.new("RGB", (1400, 800), "white")
    draw = ImageDraw.Draw(img)
    lines = [
        "GLOW OpenRouter Vision Test",
        "This image contains visible text for OCR.",
        "ACB Large Print check: Arial-like sans serif layout.",
        "Expected marker: VISION_TEXT_OK",
    ]
    y = 80
    for idx, line in enumerate(lines):
        draw.text((80, y + idx * 120), line, fill="black")

    img.save(image_path)
    img.save(pdf_path, "PDF", resolution=150.0)
    return image_path, pdf_path


def generate_clip(out_dir: Path) -> Path:
    src = Path(r"S:\code\bw\Samples\ronaldreaganchallengeraddressatt3232.mp3")
    clip = out_dir / "reagan-30s.mp3"
    if not src.exists():
        raise FileNotFoundError(f"Source MP3 not found: {src}")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-t",
        "30",
        str(clip),
    ]
    subprocess.run(cmd, check=True)
    return clip


def main() -> None:
    out = Path(__file__).resolve().parent
    image_path, pdf_path = generate_image_and_pdf(out)
    clip_path = generate_clip(out)
    print(f"PNG: {image_path}")
    print(f"PDF: {pdf_path}")
    print(f"MP3: {clip_path}")


if __name__ == "__main__":
    main()
