import subprocess
import sys
import tempfile
from pathlib import Path

def test_cli_html_output(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# CLI Test\nThis is a paragraph.")
    cmd = [sys.executable, "cli.py", "html", str(md_file)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    out = proc.stdout
    assert "<h1>" in out
    assert "<p>" in out

def test_cli_parse_output(tmp_path):
    md_file = tmp_path / "test2.md"
    md_file.write_text("Some **bold** text")
    cmd = [sys.executable, "cli.py", "parse", str(md_file)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Document" in proc.stdout