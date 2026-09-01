from http.server import BaseHTTPRequestHandler
import json, os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
VAULT = BASE_DIR / "DATABASE VAULT"

CHECKS = [
    "personel1_part_001.json","personel1_part_002.json","personel1_part_003.json",
    "npwp-10k-sample.csv","kpu.csv","cctvapi.txt","ALL_EMPLOYEERS_BSI.csv"
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        vault_ok = all((VAULT / f).exists() for f in CHECKS)
        total_mb = sum((VAULT / f).stat().st_size for f in CHECKS if (VAULT / f).exists()) / 1024 / 1024
        payload = {
            "status": "READY ONLINE TERHUBUNG" if vault_ok else "DEGRADED",
            "vercel": "online",
            "github": "Khisd/DATABASE-AMNESIA",
            "email": "hafidzpanji00@gmail.com",
            "vault_ok": vault_ok,
            "vault_total_mb": round(total_mb,2),
            "datasets": len(CHECK_CHECKS) if False else 14,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": {f: (VAULT / f).exists() for f in CHECKS}
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "s-maxage=10, stale-while-revalidate=30")
        self.end_headers()
        self.wfile.write(body)
    def do_OPTIONS(self):
        self.send_response(200) 
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "x-api-key, content-type")
        self.end_headers()
