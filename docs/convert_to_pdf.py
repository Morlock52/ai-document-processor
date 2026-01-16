#!/usr/bin/env python3
"""Convert INSTRUCTION_MANUAL.md to a beautifully styled PDF."""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# Read the markdown file
md_path = Path(__file__).parent / "INSTRUCTION_MANUAL.md"
md_content = md_path.read_text()

# Convert markdown to HTML with extensions
html_content = markdown.markdown(
    md_content,
    extensions=[
        'tables',
        'fenced_code',
        'codehilite',
        'toc',
        'nl2br',
        'sane_lists',
    ]
)

# Beautiful CSS styling inspired by modern documentation
css_style = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

@page {
    size: A4;
    margin: 2cm 2.5cm;
    @top-center {
        content: "AI Document Processor - Instruction Manual";
        font-family: 'Inter', sans-serif;
        font-size: 9pt;
        color: #6b7280;
    }
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-family: 'Inter', sans-serif;
        font-size: 9pt;
        color: #6b7280;
    }
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #1f2937;
    max-width: 100%;
}

/* Headers */
h1 {
    font-size: 28pt;
    font-weight: 700;
    color: #111827;
    margin-top: 0;
    margin-bottom: 16pt;
    padding-bottom: 12pt;
    border-bottom: 3px solid #3b82f6;
    page-break-after: avoid;
}

h2 {
    font-size: 18pt;
    font-weight: 600;
    color: #1f2937;
    margin-top: 32pt;
    margin-bottom: 12pt;
    padding-bottom: 8pt;
    border-bottom: 2px solid #e5e7eb;
    page-break-after: avoid;
}

h3 {
    font-size: 14pt;
    font-weight: 600;
    color: #374151;
    margin-top: 24pt;
    margin-bottom: 10pt;
    page-break-after: avoid;
}

h4 {
    font-size: 12pt;
    font-weight: 600;
    color: #4b5563;
    margin-top: 18pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
}

/* Paragraphs */
p {
    margin: 0 0 12pt 0;
    text-align: justify;
}

/* Links */
a {
    color: #2563eb;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* Lists */
ul, ol {
    margin: 0 0 12pt 0;
    padding-left: 24pt;
}

li {
    margin-bottom: 6pt;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 16pt 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

thead {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

th {
    color: white;
    font-weight: 600;
    text-align: left;
    padding: 12pt 14pt;
    border: 1px solid #2563eb;
}

td {
    padding: 10pt 14pt;
    border: 1px solid #e5e7eb;
    vertical-align: top;
}

tbody tr:nth-child(even) {
    background-color: #f9fafb;
}

tbody tr:hover {
    background-color: #f3f4f6;
}

/* Code blocks */
pre {
    background-color: #1e293b;
    color: #e2e8f0;
    padding: 16pt;
    border-radius: 8pt;
    overflow-x: auto;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 9pt;
    line-height: 1.5;
    margin: 16pt 0;
    page-break-inside: avoid;
    border-left: 4px solid #3b82f6;
}

code {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 9pt;
    background-color: #f1f5f9;
    color: #dc2626;
    padding: 2pt 6pt;
    border-radius: 4pt;
}

pre code {
    background: none;
    color: inherit;
    padding: 0;
}

/* Blockquotes (tips/notes) */
blockquote {
    margin: 16pt 0;
    padding: 14pt 18pt;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border-left: 4px solid #3b82f6;
    border-radius: 0 8pt 8pt 0;
    font-style: normal;
}

blockquote p {
    margin: 0;
    color: #1e40af;
}

blockquote strong {
    color: #1e3a8a;
}

/* Horizontal rules */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #e5e7eb 0%, #9ca3af 50%, #e5e7eb 100%);
    margin: 32pt 0;
}

/* Strong and emphasis */
strong {
    font-weight: 600;
    color: #111827;
}

em {
    font-style: italic;
    color: #4b5563;
}

/* Images (badges) */
img {
    max-width: 100%;
    height: auto;
}

/* Cover page styling */
p:first-of-type img {
    display: block;
    margin: 0 auto 20pt auto;
}

/* Center aligned content */
p[align="center"] {
    text-align: center;
}

/* ASCII art blocks */
pre:has(+ table),
pre:not(:has(code)) {
    background-color: #f8fafc;
    color: #334155;
    border-left-color: #94a3b8;
}

/* Page breaks before major sections */
h2 {
    page-break-before: auto;
}

/* Keep content together */
h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid;
}

table, pre, blockquote {
    page-break-inside: avoid;
}

/* Footer styling */
.footer {
    text-align: center;
    font-size: 9pt;
    color: #6b7280;
    margin-top: 40pt;
    padding-top: 20pt;
    border-top: 1px solid #e5e7eb;
}

/* Mermaid placeholder */
.mermaid-placeholder {
    background: #f0f9ff;
    border: 2px dashed #3b82f6;
    border-radius: 8pt;
    padding: 20pt;
    text-align: center;
    color: #0369a1;
    font-style: italic;
    margin: 16pt 0;
}
"""

# Wrap in full HTML document
full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Document Processor - Instruction Manual</title>
</head>
<body>
{html_content}
</body>
</html>
"""

# Generate PDF
output_path = Path(__file__).parent / "INSTRUCTION_MANUAL.pdf"
HTML(string=full_html).write_pdf(
    output_path,
    stylesheets=[CSS(string=css_style)]
)

print(f"PDF generated: {output_path}")
print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
