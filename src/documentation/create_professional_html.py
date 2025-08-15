#!/usr/bin/env python3
"""
Create a professionally formatted HTML version of the OpenStrand Studio manual
with proper visual representation, tables, and styling.
"""

import re
import os

def convert_markdown_to_html(markdown_file, output_file):
    """Convert markdown to properly formatted HTML with professional styling"""
    
    # Read the markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Convert markdown tables to HTML tables
    def convert_table(match):
        lines = match.group(0).strip().split('\n')
        html = '<table class="data-table">\n'
        
        # Process header row
        if len(lines) > 0:
            headers = [cell.strip() for cell in lines[0].split('|') if cell.strip()]
            html += '<thead><tr>\n'
            for header in headers:
                html += f'<th>{header}</th>\n'
            html += '</tr></thead>\n'
        
        # Process data rows (skip separator line)
        if len(lines) > 2:
            html += '<tbody>\n'
            for line in lines[2:]:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if cells:
                    html += '<tr>\n'
                    for cell in cells:
                        # Make bold text in cells
                        cell = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', cell)
                        html += f'<td>{cell}</td>\n'
                    html += '</tr>\n'
            html += '</tbody>\n'
        
        html += '</table>\n'
        return html
    
    # Convert tables
    content = re.sub(r'\|.*?\|.*?\n\|[\s\-\|]+\n(?:\|.*?\n)+', convert_table, content, flags=re.MULTILINE)
    
    # Convert headers
    content = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    
    # Convert emphasis and strong
    content = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', content)
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    
    # Convert code blocks
    content = re.sub(r'```(\w+)?\n(.*?)```', lambda m: f'<pre class="code-block lang-{m.group(1) or "text"}"><code>{m.group(2)}</code></pre>', content, flags=re.DOTALL)
    content = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', content)
    
    # Convert lists
    def convert_list(text):
        # Convert unordered lists
        text = re.sub(r'^- (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'(<li>.*?</li>\n)+', lambda m: f'<ul>\n{m.group(0)}</ul>\n', text, flags=re.DOTALL)
        
        # Convert ordered lists
        text = re.sub(r'^\d+\. (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        return text
    
    content = convert_list(content)
    
    # Convert blockquotes
    content = re.sub(r'^> (.*?)$', r'<blockquote>\1</blockquote>', content, flags=re.MULTILINE)
    
    # Convert line breaks and paragraphs
    content = re.sub(r'\n\n+', '</p>\n\n<p>', content)
    content = '<p>' + content + '</p>'
    
    # Clean up empty paragraphs around block elements
    content = re.sub(r'<p>\s*(<h[1-6]>)', r'\1', content)
    content = re.sub(r'(</h[1-6]>)\s*</p>', r'\1', content)
    content = re.sub(r'<p>\s*(<table)', r'\1', content)
    content = re.sub(r'(</table>)\s*</p>', r'\1', content)
    content = re.sub(r'<p>\s*(<ul>)', r'\1', content)
    content = re.sub(r'(</ul>)\s*</p>', r'\1', content)
    content = re.sub(r'<p>\s*(<pre)', r'\1', content)
    content = re.sub(r'(</pre>)\s*</p>', r'\1', content)
    content = re.sub(r'<p>\s*</p>', '', content)
    
    # Professional CSS styling
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: #ffffff;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px 40px;
            font-size: 11pt;
        }
        
        /* Typography */
        h1 {
            color: #1a1a1a;
            font-size: 24pt;
            font-weight: 700;
            margin: 30px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
            page-break-after: avoid;
        }
        
        h1:first-child {
            margin-top: 0;
        }
        
        h2 {
            color: #2c3e50;
            font-size: 18pt;
            font-weight: 600;
            margin: 25px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #ecf0f1;
            page-break-after: avoid;
        }
        
        h3 {
            color: #34495e;
            font-size: 14pt;
            font-weight: 600;
            margin: 20px 0 10px 0;
            page-break-after: avoid;
        }
        
        h4 {
            color: #7f8c8d;
            font-size: 12pt;
            font-weight: 500;
            margin: 18px 0 8px 0;
            font-style: italic;
            page-break-after: avoid;
        }
        
        p {
            margin: 10px 0;
            text-align: justify;
            line-height: 1.6;
        }
        
        /* Lists */
        ul, ol {
            margin: 10px 0 10px 25px;
            line-height: 1.6;
        }
        
        li {
            margin: 5px 0;
        }
        
        li ul, li ol {
            margin: 8px 0 8px 20px;
        }
        
        /* Tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            overflow: hidden;
            border-radius: 8px;
            page-break-inside: avoid;
        }
        
        .data-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .data-table th {
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 9pt;
            letter-spacing: 0.5px;
        }
        
        .data-table td {
            padding: 8px 12px;
            border-bottom: 1px solid #ecf0f1;
            font-size: 10pt;
        }
        
        .data-table tbody tr {
            background: #ffffff;
            transition: all 0.2s;
        }
        
        .data-table tbody tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .data-table tbody tr:hover {
            background: #e8f4f8;
            transform: scale(1.01);
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .data-table tbody tr:last-child td {
            border-bottom: none;
        }
        
        /* Code blocks */
        .code-block {
            background: #2d3748;
            color: #e2e8f0;
            padding: 12px 15px;
            border-radius: 6px;
            margin: 12px 0;
            overflow-x: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 9pt;
            line-height: 1.5;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            page-break-inside: avoid;
        }
        
        .inline-code {
            background: #f1f5f9;
            color: #e11d48;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 9pt;
            font-weight: 500;
        }
        
        /* Emphasis */
        strong {
            font-weight: 600;
            color: #1a1a1a;
        }
        
        em {
            font-style: italic;
            color: #555;
        }
        
        /* Blockquotes */
        blockquote {
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 15px 20px;
            background: #f8f9fa;
            font-style: italic;
            border-radius: 0 8px 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Links */
        a {
            color: #3498db;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: all 0.2s;
        }
        
        a:hover {
            color: #2980b9;
            border-bottom-color: #2980b9;
        }
        
        /* Special sections */
        .cover-page {
            text-align: center;
            padding: 100px 0;
            page-break-after: always;
            border-bottom: 3px solid #ecf0f1;
            margin-bottom: 50px;
        }
        
        .cover-title {
            font-size: 36pt;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 20px;
        }
        
        .cover-subtitle {
            font-size: 18pt;
            color: #7f8c8d;
            margin-bottom: 30px;
        }
        
        .cover-version {
            font-size: 14pt;
            color: #95a5a6;
            margin-bottom: 15px;
        }
        
        /* Horizontal rules */
        hr {
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 40px 0;
        }
        
        /* Print styles */
        @media print {
            body {
                font-size: 11pt;
                padding: 0;
                margin: 0;
            }
            
            h1 {
                page-break-before: always;
                page-break-after: avoid;
            }
            
            h1:first-child {
                page-break-before: avoid;
            }
            
            h2, h3, h4 {
                page-break-after: avoid;
            }
            
            .data-table {
                page-break-inside: avoid;
            }
            
            .code-block {
                page-break-inside: avoid;
            }
            
            p {
                orphans: 3;
                widows: 3;
            }
        }
        
        /* Responsive adjustments */
        @media screen and (max-width: 768px) {
            body {
                padding: 20px;
                font-size: 14px;
            }
            
            h1 { font-size: 2em; }
            h2 { font-size: 1.5em; }
            h3 { font-size: 1.2em; }
            h4 { font-size: 1.1em; }
            
            .data-table {
                font-size: 0.85em;
            }
            
            .data-table th,
            .data-table td {
                padding: 8px;
            }
        }
    </style>
    """
    
    # Create the complete HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenStrand Studio - Complete User Manual v1.101</title>
    <meta name="description" content="Complete user manual for OpenStrand Studio version 1.101 - Professional rope and knot drawing application">
    <meta name="author" content="OpenStrand Studio">
    <meta name="version" content="1.101">
    {css}
</head>
<body>
    <div class="cover-page">
        <h1 class="cover-title">OpenStrand Studio</h1>
        <div class="cover-subtitle">Complete User Manual</div>
        <div class="cover-version">Version 1.101</div>
        <div class="cover-version">Documentation Version 4.0</div>
    </div>
    
    {content}
    
    <hr>
    <p style="text-align: center; color: #95a5a6; margin-top: 50px;">
        <em>OpenStrand Studio v1.101 - Complete User Manual<br>
        © 2025 OpenStrand Studio - All Rights Reserved</em>
    </p>
</body>
</html>"""
    
    # Write the HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[SUCCESS] Professional HTML created: {output_file}")
    print(f"[INFO] File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    print("\n[PDF INSTRUCTIONS]")
    print("1. Open the HTML file in Chrome, Firefox, or Edge")
    print("2. Press Ctrl+P (Print)")
    print("3. Choose 'Save as PDF'")
    print("4. Settings: A4 size, Minimum margins, No headers/footers")
    print("5. Save the PDF file")

if __name__ == "__main__":
    # Convert the markdown to professional HTML
    markdown_file = "OpenStrand_Studio_Complete_User_Manual_v1101.md"
    output_file = "OpenStrand_Studio_Professional_Manual_v1101.html"
    
    if os.path.exists(markdown_file):
        convert_markdown_to_html(markdown_file, output_file)
    else:
        print(f"❌ Error: {markdown_file} not found!")