# DATABASE-AMNESIA Vault API

Vercel serverless API untuk query database AMNESIA OSINT.

## Endpoints

```
GET /api/lookup?type=npwp&q=Gibran&apikey=KEY
GET /api/lookup?type=npwp&nik=3372052106610006&apikey=KEY
GET /api/lookup?type=npwp&npwp=065729212526000&apikey=KEY
GET /api/lookup?type=kpu&q=Budi&apikey=KEY
GET /api/lookup?type=bsi&q=Ahmad&apikey=KEY
GET /api/lookup?type=siak&q=Sari&apikey=KEY
GET /api/lookup?type=kemendagri&q=Jakarta&apikey=KEY
GET /api/lookup?type=dukcapil&q=Surabaya&apikey=KEY
```

## Datasets

| type | File | Keterangan |
|---|---|---|
| `npwp` | npwp-10k-sample.csv | Data NPWP + NIK + Nama + Alamat |
| `kpu` | kpu.csv | Data pemilih KPU |
| `siak` | siak_clean_sample_1k.csv | Data SIAK kependudukan |
| `siak_full` | siak_full_sample_1k.csv | Data SIAK lengkap |
| `bsi` | ALL_EMPLOYEERS_BSI.csv | Data karyawan BSI |
| `kemendagri` | KEMENDAGRI BY DIVACCX.txt | Data Kemendagri |
| `dukcapil` | Dukcapil .txt | Data Dukcapil |

## Auth

Kirim apikey via query param atau header:
- `?apikey=AMN3S14_DEMO`
- `x-api-key: AMN3S14_DEMO`
