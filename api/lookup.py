from http.server import BaseHTTPRequestHandler
import json, os, csv
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# DATABASE-AMNESIA Vercel API
# Contoh:
#   /api/lookup?type=npwp&q=Gibran&apikey=KEY
#   /api/lookup?type=npwp&nik=3372052106610006&apikey=KEY
#   /api/lookup?type=npwp&npwp=065729212526000&apikey=KEY
#   /api/lookup?type=kpu&q=Budi&apikey=KEY
#   /api/lookup?type=bsi&q=Ahmad&apikey=KEY
#   /api/lookup?type=siak&q=Sari&apikey=KEY

BASE_DIR = Path(__file__).resolve().parent.parent
VAULT = BASE_DIR / "DATABASE VAULT"

VAULT_MAP = {
    "npwp":       VAULT / "npwp-10k-sample.csv",
    "kpu":        VAULT / "kpu.csv",
    "siak":       VAULT / "siak_clean_sample_1k.csv",
    "siak_full":  VAULT / "siak_full_sample_1k.csv",
    "bsi":        VAULT / "ALL_EMPLOYEERS_BSI.csv",
    "kemendagri": VAULT / "KEMENDAGRI BY DIVACCX.txt",
    "dukcapil":   VAULT / "Dukcapil .txt",
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # Auth
        need_key = os.getenv("API_KEY", os.getenv("VERCEL_API_KEY", "AMN3S14_DEMO"))
        got_key = (qs.get("apikey", [""])[0] or qs.get("key", [""])[0]
                   or self.headers.get("x-api-key", "") or self.headers.get("X-Api-Key", ""))
        if need_key and got_key != need_key:
            self._json({"error": "apikey salah — kirim ?apikey=KEY atau header x-api-key"}, 401)
            return

        # Dataset
        dataset = (qs.get("type", [""])[0] or qs.get("dataset", [""])[0] or "").strip().lower()
        if not dataset or dataset not in VAULT_MAP:
            self._json({
                "error": f"dataset '{dataset}' tidak tersedia.",
                "datasets": list(VAULT_MAP.keys()),
                "contoh": "/api/lookup?type=npwp&q=Gibran&apikey=AMN3S14_DEMO"
            }, 400)
            return

        # Query params
        q    = (qs.get("q", [""])[0] or qs.get("keyword", [""])[0] or
                qs.get("nama", [""])[0] or "").strip()
        nik  = qs.get("nik", [""])[0].strip()
        npwp = qs.get("npwp", [""])[0].strip()
        keyword = q.lower()

        # Limit & page
        try:
            limit = int(qs.get("limit", ["20"])[0])
            if limit <= 0:
                limit = 0
            else:
                limit = min(limit, 500)
        except:
            limit = 20

        try:
            page = max(1, int(qs.get("page", ["1"])[0]))
        except:
            page = 1

        if not keyword and not nik and not npwp:
            self._json({
                "error": "param q/nama/nik/npwp wajib",
                "datasets": list(VAULT_MAP.keys()),
                "contoh": [
                    "/api/lookup?type=npwp&q=Gibran&apikey=AMN3S14_DEMO",
                    "/api/lookup?type=npwp&nik=3372052106610006&apikey=AMN3S14_DEMO",
                    "/api/lookup?type=kpu&q=Budi&apikey=AMN3S14_DEMO",
                ]
            }, 400)
            return

        vault_file = VAULT_MAP[dataset]
        if not vault_file.exists():
            self._json({"total": 0, "dataset": dataset, "data": [],
                        "note": f"{vault_file.name} not in bundle"}, 404)
            return

        try:
            suffix = vault_file.suffix.lower()

            # --- CSV ---
            if suffix == ".csv":
                all_matched = []
                with open(vault_file, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        row = {k: (v or "").strip() for k, v in row.items()}
                        if nik:
                            if row.get("NIK", "") == nik:
                                all_matched.append(row)
                            continue
                        if npwp:
                            if row.get("NPWP", "") == npwp:
                                all_matched.append(row)
                            continue
                        if keyword:
                            if keyword in " ".join(row.values()).lower():
                                all_matched.append(row)

                total = len(all_matched)
                if total == 0:
                    self._json({"total": 0, "keyword": keyword or nik or npwp,
                                "dataset": dataset, "data": [], "error": "Data tidak ditemukan"}, 404)
                    return
                start = (page - 1) * limit if limit else 0
                data = all_matched[start:start + limit] if limit else all_matched
                self._json({"total": total, "page": page, "limit": limit,
                            "keyword": keyword or nik or npwp,
                            "dataset": dataset, "file": vault_file.name, "data": data})
                return

            # --- TXT line grep ---
            all_matched = []
            with open(vault_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if keyword and keyword in line.lower():
                        all_matched.append({"line": line.strip()[:600]})
            total = len(all_matched)
            start = (page - 1) * limit if limit else 0
            data = all_matched[start:start + limit] if limit else all_matched
            self._json({"total": total, "page": page, "limit": limit,
                        "keyword": keyword, "dataset": dataset,
                        "file": vault_file.name, "data": data})

        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "x-api-key, content-type")
        self.send_header("Cache-Control", "s-maxage=60, stale-while-revalidate=30")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "x-api-key, content-type")
        self.end_headers()
