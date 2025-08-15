#!/usr/bin/env python3
"""
Convert OpenStrand Studio User Manual to PDF
Requires: pip install markdown pdfkit weasyprint
"""

import markdown
import os
import sys
from pathlib import Path

def markdown_to_html(md_file, output_file):
    """Convert markdown to HTML with proper CSS styling"""
    
    # Read the markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Configure markdown extensions
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.toc',
        'markdown.extensions.codehilite'
    ]
    
    # Convert to HTML
    html = markdown.markdown(md_content, extensions=extensions)
    
    # Add CSS styling for professional appearance
    css_style = """
    <style>
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
            page-break-before: always;
        }
        
        h2 {
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
            margin-top: 25px;
        }
        
        h3 {
            color: #7f8c8d;
            margin-top: 20px;
        }
        
        h4 {
            color: #95a5a6;
            font-style: italic;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        
        table, th, td {
            border: 1px solid #bdc3c7;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
        }
        
        th {
            background-color: #ecf0f1;
            font-weight: bold;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        code {
            background-color: #f1f2f6;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        
        pre {
            background-color: #f1f2f6;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            margin-left: 0;
            padding-left: 20px;
            font-style: italic;
            background-color: #f8f9fa;
            padding: 15px 20px;
            border-radius: 0 5px 5px 0;
        }
        
        ul, ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        
        li {
            margin: 8px 0;
        }
        
        strong, b {
            color: #2c3e50;
            font-weight: bold;
        }
        
        em, i {
            color: #7f8c8d;
            font-style: italic;
        }
        
        .toc {
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        
        .page-break {
            page-break-before: always;
        }
        
        @media print {
            body {
                font-size: 12pt;
                line-height: 1.4;
            }
            
            h1 {
                font-size: 18pt;
                page-break-after: avoid;
            }
            
            h2 {
                font-size: 16pt;
                page-break-after: avoid;
            }
            
            h3 {
                font-size: 14pt;
                page-break-after: avoid;
            }
            
            table {
                page-break-inside: avoid;
            }
            
            pre {
                page-break-inside: avoid;
            }
            
            img {
                max-width: 100%;
                page-break-inside: avoid;
            }
        }
        
        .cover-page {
            text-align: center;
            padding: 100px 0;
            page-break-after: always;
        }
        
        .cover-title {
            font-size: 36pt;
            color: #2c3e50;
            margin-bottom: 20px;
            font-weight: bold;
        }
        
        .cover-subtitle {
            font-size: 18pt;
            color: #7f8c8d;
            margin-bottom: 40px;
        }
        
        .cover-version {
            font-size: 14pt;
            color: #95a5a6;
            margin-bottom: 20px;
        }
        
        .cover-date {
            font-size: 12pt;
            color: #bdc3c7;
        }
    </style>
    """
    
    # Create complete HTML document
    html_doc = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenStrand Studio - Complete User Manual</title>
        {css_style}
    </head>
    <body>
        {html}
    </body>
    </html>
    """
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    
    print(f"HTML file created: {output_file}")

def html_to_pdf_weasyprint(html_file, pdf_file):
    """Convert HTML to PDF using WeasyPrint (better for complex layouts)"""
    try:
        from weasyprint import HTML, CSS
        from weasyprint.fonts import FontConfiguration
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Additional CSS for PDF
        pdf_css = CSS(string='''
            @page {
                size: A4;
                margin: 1in;
                @top-center {
                    content: "OpenStrand Studio - User Manual v1.101";
                    font-size: 10pt;
                    color: #7f8c8d;
                }
                @bottom-center {
                    content: "Page " counter(page);
                    font-size: 10pt;
                    color: #7f8c8d;
                }
            }
        ''')
        
        # Convert to PDF
        HTML(filename=html_file).write_pdf(
            pdf_file, 
            stylesheets=[pdf_css],
            font_config=font_config
        )
        
        print(f"PDF created successfully: {pdf_file}")
        return True
        
    except ImportError:
        print("WeasyPrint not installed. Install with: pip install weasyprint")
        return False
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return False

def html_to_pdf_pdfkit(html_file, pdf_file):
    """Convert HTML to PDF using pdfkit (requires wkhtmltopdf)"""
    try:
        import pdfkit
        
        options = {
            'page-size': 'A4',
            'margin-top': '1in',
            'margin-right': '0.8in',
            'margin-bottom': '1in',
            'margin-left': '0.8in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'print-media-type': None,
            'header-center': 'OpenStrand Studio - User Manual v1.101',
            'header-font-size': '9',
            'header-spacing': '5',
            'footer-center': 'Page [page] of [topage]',
            'footer-font-size': '9',
            'footer-spacing': '5'
        }
        
        pdfkit.from_file(html_file, pdf_file, options=options)
        print(f"PDF created successfully: {pdf_file}")
        return True
        
    except ImportError:
        print("pdfkit not installed. Install with: pip install pdfkit")
        print("Also requires wkhtmltopdf: https://wkhtmltopdf.org/downloads.html")
        return False
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return False

def main():
    """Main conversion function"""
    
    # File paths
    current_dir = Path(__file__).parent
    md_file = current_dir / "OpenStrand_Studio_Complete_User_Manual_v1101.md"
    html_file = current_dir / "OpenStrand_Studio_Complete_User_Manual_v1101.html"
    pdf_file = current_dir / "OpenStrand_Studio_Complete_User_Manual_v1101.pdf"
    
    # Check if markdown file exists
    if not md_file.exists():
        print(f"Markdown file not found: {md_file}")
        return
    
    print("Converting OpenStrand Studio User Manual to PDF...")
    print(f"Source: {md_file}")
    print(f"Target: {pdf_file}")
    
    # Step 1: Convert Markdown to HTML
    print("\nStep 1: Converting Markdown to HTML...")
    markdown_to_html(md_file, html_file)
    
    # Step 2: Convert HTML to PDF (try multiple methods)
    print("\nStep 2: Converting HTML to PDF...")
    
    # Try WeasyPrint first (better quality)
    if html_to_pdf_weasyprint(html_file, pdf_file):
        print("✅ PDF conversion completed using WeasyPrint")
    elif html_to_pdf_pdfkit(html_file, pdf_file):
        print("✅ PDF conversion completed using pdfkit")
    else:
        print("❌ PDF conversion failed. Please install one of the following:")
        print("   Option 1: pip install weasyprint")
        print("   Option 2: pip install pdfkit (plus download wkhtmltopdf)")
        print(f"\n📄 HTML version available at: {html_file}")
        return
    
    # Cleanup - remove HTML file
    try:
        html_file.unlink()
        print("🧹 Cleaned up temporary HTML file")
    except:
        pass
    
    print(f"\n🎉 Complete! PDF manual available at: {pdf_file}")
    print(f"📊 File size: {pdf_file.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()