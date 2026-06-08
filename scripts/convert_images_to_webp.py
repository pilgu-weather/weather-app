from argparse import ArgumentParser
from pathlib import Path

from PIL import Image, ImageOps, features


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def ensure_webp_support():
    try:
        webp_supported = features.check("webp")
    except Exception:
        webp_supported = False

    if not webp_supported:
        raise SystemExit(
            "Pillow WebP support is not available. Install Pillow with "
            "libwebp support, then rerun this script."
        )


def convert_image(path, max_width, quality, force):
    output_path = path.with_suffix(".webp")

    if (
        output_path.exists()
        and not force
        and output_path.stat().st_mtime >= path.stat().st_mtime
    ):
        return "skipped", output_path

    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)

        if image.width > max_width:
            ratio = max_width / image.width
            target_size = (
                max_width,
                max(1, round(image.height * ratio))
            )
            image = image.resize(
                target_size,
                Image.Resampling.LANCZOS
            )

        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "A" in image.mode else "RGB")

        image.save(
            output_path,
            "WEBP",
            quality=quality,
            method=6
        )

    return "converted", output_path


def iter_images(paths):
    for root in paths:
        root_path = Path(root)

        if root_path.is_file():
            candidates = [root_path]
        else:
            candidates = root_path.rglob("*")

        for path in candidates:
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                yield path


def main():
    parser = ArgumentParser(
        description="Convert Weather Fit images to resized WebP copies."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=[
            "static/styles",
            "static/background"
        ],
        help="Files or directories to convert."
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=1200,
        help="Resize images wider than this width."
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=78,
        help="WebP quality, 1-100."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate WebP files even when they are newer."
    )

    args = parser.parse_args()
    ensure_webp_support()

    converted = 0
    skipped = 0

    for image_path in iter_images(args.paths):
        status, output_path = convert_image(
            image_path,
            args.max_width,
            args.quality,
            args.force
        )

        if status == "converted":
            converted += 1
        else:
            skipped += 1

        print(f"{status}: {image_path} -> {output_path}")

    print(
        f"done: {converted} converted, {skipped} skipped"
    )


if __name__ == "__main__":
    main()
