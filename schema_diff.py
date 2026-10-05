#!/usr/bin/env python3
"""schema-diff: compare two flat JSON schemas (column -> type) and flag breaking changes.

Standard library only. Exit code 1 when the change is breaking (a column was
removed or changed type), 0 otherwise, 2 on invalid input.
"""
import argparse
import json
import sys


class SchemaError(ValueError):
    """Raised when a schema file is not a flat {column: type} object."""


def load_schema(path):
    """Load a schema file and validate it is a JSON object of str -> str."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise SchemaError(f"{path}: invalid JSON ({exc})") from exc
    except OSError as exc:
        raise SchemaError(f"{path}: {exc.strerror}") from exc
    return validate_schema(data, path)


def validate_schema(data, label="schema"):
    if not isinstance(data, dict):
        raise SchemaError(f"{label}: expected a JSON object mapping column -> type")
    for col, typ in data.items():
        if not isinstance(typ, str):
            raise SchemaError(f"{label}: type for column {col!r} must be a string")
    return data


def diff_schemas(old, new, ignore_case=False):
    """Return a dict describing added, removed and type-changed columns."""
    norm = (lambda t: t.strip().lower()) if ignore_case else (lambda t: t.strip())
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    type_changes = [
        {"column": col, "from": old[col], "to": new[col]}
        for col in sorted(set(old) & set(new))
        if norm(old[col]) != norm(new[col])
    ]
    return {
        "added": [{"column": c, "type": new[c]} for c in added],
        "removed": [{"column": c, "type": old[c]} for c in removed],
        "type_changes": type_changes,
        "breaking": bool(removed or type_changes),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="schema-diff",
        description="Compare two JSON schema files ({column: type}) and report changes.",
    )
    parser.add_argument("old", help="path to the old/baseline schema JSON")
    parser.add_argument("new", help="path to the new/candidate schema JSON")
    parser.add_argument("--ignore-case", action="store_true",
                        help="treat types case-insensitively (e.g. INT == int)")
    parser.add_argument("--compact", action="store_true",
                        help="print single-line JSON instead of indented")
    args = parser.parse_args(argv)

    try:
        old = load_schema(args.old)
        new = load_schema(args.new)
    except SchemaError as exc:
        print(f"schema-diff: error: {exc}", file=sys.stderr)
        return 2

    result = diff_schemas(old, new, ignore_case=args.ignore_case)
    print(json.dumps(result, indent=None if args.compact else 2))
    return 1 if result["breaking"] else 0


if __name__ == "__main__":
    sys.exit(main())
