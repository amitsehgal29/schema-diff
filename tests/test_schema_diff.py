import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

import schema_diff

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, os.pardir, "samples")


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = schema_diff.main(list(args))
    return code, out.getvalue(), err.getvalue()


class DiffSchemasTests(unittest.TestCase):
    def test_identical_is_not_breaking(self):
        s = {"id": "int", "email": "string"}
        r = schema_diff.diff_schemas(s, dict(s))
        self.assertEqual(r, {"added": [], "removed": [], "type_changes": [], "breaking": False})

    def test_added_only_is_not_breaking(self):
        r = schema_diff.diff_schemas({"id": "int"}, {"id": "int", "email": "string"})
        self.assertEqual(r["added"], [{"column": "email", "type": "string"}])
        self.assertFalse(r["breaking"])

    def test_removed_is_breaking(self):
        r = schema_diff.diff_schemas({"id": "int", "email": "string"}, {"id": "int"})
        self.assertEqual(r["removed"], [{"column": "email", "type": "string"}])
        self.assertTrue(r["breaking"])

    def test_type_change_is_breaking(self):
        r = schema_diff.diff_schemas({"id": "int"}, {"id": "bigint"})
        self.assertEqual(r["type_changes"], [{"column": "id", "from": "int", "to": "bigint"}])
        self.assertTrue(r["breaking"])

    def test_ignore_case(self):
        r = schema_diff.diff_schemas({"id": "INT"}, {"id": "int"}, ignore_case=True)
        self.assertFalse(r["breaking"])
        r = schema_diff.diff_schemas({"id": "INT"}, {"id": "int"})
        self.assertTrue(r["breaking"])

    def test_validate_rejects_non_object(self):
        with self.assertRaises(schema_diff.SchemaError):
            schema_diff.validate_schema(["id", "int"])
        with self.assertRaises(schema_diff.SchemaError):
            schema_diff.validate_schema({"id": 5})


class CliTests(unittest.TestCase):
    def test_samples_breaking_exit_1(self):
        code, out, _ = run_cli(os.path.join(SAMPLES, "orders_v1.json"),
                               os.path.join(SAMPLES, "orders_v2.json"))
        self.assertEqual(code, 1)
        r = json.loads(out)
        self.assertEqual(r["added"], [{"column": "currency", "type": "string"}])
        self.assertEqual(r["removed"], [{"column": "legacy_flag", "type": "boolean"}])
        self.assertEqual(r["type_changes"], [{"column": "order_id", "from": "int", "to": "bigint"}])
        self.assertTrue(r["breaking"])

    def test_non_breaking_exit_0(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a.json"), os.path.join(d, "b.json")
            with open(a, "w") as fh:
                json.dump({"id": "int"}, fh)
            with open(b, "w") as fh:
                json.dump({"id": "int", "name": "string"}, fh)
            code, out, _ = run_cli(a, b, "--compact")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 1)
        self.assertFalse(json.loads(out)["breaking"])

    def test_invalid_json_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            bad = os.path.join(d, "bad.json")
            with open(bad, "w") as fh:
                fh.write("{not json")
            code, _, err = run_cli(bad, bad)
        self.assertEqual(code, 2)
        self.assertIn("invalid JSON", err)


if __name__ == "__main__":
    unittest.main()
