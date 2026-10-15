"""Source-only adapter regression checks; no FABulous import or RTL execution."""
import ast
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'verify/fixtures/nf-tiny/fabulous/generate.py'
NEW = ROOT / 'verify/fixtures/fnd-06/generate.py'


class ReferenceGeneratorTests(unittest.TestCase):
    def test_historical_source_unchanged(self):
        self.assertEqual(hashlib.sha256(OLD.read_bytes()).hexdigest(),
                         '158197e2fcd82ea8fbdcf11115a26e425113e2a91d5fc73574d1006443d3e0cd')

    def test_only_reviewed_adapter_deltas(self):
        old = ast.parse(OLD.read_text())
        new = ast.parse(NEW.read_text())
        # Normalize documentation, relocated input lookup, official marker, and
        # additional identity metadata. Every remaining executable AST must match.
        new.body[0] = old.body[0]
        old_main = next(n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        new_main = next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        def assigned(node):
            return node.targets[0].id if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) else None
        index = next(i for i, n in enumerate(new_main.body) if assigned(n) == 'adapter')
        self.assertEqual([assigned(n) for n in new_main.body[index:index + 3]], ['adapter', 'fixture', 'here'])
        self.assertEqual(ast.unparse(new_main.body[index + 1].value), "adapter.parent.parent / 'nf-tiny'")
        self.assertEqual(ast.unparse(new_main.body[index + 2].value), "fixture / 'fabulous'")
        original = [n for n in old_main.body if assigned(n) in ('here', 'fixture')]
        new_main.body[index:index + 3] = original
        marker = next(n for n in new_main.body if isinstance(n, ast.Expr) and ast.unparse(n) == "(output / '.FABulous').mkdir()")
        marker_index = new_main.body.index(marker)
        mkdir_index = next(i for i, n in enumerate(new_main.body) if ast.unparse(n) == 'output.mkdir(parents=True)')
        context_index = next(i for i, n in enumerate(new_main.body) if assigned(n) == 'context')
        self.assertEqual(marker_index, mkdir_index + 1)
        self.assertLess(marker_index, context_index)
        new_main.body.remove(marker)
        record = next(n.value for n in new_main.body if assigned(n) == 'record')
        self.assertEqual([k.value for k in record.keys[:2]], ['generator_sources', 'execution_adjustments'])
        identities = record.values[0]
        self.assertEqual([k.value for k in identities.keys], ['historical', 'adapter'])
        historical, adapter = identities.values
        self.assertEqual(ast.literal_eval(historical.values[0]), 'verify/fixtures/nf-tiny/fabulous/generate.py')
        self.assertEqual(ast.unparse(historical.values[1]), "digest(here / 'generate.py')")
        self.assertEqual(ast.literal_eval(adapter.values[0]), 'verify/fixtures/fnd-06/generate.py')
        self.assertEqual(ast.unparse(adapter.values[1]), 'digest(adapter)')
        self.assertEqual(ast.literal_eval(record.values[1]), ['create-official-project-marker-before-init-context'])
        record.keys = record.keys[2:]
        record.values = record.values[2:]
        self.assertEqual(ast.dump(old), ast.dump(new))


if __name__ == '__main__':
    unittest.main()
