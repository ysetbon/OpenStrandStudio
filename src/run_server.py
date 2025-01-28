from http.server import HTTPServer, SimpleHTTPRequestHandler
import subprocess
import webbrowser
import sys

class OpenStrandStudioHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>OpenStrand Studio</title>
            </head>
            <body>
                <h1>OpenStrand Studio</h1>
                <p>This is a PyQt5 desktop application and cannot be run directly in a web browser.</p>
                <p>To run the application:</p>
                <ol>
                    <li>Open a terminal or command prompt</li>
                    <li>Navigate to the directory containing OpenStrandStudio.pyz</li>
                    <li>Run the command: <code>python OpenStrandStudio.pyz</code></li>
                </ol>
                <button onclick="runApplication()">Attempt to Launch Application (Desktop Only)</button>
                <div id="output"></div>
                <script>
                function runApplication() {
                    fetch('/run')
                        .then(response => response.text())
                        .then(data => {
                            document.getElementById('output').innerText = data;
                        });
                }
                </script>
            </body>
            </html>
            ''')
        elif self.path == '/run':
            try:
                result = subprocess.run([sys.executable, 'OpenStrandStudio.pyz'], capture_output=True, text=True)
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                output = result.stdout if result.stdout else "Application launched, but no output was captured."
                self.wfile.write(output.encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error running application: {str(e)}".encode())
        else:
            super().do_GET()

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, OpenStrandStudioHandler)
    print(f"Server running on http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()