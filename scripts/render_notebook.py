#!/usr/bin/env python3
"""
Execute a Jupyter notebook and emit an HTML article fragment.

Fallback when Quarto is not installed. Prefer `quarto render` when available;
output shape matches scripts/render-projects.mjs expectations.
"""

from __future__ import annotations

import argparse
import base64
import html
import re
import sys
from pathlib import Path

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat.notebooknode import NotebookNode


def markdown_to_html(text: str) -> str:
    import markdown

    # Protect math so Markdown does not eat backslashes inside $...$.
    blocks: list[str] = []

    def stash(match: re.Match[str]) -> str:
        blocks.append(match.group(0))
        return f"MATHBLOCK{len(blocks) - 1}END"

    protected = re.sub(r"\$\$[\s\S]+?\$\$|\$[^$\n]+?\$", stash, text)
    rendered = markdown.markdown(protected, extensions=["extra", "sane_lists"])
    for i, block in enumerate(blocks):
        rendered = rendered.replace(f"MATHBLOCK{i}END", block)
    return rendered


def render_math_placeholders(fragment: str) -> str:
    """Leave $...$ and $$...$$ for KaTeX auto-render in the browser."""
    return fragment


def code_cell_html(source: str, outputs_html: str) -> str:
    escaped = html.escape(source)
    return f"""
<details class="code-fold">
  <summary>Show Python</summary>
  <pre><code class="language-python">{escaped}</code></pre>
</details>
{outputs_html}
"""


def output_to_html(
    output: NotebookNode,
    figures_dir: Path,
    fig_counter: list[int],
    slug: str,
) -> str:
    data = output.get("data", {})
    if "image/png" in data:
        fig_counter[0] += 1
        name = f"figure-{fig_counter[0]}.png"
        raw = data["image/png"]
        if isinstance(raw, str):
            raw_bytes = base64.b64decode(raw)
        else:
            raw_bytes = raw
        figures_dir.mkdir(parents=True, exist_ok=True)
        (figures_dir / name).write_bytes(raw_bytes)
        return f'<p><img src="/projects/{slug}/{name}" alt="Figure {fig_counter[0]}" /></p>'

    if "text/plain" in data and output.get("output_type") == "stream":
        text = "".join(output.get("text", []))
        return f"<pre class=\"stream\">{html.escape(text)}</pre>"

    if output.get("output_type") == "stream":
        text = "".join(output.get("text", []))
        return f"<pre class=\"stream\">{html.escape(text)}</pre>"

    if "text/plain" in data:
        text = data["text/plain"]
        if isinstance(text, list):
            text = "".join(text)
        return f"<pre class=\"stream\">{html.escape(text)}</pre>"

    return ""


def notebook_to_fragment(nb: NotebookNode, figures_dir: Path, slug: str) -> str:
    parts: list[str] = []
    fig_counter = [0]
    for cell in nb.cells:
        if cell.cell_type == "markdown":
            src = "".join(cell.source) if isinstance(cell.source, list) else cell.source
            parts.append(render_math_placeholders(markdown_to_html(src)))
        elif cell.cell_type == "code":
            src = "".join(cell.source) if isinstance(cell.source, list) else cell.source
            outs = []
            for output in cell.get("outputs", []):
                outs.append(output_to_html(output, figures_dir, fig_counter, slug))
            parts.append(code_cell_html(src, "\n".join(outs)))
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--public-dir", required=True)
    parser.add_argument("--article-out", required=True)
    args = parser.parse_args()

    root = Path(args.repo_root)
    sys.path.insert(0, str(root))

    nb_path = Path(args.notebook)
    nb = nbformat.read(nb_path, as_version=4)

    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": str(root)}})

    figures_dir = Path(args.public_dir)
    fragment = notebook_to_fragment(nb, figures_dir, args.slug)

    out = Path(args.article_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fragment, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
