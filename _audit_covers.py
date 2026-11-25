"""One-off audit of topic cover files. Not part of the app."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT: Path = Path(__file__).resolve().parent / "frontend" / "public" / "topic-covers"
BACKEND_MANIFEST: Path = (
    Path(__file__).resolve().parent / "backend" / "app" / "data" / "topic_covers_manifest.json"
)
EXPECTED: set[str] = {f"{index:03d}.jpg" for index in range(1, 11)}


def main() -> None:
    manifest: dict[str, list[str]] = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    backend: dict[str, list[str]] = json.loads(BACKEND_MANIFEST.read_text(encoding="utf-8"))
    problems: list[str] = []
    rows: list[tuple[str, str, int, int, float, str, str, float]] = []

    folders: list[Path] = sorted(path for path in ROOT.iterdir() if path.is_dir())
    print("FOLDERS", len(folders))
    print("MANIFEST_MATCH_BACKEND", manifest == backend)
    print("DIRS_VS_MANIFEST", sorted(path.name for path in folders) == sorted(manifest))

    for folder in folders:
        names: set[str] = {path.name for path in folder.iterdir() if path.is_file()}
        missing: list[str] = sorted(EXPECTED - names)
        extra: list[str] = sorted(names - EXPECTED)
        manifest_names: list[str] = manifest.get(folder.name, [])
        if manifest_names != [f"{index:03d}.jpg" for index in range(1, 11)]:
            problems.append(f"{folder.name}: manifest list is not 001-010")
        if missing or extra:
            problems.append(f"{folder.name}: missing={missing or '-'} extra={extra or '-'}")
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    width, height = image.size
                    image_format: str = image.format or "?"
            except Exception as error:
                problems.append(f"{folder.name}/{path.name}: UNREADABLE {error}")
                continue
            ratio: float = round(width / height, 3) if height else 0.0
            if width > height * 1.05:
                orientation: str = "land"
            elif height > width * 1.05:
                orientation = "port"
            else:
                orientation = "square"
            size_kb: float = round(path.stat().st_size / 1024, 1)
            rows.append((folder.name, path.name, width, height, ratio, orientation, image_format, size_kb))

    widths: list[int] = [row[2] for row in rows]
    heights: list[int] = [row[3] for row in rows]
    sizes: list[float] = [row[7] for row in rows]
    print("COUNT", len(rows))
    print("ORIENT", dict(Counter(row[5] for row in rows)))
    print("FORMAT", dict(Counter(row[6] for row in rows)))
    print("WIDTH_MIN_MAX", min(widths), max(widths))
    print("HEIGHT_MIN_MAX", min(heights), max(heights))
    print("KB_MIN_MAX", min(sizes), max(sizes))
    print("TOTAL_MB", round(sum(sizes) / 1024, 1))
    print("---PROBLEMS---")
    if not problems:
        print("none")
    for problem in problems:
        print(problem)
    print("---OFF_TARGET---")
    off_target: int = 0
    for folder, name, width, height, ratio, orientation, image_format, size_kb in rows:
        flags: list[str] = []
        if image_format != "JPEG":
            flags.append("not-jpeg")
        if orientation != "land":
            flags.append(orientation)
        if abs(ratio - 1.5) > 0.08:
            flags.append(f"ratio={ratio}")
        if width < 1000:
            flags.append(f"narrow={width}")
        if width > 2500:
            flags.append(f"wide={width}")
        if size_kb > 800:
            flags.append(f"heavy={size_kb}kb")
        if flags:
            off_target += 1
            print(f"{folder}/{name} {width}x{height} {size_kb}kb " + ", ".join(flags))
    print("OFF_TARGET_COUNT", off_target)


if __name__ == "__main__":
    main()
