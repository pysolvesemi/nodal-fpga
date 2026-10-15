"""Independent controls for exact Scala authoring manifests/classpath scope."""
from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import maven_inventory as maven


class MavenInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        data = json.loads((ROOT / "tools/dependencies/scala-authoring.json").read_text())
        for file in ["tools/dependencies/scala-authoring.json", *data["build_inputs"]]:
            path = self.root / file
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / file, path)
        self.source = self.root / "frontend/scala/src/main/scala/Writer.scala"
        self.source.parent.mkdir(parents=True)
        self.source.write_text('import com.fasterxml.jackson.core.{JsonEncoding, JsonFactoryBuilder}\nobject Writer {}\n')

    def test_reviewed_static_boundary_is_accepted(self):
        maven.check_static(self.root)

    def test_manifest_and_repository_change_requires_review(self):
        for name in ["frontend/scala/build.sbt", "tools/repositories"]:
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_text()
                path.write_text(original + "\n// changed\n")
                with self.assertRaisesRegex(ValueError, "NF-SCALA-GRAPH"):
                    maven.check_static(self.root)
                path.write_text(original)

    def test_parser_databind_reflection_and_process_apis_reject(self):
        for code in ['factory.createParser(input)', 'new ObjectMapper()', 'NumberInput.looksLikeValidNumber(s)',
                     'Class.forName(name)', 'System.loadLibrary(name)', 'new ProcessBuilder(args)',
                     'import com.fasterxml.jackson.core.JsonParser', 'com.fasterxml.jackson.core.JsonFactory()']:
            with self.subTest(code=code):
                self.source.write_text(code)
                with self.assertRaisesRegex(ValueError, "NF-SCALA-GRAPH"):
                    maven.check_static(self.root)

    def test_comment_and_literal_mentions_do_not_fake_api_calls(self):
        self.source.write_text('// createParser(input)\nval description = "JsonParser is not used"\n')
        maven.check_static(self.root)

    def test_actual_classpath_requires_single_official_instance(self):
        for log in ['', 'Scala instance { compiler jars: /tmp/spoof.jar }',
                    'Scala instance {}\nScala instance {}']:
            with self.subTest(log=log), self.assertRaisesRegex(ValueError, "NF-SCALA-GRAPH"):
                maven.classpaths(log)
