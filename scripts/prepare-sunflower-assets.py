"""Converte os originais do imagegen em arquivos WebP para o catálogo."""

import argparse
from pathlib import Path

from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--main", type=Path, required=True)
parser.add_argument("--detail", type=Path, required=True)
args = parser.parse_args()
target = Path(__file__).resolve().parents[1] / "dist" / "assets"
for name, original in (("sunflower", args.main), ("sunflower-detail", args.detail)):
    with Image.open(original) as source:
        photo = source.convert("RGB")
        photo.save(target / f"{name}.webp", "WEBP", quality=85, method=6)
        if name == "sunflower":
            photo.thumbnail((480, 600), Image.Resampling.LANCZOS)
            photo.save(target / "sunflower-small.webp", "WEBP", quality=83, method=6)
    print(target / f"{name}.webp")
