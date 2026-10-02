"""Write a flat wheel index (pip --find-links / uv `format = "flat"`) page.

The page links every wheel in a release by its GitHub Release asset URL, with
a `#sha256=` fragment so installers verify the download. It lists one release
only: every release ships the same filenames (zeroc_ice-3.6.5-...), so listing
several would give the resolver duplicate candidates.

Usage:
    python scripts/make_index.py --dist dist \
        --base-url https://github.com/HocheggerLab/ice-wheels/releases/download/<tag> \
        --out site/index.html
"""

import argparse
import hashlib
import html
from pathlib import Path


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 digest of a file.

    Args:
        path: File to hash.

    Returns:
        Lowercase hex digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_index(wheels: list[Path], base_url: str, title: str) -> str:
    """Render the index HTML.

    Args:
        wheels: Wheel files to list, in display order.
        base_url: URL prefix that each wheel filename is appended to.
        title: Page title.

    Returns:
        The complete HTML document.
    """
    prefix = base_url.rstrip("/")
    rows = []
    for wheel in wheels:
        href = html.escape(f"{prefix}/{wheel.name}#sha256={sha256_of(wheel)}")
        rows.append(f'    <a href="{href}">{html.escape(wheel.name)}</a><br>')
    links = "\n".join(rows)
    return (
        "<!DOCTYPE html>\n<html>\n  <head>\n"
        f'    <meta charset="utf-8">\n    <title>{html.escape(title)}</title>\n'
        "  </head>\n  <body>\n"
        f"    <h1>{html.escape(title)}</h1>\n{links}\n"
        "  </body>\n</html>\n"
    )


def main() -> None:
    """Parse arguments and write the index page."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dist", type=Path, required=True, help="directory of .whl files")
    parser.add_argument("--base-url", required=True, help="release download URL prefix")
    parser.add_argument("--out", type=Path, required=True, help="index.html to write")
    parser.add_argument("--title", default="zeroc-ice wheels for OMERO (HocheggerLab)")
    args = parser.parse_args()

    wheels = sorted(args.dist.glob("*.whl"))
    if not wheels:
        raise SystemExit(f"no wheels found in {args.dist}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_index(wheels, args.base_url, args.title), encoding="utf-8")
    print(f"wrote {args.out} listing {len(wheels)} wheels")


if __name__ == "__main__":
    main()
