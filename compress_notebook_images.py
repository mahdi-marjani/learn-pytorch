#!/usr/bin/env python3
"""
compress_notebook_images.py

Shrinks image outputs embedded in a .ipynb file, in two ways:

1. Dedup: if a single output stores the same image in more than one format
   (e.g. both image/png and image/jpeg), keep only the smaller one.
2. Recompress: re-encode every remaining embedded image through Pillow as
   JPEG at a given quality, optionally downscaling it first. This can shrink
   even single-format outputs a lot, since notebooks often store raw/loosely
   compressed PNGs.

Usage:
    python compress_notebook_images.py input.ipynb output.ipynb
    python compress_notebook_images.py input.ipynb output.ipynb --quality 85 --max-width 1000
    python compress_notebook_images.py input.ipynb output.ipynb --no-recompress   # dedup only

Notes:
    - Only touches cell OUTPUTS (rendered results), never your source code.
    - Recompressing converts kept images to JPEG, so transparency (alpha
      channel) will be lost/flattened onto white. Use --no-recompress if any
      of your images need transparency.
    - Always writes to a NEW file; your original is never modified in place.
"""

import argparse
import base64
import io
import json
import sys

from PIL import Image

IMAGE_MIME_EXT = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/gif": "gif",
    "image/webp": "webp",
}


def recompress_b64_image(b64_data: str, quality: int, max_width: int | None) -> tuple[str, str]:
    """Decode a base64 image, optionally resize, re-encode as JPEG.
    Returns (new_base64_string, new_mime_type)."""
    raw = base64.b64decode(b64_data)
    img = Image.open(io.BytesIO(raw))

    # Flatten transparency onto white before JPEG (JPEG has no alpha channel)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if max_width and img.width > max_width:
        new_height = int(img.height * (max_width / img.width))
        img = img.resize((max_width, new_height), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    new_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return new_b64, "image/jpeg"


def process_notebook(nb: dict, quality: int, max_width: int | None, recompress: bool) -> dict:
    stats = {"deduped": 0, "recompressed": 0, "bytes_before": 0, "bytes_after": 0}

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            data = out.get("data")
            if not data:
                continue

            img_keys = [k for k in data if k in IMAGE_MIME_EXT]
            if not img_keys:
                continue

            # Step 1: dedup — keep only the smallest representation
            if len(img_keys) > 1:
                sizes = {k: len(data[k]) for k in img_keys}
                keep = min(sizes, key=sizes.get)
                for k in img_keys:
                    if k != keep:
                        del data[k]
                        stats["deduped"] += 1
                img_keys = [keep]

            # Step 2: recompress the remaining image
            if recompress:
                mime = img_keys[0]
                before = len(data[mime])
                stats["bytes_before"] += before
                try:
                    new_b64, new_mime = recompress_b64_image(data[mime], quality, max_width)
                except Exception as e:
                    print(f"  warning: could not recompress an image ({mime}): {e}", file=sys.stderr)
                    stats["bytes_after"] += before
                    continue

                # Only keep the recompressed version if it's actually smaller
                if len(new_b64) < before:
                    if mime != new_mime:
                        del data[mime]
                    data[new_mime] = new_b64
                    stats["recompressed"] += 1
                    stats["bytes_after"] += len(new_b64)
                else:
                    stats["bytes_after"] += before

    return stats


def main():
    parser = argparse.ArgumentParser(description="Shrink embedded image outputs in a Jupyter notebook.")
    parser.add_argument("input", help="Path to input .ipynb file")
    parser.add_argument("output", help="Path to write the shrunk .ipynb file")
    parser.add_argument("--quality", type=int, default=85, help="JPEG quality 1-95 (default: 85)")
    parser.add_argument("--max-width", type=int, default=None, help="Downscale images wider than this, in pixels")
    parser.add_argument("--no-recompress", action="store_true", help="Only dedup formats, skip re-encoding")
    args = parser.parse_args()

    with open(args.input) as f:
        nb = json.load(f)

    import os
    size_before = os.path.getsize(args.input)

    stats = process_notebook(nb, args.quality, args.max_width, recompress=not args.no_recompress)

    with open(args.output, "w") as f:
        json.dump(nb, f, indent=1)

    size_after = os.path.getsize(args.output)

    print(f"Deduplicated {stats['deduped']} redundant image representation(s)")
    if not args.no_recompress:
        print(f"Recompressed {stats['recompressed']} image(s)")
    print(f"File size: {size_before:,} bytes -> {size_after:,} bytes "
          f"({(1 - size_after / size_before) * 100:.1f}% smaller)")


if __name__ == "__main__":
    main()
