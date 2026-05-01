#!/usr/bin/env python3
"""Render docs/announcement-v3.0.0-combined.md to styled HTML."""
import pathlib, re, html as _html

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "docs" / "announcement-v3.0.0-combined.md"
DST = ROOT / "docs" / "announcement-v3.0.0-combined.html"


def escape(s):
    return _html.escape(s, quote=False)


def inline(s):
    s = escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(
        r"\[(.+?)\]\(([^)]+)\)",
        lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>',
        s,
    )
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def convert(src_text):
    lines = src_text.split("\n")
    i = 0
    parts = []

    while i < len(lines):
        line = lines[i]

        # Headings
        for level in range(6, 0, -1):
            prefix = "#" * level + " "
            if line.startswith(prefix):
                parts.append(f"<h{level}>{inline(line[len(prefix):])}</h{level}>")
                break
        else:
            if re.match(r"^---+$", line.strip()):
                parts.append("<hr>")

            elif line.startswith("> "):
                bq = ["<blockquote>"]
                while i < len(lines) and lines[i].startswith("> "):
                    bq.append(f"<p>{inline(lines[i][2:])}</p>")
                    i += 1
                bq.append("</blockquote>")
                parts.append("\n".join(bq))
                continue

            elif re.match(r"^[*-] ", line):
                ul = ["<ul>"]
                while i < len(lines) and re.match(r"^[*-] ", lines[i]):
                    ul.append(f"<li>{inline(lines[i][2:])}</li>")
                    i += 1
                ul.append("</ul>")
                parts.append("\n".join(ul))
                continue

            elif re.match(r"^\d+\. ", line):
                ol = ["<ol>"]
                while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                    ol.append(f"<li>{inline(re.sub(r'^[0-9]+[.] ', '', lines[i]))}</li>")
                    i += 1
                ol.append("</ol>")
                parts.append("\n".join(ol))
                continue

            elif line.startswith("|") and "|" in line[1:]:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                tbl = [
                    "<table>",
                    "<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr></thead>",
                    "<tbody>",
                ]
                i += 1
                if i < len(lines) and re.match(r"^[| :-]+$", lines[i]):
                    i += 1
                while i < len(lines) and lines[i].startswith("|") and "|" in lines[i][1:]:
                    row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    tbl.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
                    i += 1
                tbl += ["</tbody>", "</table>"]
                parts.append("\n".join(tbl))
                continue

            elif line.strip() == "":
                parts.append("")

            else:
                parts.append(f"<p>{inline(line)}</p>")

        i += 1

    return "\n".join(parts)


CSS = """
body{font-family:Arial,sans-serif;font-size:1.125rem;line-height:1.5;margin:0;background:#f7f8fb;color:#1a1a1a}
main{max-width:76ch;margin:2rem auto;background:#fff;padding:2rem 2.5rem;border:1px solid #d9deea}
h1{font-size:1.75rem;line-height:1.2;margin-top:0}
h2{font-size:1.4rem;margin-top:2.25rem}
h3{font-size:1.15rem;margin-top:1.75rem}
h4{font-size:1rem;margin-top:1.25rem}
blockquote{border-left:4px solid #0c234b;margin:1.25rem 0;padding:.75rem 1.25rem;background:#f0f4fa}
blockquote p{margin:.4rem 0}
table{border-collapse:collapse;width:100%;margin:1.25rem 0;font-size:.9rem}
th{background:#0c234b;color:#fff;padding:.5rem .75rem;text-align:left}
td{border:1px solid #d0d7e3;padding:.4rem .75rem}
tr:nth-child(even) td{background:#f5f7fb}
code{background:#f0f0f0;padding:.1rem .25rem;border-radius:3px;font-size:.9rem}
hr{border:none;border-top:1px solid #d9deea;margin:2rem 0}
ul,ol{padding-left:1.5rem}
a{color:#0c234b}
"""

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GLOW 3.0.0: Built by the Community, for the Community</title>
  <style>{css}</style>
</head>
<body>
  <main>
{body}
  </main>
</body>
</html>
"""

if __name__ == "__main__":
    body = convert(SRC.read_text(encoding="utf-8"))
    doc = TEMPLATE.format(css=CSS, body=body)
    DST.write_text(doc, encoding="utf-8")
    print(f"Written {len(doc):,} bytes -> {DST}")
