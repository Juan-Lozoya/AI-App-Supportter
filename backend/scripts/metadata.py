import csv
import json
from pathlib import Path

CSV_PATH = Path("../data/Document_Metadata.csv")
DOCS_DIR = Path("../data/knowledge-base")
EXCLUDED_TYPES = {"RAG Evaluation Benchmark"}  # no va a la KB

with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
  for row in csv.DictReader(f):
    if row["document_type"] in EXCLUDED_TYPES:
      print(f"Omitido (no va a la KB): {row['filename']}")
      continue

    doc_path = DOCS_DIR / row["filename"]
    if not doc_path.exists():
      print(f"AVISO: no existe {doc_path}")
      continue

    attributes = {
      "document_id": row["document_id"],
      "document_type": row["document_type"],
      "company_name": row["company_name"],
      "event_type": row["event_type"],
      "announcement_date": row["announcement_date"],
      "announcement_date_num": int(row["announcement_date"].replace("-", "")),
      "security_id": row["security_id"],
      "keywords": [k.strip() for k in row["keywords"].split(",")],
    }

    sidecar = DOCS_DIR / f"{row['filename']}.metadata.json"
    sidecar.write_text(
      json.dumps({"metadataAttributes": attributes}, ensure_ascii=False, indent=2),
      encoding="utf-8",
    )
    print(f"Creado: {sidecar.name}")