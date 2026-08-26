import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import batch_repair as br  # noqa: E402


def test_salvage_recovers_valid_rows_from_malformed_array():
    text = ('```json\n[\n {"id": "a1", "verdict": "supported", "passage": "ok"},\n'
            ' {"id": "bad", "verdict": "supported", "passage": "x" and "y"},\n'
            ' {"id": "a2", "verdict": "NONE", "passage": null}\n]\n```')
    rows = br.salvage_rows(text)
    assert [r["id"] for r in rows] == ["a1", "a2"]


def test_salvage_handles_braces_inside_strings():
    rows = br.salvage_rows('{"id": "a", "passage": "uses {curly} braces"}')
    assert rows and rows[0]["id"] == "a"
