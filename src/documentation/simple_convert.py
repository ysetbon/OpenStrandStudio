import os

# Read markdown
with open('OpenStrand_Studio_Complete_User_Manual_v1101.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Simple conversion - replace markdown syntax with HTML
content = content.replace('# ', '<h1>').replace('\n## ', '</h1>\n<h2>').replace('\n### ', '</h2>\n<h3>')
content = content.replace('\n#### ', '</h3>\n<h4>').replace('**', '<strong>').replace('*', '<em>')
content = content.replace('</h1>\n', '</h1>\n').replace('</h2>\n', '</h2>\n').replace('</h3>\n', '</h3>\n')

# Add HTML structure
html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OpenStrand Studio Manual v1.101</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 1in; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
        h3 {{ color: #7f8c8d; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #bdc3c7; padding: 8px; text-align: left; }}
        th {{ background-color: #ecf0f1; }}
        code {{ background: #f4f4f4; padding: 2px 4px; }}
    </style>
</head>
<body>
{content}
</body>
</html>"""

# Write HTML
with open('OpenStrand_Studio_Manual_v1101.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML file created: OpenStrand_Studio_Manual_v1101.html")
print("You can open this in any web browser and use 'Print to PDF' function")