from http.server import BaseHTTPRequestHandler
import json, os, csv
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# DATABASE-AMNESIA Vercel API
# Contoh:
#   /api/lookup?type=npwp&q=Gibran&apikey=KEY
#   /api/lookup?type=npwp&nik=3372052106610006&apikey=KEY
#   /api/lookup?type=kpu&q=Budi&apikey=KEY
#   /api/lookup?type=bsi&q=Ahmad&apikey=KEY
#   /api/lookup?type=personel&q=Komisaris&apikey=KEY
#   /api/lookup?type=indihome&q=Jakarta&apikey=KEY
#   /api/lookup?type=polda&q=Semarang&apikey=KEY
#   /api/lookup?type=militer&q=Infantri&apikey=KEY
#   /api/lookup?type=cctv&q=Bandung&apikey=KEY

BASE_DIR = Path(__file__).resolve().parent.parent
VAULT = BASE_DIR / "DATABASE VAULT"

VAULT_MAP = {
    "npwp":      VAULT / "npwp-10k-sample.csv",
    "kpu":       VAULT / "kpu.csv",
    "siak":      VAULT / "siak_clean_sample_1k.csv",
    "siak_full": VAULT / "siak_full_sample_1k.csv",
    "bsi":       VAULT / "ALL_EMPLOYEERS_BSI.csv",
    "kemendagri":VAULT / "KEMENDAGRI BY DIVACCX.txt",
    "dukcapil":  VAULT / "Dukcapil .txt",
    "personel":  VAULT / "personel1.json",
    "indihome":  VAULT / "myindihome_sample.csv",
    "polda":     VAULT / "poldajateng1.xlsx",
    "militer":   VAULT / "DATA_RAHASIA_MILITER_TNI_ANGKATAN_DARAT_DISINFOLAHTA_INDONESIA.xlsx",
    "cctv":      VAULT / "cctvapi.txt",
    "dokter":    VAULT / "doctors_perdosni.json",
    "perdosni":  VAULT / "doctors_perdosni.json",
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
            limit = 0 if limit <= 0 else min(limit, 500)
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
                    "/api/lookup?type=personel&q=Komisaris&apikey=AMN3S14_DEMO",
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
                        if keyword and keyword in " ".join(row.values()).lower():
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

            # --- XLSX ---
            if suffix == ".xlsx":
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(str(vault_file), read_only=True, data_only=True)
                    ws = wb.active
                    headers = None
                    all_matched = []
                    for row in ws.iter_rows(values_only=True):
                        if headers is None:
                            headers = [str(c) if c else "" for c in row]
                            continue
                        row_vals = [str(c) if c is not None else "" for c in row]
                        row_str = " ".join(row_vals).lower()
                        if keyword and keyword in row_str:
                            all_matched.append(dict(zip(headers, row_vals)))
                    total = len(all_matched)
                    if total == 0:
                        self._json({"total": 0, "keyword": keyword, "dataset": dataset,
                                    "data": [], "error": "Data tidak ditemukan"}, 404)
                        return
                    start = (page - 1) * limit if limit else 0
                    data = all_matched[start:start + limit] if limit else all_matched
                    self._json({"total": total, "page": page, "limit": limit,
                                "keyword": keyword, "dataset": dataset,
                                "file": vault_file.name, "data": data})
                    return
                except Exception as e:
                    self._json({"error": f"xlsx error: {e}"}, 500)
                    return

            # --- JSON (personel1.json) ---
            if suffix == ".json":
                all_matched = []
                dec = json.JSONDecoder()
                with open(vault_file, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                idx = 0
                n = len(text)
                while idx < n:
                    while idx < n and text[idx].isspace(): idx += 1
                    if idx >= n: break
                    if text[idx] not in "[{": idx += 1; continue
                    try:
                        obj, end = dec.raw_decode(text, idx)
                        idx = end
                        if isinstance(obj, list):
                            for item in obj:
                                item_str = json.dumps(item, ensure_ascii=False).lower()
                                if nik and isinstance(item, dict) and item.get("NIK") == nik:
                                    all_matched.append(item)
                                elif keyword and keyword in item_str:
                                    all_matched.append(item)
                            break
                        elif isinstance(obj, dict):
                            item_str = json.dumps(obj, ensure_ascii=False).lower()
                            if (nik and obj.get("NIK") == nik) or (keyword and keyword in item_str):
                                all_matched.append(obj)
                        while idx < n and text[idx] in ", \n\r\t]":
                            if text[idx] == "]": break
                            idx += 1
                        if idx < n and text[idx] == "]": break
                    except:
                        idx += 1
                total = len(all_matched)
                if total == 0:
                    self._json({"total": 0, "keyword": keyword or nik, "dataset": dataset,
                                "data": [], "error": "Data tidak ditemukan"}, 404)
                    return
                start = (page - 1) * limit if limit else 0
                data = all_matched[start:start + limit] if limit else all_matched
                self._json({"total": total, "page": page, "limit": limit,
                            "keyword": keyword or nik, "dataset": dataset,
                            "file": vault_file.name, "data": data})
                return

            # --- TXT / JSON array (cctv, dukcapil, kemendagri) ---
            with open(vault_file, "r", encoding="utf-8", errors="ignore") as f:
                peek = f.read(2048)
                f.seek(0)
                is_json_array = peek.strip().startswith("[")

            if is_json_array:
                buf = ""
                all_matched = []
                with open(vault_file, "r", encoding="utf-8", errors="ignore") as f:
                    while True:
                        chunk = f.read(2 * 1024 * 1024)
                        if not chunk: break
                        buf += chunk
                        while "}," in buf:
                            idx = buf.find("},")
                            obj_txt = buf[:idx + 1]
                            buf = buf[idx + 2:]
                            if keyword in obj_txt.lower():
                                try:
                                    all_matched.append(json.loads(obj_txt))
                                except: pass
                    if keyword in buf.lower() and buf.strip():
                        try:
                            tail = buf.strip().rstrip(",").rstrip("]")
                            if tail:
                                obj = json.loads(tail)
                                if keyword in json.dumps(obj).lower():
                                    all_matched.append(obj)
                        except: pass
                total = len(all_matched)
                start = (page - 1) * limit if limit else 0
                data = all_matched[start:start + limit] if limit else all_matched
                self._json({"total": total, "page": page, "limit": limit,
                            "keyword": keyword, "dataset": dataset,
                            "file": vault_file.name, "data": data})
            else:
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
