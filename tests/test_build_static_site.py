import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_static_site import main  # noqa: E402


def test_main_writes_nonempty_html(tmp_path):
    output_path = tmp_path / "index.html"

    result_path = main(output_path)

    assert result_path == output_path
    assert output_path.exists()
    html = output_path.read_text()
    assert len(html) > 0
    assert "Subscribers" in html
    assert "plotly" in html.lower()
