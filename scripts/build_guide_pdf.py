"""Assemble every project doc into one navigable PDF."""

import base64
import os
import re

import markdown
from weasyprint import HTML

ROOT = "/home/claude/northstar-triage"
OUT = "/mnt/user-data/outputs/Northstar_Team_Guide.pdf"

# (file, section title, who it's for, anchor id)
SECTIONS = [
    ("docs/START_HERE.md",       "Start Here",                    "Everyone",  "start"),
    ("docs/SETUP_FROM_ZERO.md",  "Setup From Zero",               "Everyone — do this first", "setup"),
    ("docs/GLOSSARY.md",         "Glossary",                      "Everyone — look things up", "glossary"),
    ("docs/GIT_GUIDE.md",        "Git Reference",                 "Everyone", "git"),
    ("docs/CONCEPTS.md",         "The Code Concepts You'll Need", "Everyone",  "concepts"),
    ("docs/guides/ENRIQUE.md",   "Enrique",  "Orchestrator Engineer & Repo Owner", "enrique"),
    ("docs/guides/LANCE.md",     "Lance",    "Integration Engineer",               "lance"),
    ("docs/guides/MITCHY.md",    "Mitchy",   "Prompt Engineer",                    "mitchy"),
    ("docs/guides/JULIAN.md",    "Julian",   "QA / Critic Engineer",               "julian"),
    ("docs/guides/NATAKI.md",    "Nataki",   "Logging & Observability Engineer",   "nataki"),
]

CSS = """
@page {
  size: Letter;
  margin: 20mm 17mm 18mm 17mm;
  @bottom-center {
    content: counter(page);
    font-family: Helvetica, Arial, sans-serif;
    font-size: 8.5pt;
    color: #9A9AA4;
  }
  @top-right {
    content: "Northstar Support Co. — Team Guide";
    font-family: Helvetica, Arial, sans-serif;
    font-size: 8pt;
    color: #B4B4BE;
  }
}
@page :first { @top-right { content: ""; } @bottom-center { content: ""; } }

body {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9.8pt;
  line-height: 1.52;
  color: #23232B;
}

h1 {
  font-size: 20pt; color: #16294A; margin: 0 0 2pt 0;
  padding-bottom: 6pt; border-bottom: 2.5px solid #2C4B7C;
}
h2 {
  font-size: 13pt; color: #1C3050; margin: 20pt 0 6pt 0;
  padding-bottom: 3pt; border-bottom: 1px solid #D8D8E0;
  page-break-after: avoid;
}
h3 { font-size: 10.8pt; color: #2C4B7C; margin: 14pt 0 4pt 0; page-break-after: avoid; }
p { margin: 0 0 7pt 0; }
ul, ol { margin: 0 0 8pt 0; padding-left: 17pt; }
li { margin-bottom: 3pt; }

code {
  font-family: "DejaVu Sans Mono", Menlo, monospace;
  font-size: 8.4pt; background: #F1F1F5; padding: 1px 3.5px;
  border-radius: 2px; color: #8C3A3A;
}
pre {
  background: #F7F7FA; border: 1px solid #DEDEE6; border-left: 3px solid #2C4B7C;
  border-radius: 3px; padding: 8pt 10pt; margin: 0 0 9pt 0;
  font-size: 8.1pt; line-height: 1.42; overflow-wrap: break-word;
  white-space: pre-wrap; page-break-inside: avoid;
}
pre code { background: none; padding: 0; color: #23232B; font-size: 8.1pt; }

table {
  border-collapse: collapse; width: 100%; margin: 0 0 10pt 0;
  font-size: 8.8pt; page-break-inside: avoid;
}
th {
  background: #EDF0F6; text-align: left; padding: 4.5pt 6pt;
  border: 1px solid #C8CDD8; color: #16294A; font-weight: 600;
}
td { padding: 4.5pt 6pt; border: 1px solid #D8DCE4; vertical-align: top; }

blockquote {
  margin: 0 0 9pt 0; padding: 6pt 10pt;
  background: #FBF6E9; border-left: 3px solid #9A6B1E; color: #4A3A18;
}
hr { border: none; border-top: 1px solid #DEDEE6; margin: 14pt 0; }
strong { color: #16294A; }
a { color: #2C4B7C; text-decoration: none; }

/* ---------- cover ---------- */
.cover { text-align: center; padding-top: 42mm; page-break-after: always; }
.cover .kicker { font-size: 10pt; letter-spacing: 2.6px; color: #8A8A94; text-transform: uppercase; }
.cover h1 { font-size: 31pt; border: none; color: #16294A; margin: 12pt 0 6pt 0; }
.cover .sub { font-size: 12.5pt; color: #55555F; margin-bottom: 30pt; }
.cover img { width: 155mm; margin: 0 auto 26pt auto; }
.cover .team { font-size: 10pt; color: #6A6A74; line-height: 1.9; }

/* ---------- contents ---------- */
.toc { page-break-after: always; }
.toc h1 { margin-bottom: 14pt; }
.toc-row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 7pt 0; border-bottom: 1px solid #E8E8EE;
}
.toc-name { font-size: 12pt; color: #16294A; font-weight: 600; }
.toc-role { font-size: 9pt; color: #7A7A84; }
.toc-note {
  margin-top: 20pt; padding: 10pt 12pt; background: #F4F7FB;
  border-left: 3px solid #2C4B7C; font-size: 9.4pt;
}

/* ---------- section dividers ---------- */
.divider { page-break-before: always; padding-top: 60mm; text-align: center; }
.divider .who { font-size: 9.5pt; letter-spacing: 2.4px; text-transform: uppercase; color: #8A8A94; }
.divider .name { font-size: 30pt; color: #16294A; font-weight: 600; margin: 8pt 0 4pt 0; }
.divider .role { font-size: 12pt; color: #55555F; }
.divider .rule { width: 46mm; border-top: 2.5px solid #2C4B7C; margin: 18pt auto 0 auto; }

.section { page-break-before: always; }
.section h1 { font-size: 17pt; }
"""


def md_to_html(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        text = f.read()
    # strip HTML comments that are notes-to-self inside prompt files
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Python-markdown needs a blank line before a list. Our source files often
    # put one directly under a sentence, which silently flattens into a
    # paragraph. Insert the blank line where it's missing.
    lines = text.split("\n")
    fixed = []
    in_fence = False
    list_start = re.compile(r"^\s*(?:[-*+] |\d+\. )")
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if (not in_fence and list_start.match(line) and fixed
                and fixed[-1].strip() and not list_start.match(fixed[-1])
                and not fixed[-1].lstrip().startswith(("#", ">", "|"))
                and not fixed[-1].startswith("  ")):
            fixed.append("")
        fixed.append(line)
    text = "\n".join(fixed)

    return markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists"]
    )


def build():
    with open(os.path.join(ROOT, "docs/architecture.png"), "rb") as f:
        diagram = base64.b64encode(f.read()).decode()

    parts = [f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>"]

    # Cover
    parts.append(f"""
    <div class="cover">
      <div class="kicker">The Knowledge House &middot; Phase 2 Final Project</div>
      <h1>Northstar Support Co.</h1>
      <div class="sub">Agentic Ticket Triage &mdash; Team Build Guide</div>
      <img src="data:image/png;base64,{diagram}" alt="Architecture diagram"/>
      <div class="team">
        Enrique Quezada &middot; Lance Gonzalez &middot; Julian Seiferth<br/>
        Mitchy Derose &middot; Nataki Boykin
      </div>
    </div>
    """)

    # Contents
    rows = "".join(
        f'<div class="toc-row"><span class="toc-name">{title}</span>'
        f'<span class="toc-role">{role}</span></div>'
        for _, title, role, _ in SECTIONS
    )
    parts.append(f"""
    <div class="toc">
      <h1>Contents</h1>
      {rows}
      <div class="toc-note">
        <strong>How to use this guide.</strong> If you have never programmed
        before, start with <strong>Setup From Zero</strong> on page 7 &mdash; it
        assumes nothing and walks through installing everything, opening a
        terminal, and making your first commit. Everyone reads the first five
        sections. After that, find the
        section with your name on it and work through the numbered tasks in
        order. Each personal section ends with a checklist, the one line you
        own in the pitch, and the specific errors you are likely to hit.
        <br/><br/>
        <strong>You are not starting from a blank file.</strong> Every piece of
        the project already exists as a working stub. Your job is to replace
        your stub with the real thing. If you get stuck, the project still
        runs.
      </div>
    </div>
    """)

    for path, title, role, _anchor in SECTIONS:
        is_person = path.startswith("docs/guides/")
        if is_person:
            parts.append(f"""
            <div class="divider">
              <div class="who">Your section</div>
              <div class="name">{title}</div>
              <div class="role">{role}</div>
              <div class="rule"></div>
            </div>
            """)
            parts.append(f'<div class="section">{md_to_html(path)}</div>')
        else:
            parts.append(f'<div class="section">{md_to_html(path)}</div>')

    parts.append("</body></html>")

    HTML(string="".join(parts), base_url=ROOT).write_pdf(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
