import base64
import sys
from pathlib import Path

from IPython.display import Image, display

from .workflow import build_workflow

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

def visualize_graph():
    """Build the workflow graph, render it as PNG, and display in IPython."""
    graph = build_workflow()
    png_data = graph.get_graph().draw_mermaid_png()

    repo_out = Path(__file__).resolve().parents[3] / "out"
    repo_out.mkdir(parents=True, exist_ok=True)
    out_path = repo_out / "stategraph.png"

    if isinstance(png_data, str):
        try:
            png_bytes = base64.b64decode(png_data)
        except Exception:
            png_bytes = png_data.encode("utf-8")
    else:
        png_bytes = png_data

    with open(out_path, "wb") as f:
        f.write(png_bytes)

    display(Image(filename=str(out_path)))
    
if __name__ == "__main__":
    visualize_graph()