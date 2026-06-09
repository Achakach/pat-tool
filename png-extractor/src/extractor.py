from pathlib import Path
import zipfile
import sys


def extract_images(xlsx_path: Path, output_dir: Path) -> int:
    """Extract PNG images from an XLSX file's /xl/media/ directory.

    Args:
        xlsx_path: Path to the XLSX file.
        output_dir: Directory where extracted PNGs will be saved.

    Returns:
        Number of PNGs extracted (0 on failure).
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(xlsx_path, "r") as zf:
            media_members = [name for name in zf.namelist()
                             if name.startswith("xl/media/")]

            png_count = 0
            for name in media_members:
                if name.lower().endswith(".png"):
                    stem = xlsx_path.stem
                    out_name = f"_raw_{stem}_{png_count}.png"
                    out_path = output_dir / out_name

                    with zf.open(name) as src:
                        data = src.read()
                    if len(data) < 500:
                        continue  # skip noise/spacer images
                    with open(out_path, "wb") as dst:
                        dst.write(data)

                    png_count += 1
                else:
                    print(f"Warning: skipping non-PNG image: {name}",
                          file=sys.stderr)

            return png_count

    except zipfile.BadZipFile:
        print(f"Error: '{xlsx_path}' is not a valid ZIP/XLSX file",
              file=sys.stderr)
        return 0
    except PermissionError:
        print(f"Error: permission denied accessing '{xlsx_path}' or output directory",
              file=sys.stderr)
        return 0
