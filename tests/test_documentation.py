"""Execute the image-based usage guide with an aligned GeoTIFF/MTL fixture."""
from pathlib import Path
import ast
import re
import unittest
import test_scene_io as scene_fixture


@unittest.skipIf(scene_fixture.Image is None, "Install .[examples] to test image examples")
class DocumentationTests(unittest.TestCase):
    def test_usage_python_blocks_execute(self):
        fixture = scene_fixture.SceneIOTests()
        fixture.setUp()
        try:
            path = Path(__file__).resolve().parents[1] / "docs" / "usage.md"
            blocks = re.findall(r"```python\n(.*?)```", path.read_text(encoding="utf-8-sig"), re.S)
            self.assertTrue(blocks)
            destination = fixture.folder / "results"

            class ConfigurePaths(ast.NodeTransformer):
                def visit_Assign(self, node):
                    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                        replacement = {"pasta": fixture.folder, "saida": destination}.get(node.targets[0].id)
                        if replacement is not None:
                            node.value = ast.Call(func=ast.Name(id="Path", ctx=ast.Load()),
                                args=[ast.Constant(value=str(replacement))], keywords=[])
                    return node

            namespace = {}
            for index, block in enumerate(blocks, 1):
                with self.subTest(block=index):
                    tree = ast.fix_missing_locations(ConfigurePaths().visit(ast.parse(block)))
                    exec(compile(tree, str(path), "exec"), namespace)
            outputs = list(destination.glob("*.tif"))
            self.assertEqual(len(outputs), 11)
            for output in outputs:
                with scene_fixture.Image.open(output) as image:
                    self.assertEqual(image.size, (14, 12))
                    self.assertEqual(image.tag_v2[42113], "nan")
                    description = str(image.tag_v2.get(270, ""))
                    gdal_metadata = str(image.tag_v2.get(42112, ""))
                    self.assertTrue("units=" in description or 'name="units"' in gdal_metadata)
        finally:
            fixture.tearDown()
