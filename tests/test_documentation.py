"""Ensure the sequential usage guide remains executable."""
from pathlib import Path
import re
import unittest

class DocumentationTests(unittest.TestCase):
    def test_usage_python_blocks_execute(self):
        path=Path(__file__).resolve().parents[1]/"docs"/"usage.md"
        namespace={}
        blocks=re.findall(r"```python\n(.*?)```",path.read_text(encoding="utf-8-sig"),re.S)
        self.assertEqual(len(blocks),10)
        for index,block in enumerate(blocks,1):
            with self.subTest(block=index):
                exec(compile(block,str(path),"exec"),namespace)
