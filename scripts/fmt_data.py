"""Sort entries by IDs, sort top-level fields by keys, and format indentations.

Usage:
    uv run scripts/fmt_data.py
"""

import json
import re
from collections import deque
from collections.abc import Generator
from pathlib import Path
from typing import Literal


def key_order(key: str) -> tuple[int | str, ...]:
    """Convert a CSL-JSON/BibLaTeX field key to a tuple for ordering."""
    if key == "id":
        return (0,)
    else:
        return (1, key.casefold())


def id_order(id: str) -> list[int | str | tuple[int, str | int]]:
    """Convert an entry ID to a list for ordering."""
    parts = re.split(r"([\.:])", id.casefold())
    return [(0, int(p)) if p.isdigit() else (1, p) for p in parts]


def fmt_json(file: Path) -> None:
    """Format a CSL-JSON file in-place."""
    library: list[dict[str, str | list | dict]] = json.loads(
        file.read_text(encoding="utf-8")
    )
    library.sort(
        key=lambda entry: id_order(
            entry["id"]  # type: ignore
        )
    )
    for i, entry in enumerate(library):
        keys = list(entry.keys())
        keys.sort(key=key_order)
        library[i] = {k: entry[k] for k in keys}

    file.write_text(
        json.dumps(library, ensure_ascii=False, indent="\t"),
        encoding="utf-8",
    )


def split_bib(library: str) -> Generator[str]:
    """Split a full BibLaTeX library into entries, with fields sorted."""
    current: deque[str] = deque()
    state: Literal["data", "post-data"] = "data"
    for line in library.strip().splitlines():
        match state:
            case "data":
                if line.startswith("@") or line == "}":
                    current.append(line)
                elif not line[0].strip():
                    current.append("\t" + line.lstrip())
                else:
                    # Save multi-line `note`s as a single item.
                    assert current[-1].split("=", 1)[0].strip() == "note", (
                        f"Unexpected line in BibLaTeX entry: {line = }, {current = }"
                    )
                    current[-1] += "\n" + line

                if line == "}":
                    fields = list(current)[1:-1]
                    if not fields[-1].endswith(","):
                        fields[-1] += ","
                    fields.sort(
                        key=lambda line: key_order(line.split("=", 1)[0].strip())
                    )
                    current = deque([current[0]] + fields + [current[-1]])
                    state = "post-data"
            case "post-data":
                if not line.startswith("%"):
                    yield "\n".join(current).strip()
                    current.clear()
                    state = "data"
                # Save comments after data (e.g., Zotero Better BibTeX quality report)
                current.append(line)

    remaining = "\n".join(current).strip()
    if remaining:
        yield remaining


def get_bib_id(entry: str) -> str:
    """Get the citation key of a BibLaTeX entry."""
    return entry.split("{", 1)[1].split(",", 1)[0]


assert get_bib_id("@article{key,\n\t…\n}") == "key"


def fmt_bib(file: Path) -> None:
    """Format a BibLaTeX file in-place."""
    library = file.read_text(encoding="utf-8")
    entries = list(split_bib(library))
    entries.sort(key=lambda entry: id_order(get_bib_id(entry)))
    file.write_text("\n\n".join(entries), encoding="utf-8")


if __name__ == "__main__":
    from util import DATA_DIR

    for file in DATA_DIR.iterdir():
        print(f"Formatting {file.relative_to(DATA_DIR).as_posix()}…")

        match file.suffix:
            case ".bib":
                fmt_bib(file)
            case ".json":
                fmt_json(file)
            case _:
                assert file.suffix == ".toml"
