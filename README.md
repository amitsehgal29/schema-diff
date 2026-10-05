# schema-diff

A tiny, dependency-free CLI that compares two flat JSON schemas
(`{"column": "type"}`) and tells you what changed — and whether the change is
**breaking** for downstream consumers. Handy as a CI gate before deploying a
table/topic/contract change.

- **added** columns → non-breaking
- **removed** columns → breaking
- **type changes** → breaking

Python 3.8+ standard library only.

## Usage

```bash
python3 schema_diff.py OLD.json NEW.json [--ignore-case] [--compact]
```

Exit codes: `0` = no breaking change, `1` = breaking change, `2` = invalid input.

### Example (using the bundled samples)

`samples/orders_v1.json`:

```json
{"order_id": "int", "customer_email": "string", "amount": "decimal(10,2)",
 "legacy_flag": "boolean", "created_at": "timestamp"}
```

`samples/orders_v2.json`:

```json
{"order_id": "bigint", "customer_email": "string", "amount": "decimal(10,2)",
 "created_at": "timestamp", "currency": "string"}
```

```console
$ python3 schema_diff.py samples/orders_v1.json samples/orders_v2.json --compact
{"added": [{"column": "currency", "type": "string"}], "removed": [{"column": "legacy_flag", "type": "boolean"}], "type_changes": [{"column": "order_id", "from": "int", "to": "bigint"}], "breaking": true}
$ echo $?
1
```

### In CI

```bash
python3 schema_diff.py schemas/prod.json schemas/proposed.json || {
  echo "Breaking schema change detected"; exit 1; }
```

## Options

| Flag | Meaning |
|------|---------|
| `--ignore-case` | Compare types case-insensitively (`INT` == `int`) |
| `--compact` | Print single-line JSON |

## Tests

```bash
python3 -m unittest -v
```

## License

MIT
