"""Build and execute .ipynb from a '# %%' / '# %% [markdown]' annotated .py file."""
import sys, pathlib, nbformat
from nbclient import NotebookClient

def parse(path: pathlib.Path):
    cells, kind, buf = [], "code", []
    def flush():
        src = "\n".join(buf).strip("\n")
        if src.strip():
            cells.append(nbformat.v4.new_markdown_cell(src) if kind == "markdown"
                         else nbformat.v4.new_code_cell(src))
    for line in path.read_text().splitlines():
        if line.startswith("# %%"):
            flush(); buf = []
            kind = "markdown" if "[markdown]" in line else "code"
            continue
        if kind == "markdown" and line.startswith("# "):
            buf.append(line[2:])
        elif kind == "markdown" and line.strip() == "#":
            buf.append("")
        else:
            buf.append(line)
    flush()
    nb = nbformat.v4.new_notebook(cells=cells)
    nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"}}
    return nb

if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2])
    nb = parse(src)
    print(f"{src.name}: {len(nb.cells)} cells -> executing...")
    NotebookClient(nb, timeout=3600, kernel_name="python3",
                   resources={"metadata": {"path": str(out.parent)}}).execute()
    nbformat.write(nb, out)
    print(f"  wrote {out}")
