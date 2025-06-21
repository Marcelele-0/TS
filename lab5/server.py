from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/headers":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(str(self.headers).encode())
        else:
            # Obsługa plików statycznych z katalogu www/
            if self.path == "/":
                self.path = "/index.html"
            self.path = "/www" + self.path
            return super().do_GET()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))  # Ustaw katalog roboczy
    server = HTTPServer(('0.0.0.0', 4321), CustomHandler)
    print("Serwer działa na http://localhost:4321/")
    server.serve_forever()
