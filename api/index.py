from http.server import BaseHTTPRequestHandler
import json
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({
            "status": "READY ONLINE TERHUBUNG",
            "service": "Khisd/AMNESIA_OSINT REST API",
            "endpoints": ["/api/lookup?type=npwp&q=Gibran&apikey=AMN3S14_DEMO","/api/status","/api/lookup?type=cctv&q=Bandung","/api/lookup?type=personel&q=AGUSTINUS"],
            "github": "Khisd/AMNESIA_OSINT",
            "email": "hafidzpanji00@gmail.com"
        }, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(body)
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","x-api-key, content-type")
        self.end_headers()
