"""Check the basic consistency of data.

Specifically, this script checks the following statements.

- IDs are unique in each data file
- IDs are consistent across data files
- `GB-T_7714—2025.original.toml`:
  - The `id-prefix` fields are properly formed.
  - The `headings` fields are consistent with `id-prefix` fields.
  - Entries included in multiple sections are consistent.

Usage:
    uv run scripts/check_consistency.py
"""

import json
import re
import tomllib
from pathlib import Path
from unicodedata import lookup


def load_original_sections(file: Path) -> dict[str, list[str]]:
    """Load the original.toml into a map from ID prefixes to examples."""
    data = tomllib.loads(file.read_text(encoding="utf-8"))

    for s in data["section"]:
        assert s["id-prefix"].startswith("gbt7714.")
        assert s["id-prefix"].endswith(":")

        assert len(s["headings"]) == s["id-prefix"].count(".")

    library = {s["id-prefix"]: s["examples"].splitlines() for s in data["section"]}
    assert len(library) == len(data["section"])
    return library


def check_original_consistency(original_library: dict[str, list[str]], /) -> None:
    """Check the consistency within original.toml."""

    def get_entry(id: str) -> str:
        prefix, n = id.split(":")
        entry = original_library[prefix + ":"][int(n) - 1]
        m = re.match(r"^(?:\[\d+\] )?(.+)$", entry)
        assert m is not None
        return m.group(1)

    def check_eq(
        id_a: str,
        id_b: str,
        /,
        *,
        ignore_space: bool = False,
        ignore_re: str | re.Pattern[str] | list[str | re.Pattern[str]] | None = None,
    ) -> None:
        assert id_a != id_b

        a = get_entry(id_a)
        b = get_entry(id_b)

        if ignore_re is not None:
            patterns = ignore_re if isinstance(ignore_re, list) else [ignore_re]
            for pattern in patterns:
                assert a != b, (
                    f"Expected to be unequal, but equal:\n{id_a}\n{a}\n==\n{id_b}\n{b}"
                )
                a = re.sub(pattern, r"\1", a)
                b = re.sub(pattern, r"\1", b)

        if ignore_space:
            assert a != b, (
                f"Expected to be unequal, but equal:\n{id_a}\n{a}\n==\n{id_b}\n{b}"
            )
            a = a.replace(" ", "")
            b = b.replace(" ", "")

        assert a == b, (
            f"Expected to be equal ({ignore_space=}, {ignore_re=!r}), but not:\n{id_a}\n{a}\n!=\n{id_b}\n{b}"
        )

    # %% 5.1 著录用文字
    check_eq("gbt7714.5.1:1", "gbt7714.b.1:16")
    check_eq("gbt7714.5.1:2", "gbt7714.b.1:17")
    check_eq("gbt7714.5.1:3", "gbt7714.b.1:24", ignore_space=True)

    # %% 7 著录通则
    # 顺序编码制与著者-出版年制对照
    check_eq(
        "gbt7714.7.1.3:1",
        "gbt7714.7.1.3:3",
        ignore_re=[r"(^)佚名,2023\.", r"(中国书法),2023 "],
    )
    check_eq(
        "gbt7714.7.1.3:2",
        "gbt7714.7.1.3:4",
        ignore_re=[r"(^)Anon,1981\.", r"(Br Med J,)1981,"],
    )

    # 其它完整例子
    check_eq("gbt7714.7.7:1", "gbt7714.b.1:2")
    check_eq("gbt7714.7.7:2", "gbt7714.b.1:6")
    check_eq("gbt7714.7.7:3", "gbt7714.b.1:7")
    check_eq("gbt7714.7.7:4", "gbt7714.b.2:4")
    check_eq("gbt7714.7.8:2", "gbt7714.b.1:23")
    check_eq("gbt7714.7.9.1:1", "gbt7714.b.1:25", ignore_space=True)

    # %% 8.1 著者-出版年制示例
    check_eq(
        "gbt7714.8.1:1",
        "gbt7714.b.1:1",
        ignore_re=[r"^(张伯伟),2002", r"(江苏古籍出版社,)2002:"],
    )
    check_eq(
        "gbt7714.8.1:2",
        "gbt7714.b.2:3",
        ignore_re=[r"^(程根伟),1999", r"(科学出版社,)1999:"],
        ignore_space=True,
    )
    check_eq(
        "gbt7714.8.1:3",
        "gbt7714.b.4:1",
        ignore_re=[r"^(杨洪升),2013", r"(文献,)2013 "],
    )
    check_eq(
        "gbt7714.8.1:4",
        "gbt7714.b.4:12",
        ignore_re=[r"^(Caplan P),1993", r"(Computer Systems Review,)1993,"],
    )
    check_eq(
        "gbt7714.8.1:5",
        "gbt7714.b.6:6",
        ignore_re=[r"^(Christou A),2024", r"(Wright State University),2024(?=:)"],
        ignore_space=True,
    )

    # %% 8.2 图书
    check_eq("gbt7714.8.2.2:1", "gbt7714.b.1:1")
    check_eq("gbt7714.8.2.2:2", "gbt7714.b.1:4")
    check_eq("gbt7714.8.2.2:3", "gbt7714.b.1:5")
    check_eq("gbt7714.8.2.2:4", "gbt7714.b.1:8")
    check_eq("gbt7714.8.2.2:5", "gbt7714.b.1:12")
    check_eq("gbt7714.8.2.2:6", "gbt7714.b.1:18")
    check_eq("gbt7714.8.2.2:7", "gbt7714.b.1:22", ignore_space=True)

    # %% 8.3 图书中的析出文献
    check_eq("gbt7714.8.3.2:1", "gbt7714.b.2:1")
    check_eq("gbt7714.8.3.2:2", "gbt7714.b.2:2", ignore_space=True)
    check_eq("gbt7714.8.3.2:3", "gbt7714.b.2:6", ignore_space=True)
    check_eq("gbt7714.8.3.2:4", "gbt7714.b.2:9")
    check_eq("gbt7714.8.3.2:5", "gbt7714.b.2:10", ignore_space=True)

    # %% 8.4 连续出版物
    check_eq("gbt7714.8.4.2:1", "gbt7714.b.3:1")
    check_eq("gbt7714.8.4.2:2", "gbt7714.b.3:2", ignore_space=True)
    check_eq("gbt7714.8.4.2:3", "gbt7714.b.3:3")
    check_eq("gbt7714.8.4.2:4", "gbt7714.b.3:4", ignore_space=True)

    # %% 8.5.3 连续出版物中的析出文献之完整例子
    check_eq("gbt7714.8.5.3:1", "gbt7714.b.4:2")
    check_eq("gbt7714.8.5.3:2", "gbt7714.b.4:4", ignore_space=True)
    check_eq("gbt7714.8.5.3:3", "gbt7714.b.4:3")
    check_eq("gbt7714.8.5.3:4", "gbt7714.b.4:8", ignore_re=r"(http)s(?=://)")
    check_eq("gbt7714.8.5.3:5", "gbt7714.b.4:9", ignore_space=True)
    check_eq("gbt7714.8.5.3:6", "gbt7714.b.4:10", ignore_space=True)
    check_eq("gbt7714.8.5.3:7", "gbt7714.b.4:11")
    check_eq("gbt7714.8.5.3:8", "gbt7714.b.4:13")
    check_eq("gbt7714.8.5.3:9", "gbt7714.b.4:17")
    check_eq("gbt7714.8.5.3:10", "gbt7714.b.4:20", ignore_space=True)

    # %% 8.6 会议录
    check_eq("gbt7714.8.6.1:1", "gbt7714.b.5:2", ignore_space=True)
    check_eq("gbt7714.8.6.1:2", "gbt7714.b.5:5")
    check_eq("gbt7714.8.6.1:3", "gbt7714.b.5:4")
    check_eq("gbt7714.8.6.1:4", "gbt7714.b.5:10", ignore_space=True)
    check_eq("gbt7714.8.6.1:5", "gbt7714.b.5:12", ignore_space=True)

    check_eq("gbt7714.8.6.3:1", "gbt7714.b.5:1")
    check_eq("gbt7714.8.6.3:2", "gbt7714.b.5:8", ignore_space=True)
    check_eq("gbt7714.8.6.3:3", "gbt7714.b.5:9", ignore_space=True)

    # %% 8.7 学位论文
    check_eq("gbt7714.8.7.2:1", "gbt7714.b.6:1", ignore_space=True)
    check_eq("gbt7714.8.7.2:2", "gbt7714.b.6:2", ignore_space=True)
    check_eq("gbt7714.8.7.2:3", "gbt7714.b.6:4", ignore_space=True)
    check_eq("gbt7714.8.7.2:4", "gbt7714.b.6:5", ignore_space=True)
    check_eq("gbt7714.8.7.2:5", "gbt7714.b.6:6", ignore_space=True)

    # %% 8.8 报告
    check_eq("gbt7714.8.8.3:1", "gbt7714.b.7:2", ignore_space=True)
    check_eq("gbt7714.8.8.3:2", "gbt7714.b.7:3")
    check_eq("gbt7714.8.8.3:3", "gbt7714.b.7:4", ignore_space=True)
    check_eq("gbt7714.8.8.3:4", "gbt7714.b.7:5", ignore_space=True)

    # %% 8.9 标准
    check_eq("gbt7714.8.9.2:1", "gbt7714.b.8:1")
    check_eq("gbt7714.8.9.2:2", "gbt7714.b.8:4")
    check_eq(
        "gbt7714.8.9.2:3",
        "gbt7714.b.8:2",
        ignore_re=r"/OL(\]\.)http://c\.gb688\.cn/.+$",
        ignore_space=True,
    )
    check_eq("gbt7714.8.9.2:4", "gbt7714.b.8:5")
    check_eq("gbt7714.8.9.2:5", "gbt7714.b.8:6", ignore_space=True)

    # %% 8.10 专利
    check_eq("gbt7714.8.10.2:1", "gbt7714.b.9:1")
    check_eq("gbt7714.8.10.2:2", "gbt7714.b.9:4")
    check_eq("gbt7714.8.10.2:3", "gbt7714.b.9:6")
    check_eq("gbt7714.8.10.2:4", "gbt7714.b.9:8")

    # %% 8.11 网站、网页
    check_eq("gbt7714.8.11.2.2:2", "gbt7714.b.10:9")

    check_eq("gbt7714.8.11.3.2:1", "gbt7714.b.10:4", ignore_space=True)
    check_eq("gbt7714.8.11.3.2:2", "gbt7714.b.10:6", ignore_space=True)
    check_eq("gbt7714.8.11.3.2:3", "gbt7714.b.10:5", ignore_space=True)
    check_eq("gbt7714.8.11.3.2:4", "gbt7714.b.10:11", ignore_space=True)
    check_eq("gbt7714.8.11.3.2:5", "gbt7714.b.10:13", ignore_re=r"(?:CP|EB)(/OL)")

    # %% 8.12 档案
    check_eq("gbt7714.8.12.3:1", "gbt7714.b.11:1")
    check_eq("gbt7714.8.12.3:2", "gbt7714.b.11:2")
    check_eq("gbt7714.8.12.3:3", "gbt7714.b.11:3", ignore_space=True)
    check_eq("gbt7714.8.12.3:4", "gbt7714.b.11:4")

    # %% 8.13 地图
    assert (
        # 使用 U+2236 Mathematical Operators RATIO
        f"1{lookup('RATIO')}" in (entry := get_entry("gbt7714.8.13.3:1"))
        # 而非 U+003A Basic Latin COLON
        and f"1{lookup('COLON')}" not in entry
    )

    check_eq("gbt7714.8.13.1:1", "gbt7714.b.12:6")
    check_eq("gbt7714.8.13.1:2", "gbt7714.b.12:7")
    check_eq("gbt7714.8.13.1:3", "gbt7714.b.12:9")
    check_eq("gbt7714.8.13.1:4", "gbt7714.b.12:10")

    check_eq("gbt7714.8.13.3:1", "gbt7714.b.12:1")
    check_eq("gbt7714.8.13.3:2", "gbt7714.b.12:2")
    check_eq("gbt7714.8.13.3:3", "gbt7714.b.12:5")

    # %% 8.14 数据集
    check_eq("gbt7714.8.14.3:1", "gbt7714.b.13:3")
    check_eq("gbt7714.8.14.3:2", "gbt7714.b.13:5", ignore_space=True)
    check_eq(
        "gbt7714.8.14.3:3",
        "gbt7714.b.13:9",
        ignore_re=r"(\(2021\)\[)(?:2025-07-15|2024-11-25)",
        ignore_space=True,
    )

    # %% 8.15 预印本
    check_eq("gbt7714.8.15.2:1", "gbt7714.b.14:2", ignore_space=True)
    check_eq("gbt7714.8.15.2:2", "gbt7714.b.14:1", ignore_space=True)
    check_eq(
        "gbt7714.8.15.2:3",
        "gbt7714.b.14:4",
        ignore_re=r"(V2\.)arXiv ",
        ignore_space=True,
    )

    # %% 9 参考文献标引体系编制法
    check_eq("gbt7714.9.2.1.3:4", "gbt7714.b.1:3")


def load_ids_from_original(original_library: dict[str, list[str]], /) -> set[str]:
    """Load the set of IDs from original.toml."""
    ids: set[str] = set()
    for id_prefix, examples in original_library.items():
        for i in range(len(examples)):
            ids.add(f"{id_prefix}{i + 1}")

    # 顺序编码制与著者-出版年制对照的例子只保留一份
    ids.remove("gbt7714.7.1.3:3")
    ids.remove("gbt7714.7.1.3:4")

    return ids


def load_ids_from_json(file: Path) -> set[str]:
    """Load the set of IDs in a CSL-JSON file."""
    id_list: list[str] = [
        entry["id"] for entry in json.loads(file.read_text(encoding="utf-8"))
    ]
    id_set = set(id_list)
    assert len(id_set) == len(id_list)
    return id_set


def load_ids_from_bib(file: Path) -> set[str]:
    """Load the set of IDs in a BibLaTeX file."""
    id_list: list[str] = re.findall(
        r"^@\w+\{([^,\s]+),",
        file.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    id_set = set(id_list)
    assert len(id_set) == len(id_list)
    return id_set


if __name__ == "__main__":
    from util import DATA_DIR

    original_library = load_original_sections(DATA_DIR / "GB-T_7714—2025.original.toml")
    original_ids = load_ids_from_original(original_library)

    for file in DATA_DIR.iterdir():
        print(f"Checking the consistency of {file.relative_to(DATA_DIR).as_posix()}…")

        match file.suffix:
            case ".bib":
                ids = load_ids_from_bib(file)
            case ".json":
                ids = load_ids_from_json(file)
            case _:
                assert file.suffix == ".toml"
                check_original_consistency(original_library)
                continue

        assert ids == original_ids, (
            f"Expect ids == original_ids, but:\n{ids - original_ids = }\n{original_ids - ids = }"
        )
