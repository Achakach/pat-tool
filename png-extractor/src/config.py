import json
import sys


def load_config(path: str) -> dict:
    """Load and validate config.json.

    Args:
        path: Path to config JSON file.

    Returns:
        dict with 'input_folder' and 'output_folder' keys.

    Exits with code 1 on missing file or invalid schema.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        print(f"Config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Invalid config: missing 'input_folder' or 'output_folder'", file=sys.stderr)
        sys.exit(1)

    if not isinstance(cfg, dict):
        print("Invalid config: missing 'input_folder' or 'output_folder'", file=sys.stderr)
        sys.exit(1)

    input_folder = cfg.get("input_folder")
    output_folder = cfg.get("output_folder")

    if not isinstance(input_folder, str) or not isinstance(output_folder, str):
        print("Invalid config: missing 'input_folder' or 'output_folder'", file=sys.stderr)
        sys.exit(1)

    return {"input_folder": input_folder, "output_folder": output_folder}
