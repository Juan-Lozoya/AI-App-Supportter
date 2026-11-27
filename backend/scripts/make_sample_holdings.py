"""Genera archivos de holdings SINTÉTICOS para probar el parser. No son datos reales."""
import csv
from pathlib import Path

OUT_DIR = Path("../data")
OUT_DIR.mkdir(exist_ok=True)

HEADER = ["Account", "Account Name", "Security Name", "ISIN", "CUSIP", "Ticker", "Quantity", "Currency"]
ROWS = [
  ["ACC-1001", "Sample Pension Fund A", "Aetheris Energy Holdings PLC", "GB00B9X4K218", "", "AETH", "12,500", "USD"],
  ["ACC-1002", "Sample Growth Fund B", "Aetheris Energy Holdings PLC", "GB00B9X4K218", "", "AETH", "3000", "USD"],
  ["ACC-1003", "Sample Income Fund C", "Veloce Semiconductor Corporation", "US92264B1052", "92264B105", "VLCE", "8000", "USD"],
  ["ACC-1004", "Sample Trust D", "Kestrel BioLabs Inc.", "", "49251M108", "KBLB", "5000", "USD"],
  ["ACC-1005", "Sample Fund E", "Meridian Rail Systems Inc.", "", "", "MRSI", "2,000", "USD"],
  ["ACC-1006", "Sample Fund F", "OmniCorp Industrial Group Inc.", "US68215P1049", "", "OMNI", "1.500", "USD"],
  ["ACC-1007", "Sample Fund G", "Solstice Renewables AG", "DE000SLR8804", "", "SLR", "4500", "EUR"],
  ["ACC-1008", "Sample Fund H", "Unknown Company", "XX123", "", "", "abc", "USD"],
  ["ACC-1001", "Sample Pension Fund A", "Aetheris Energy Holdings PLC", "GB00B9X4K218", "", "AETH", "500", "USD"],
  ["", "", "Veloce Semiconductor Corporation", "US92264B1052", "", "VLCE", "100", "USD"],
  ["ACC-1009", "Sample Fund I", "Veloce Semiconductor Corporation", "US92264B1052", "", "VLCE", "(200)", "USD"],
  ["Total", "", "", "", "", "", "35,800", ""],
]

with (OUT_DIR / "sample_holdings.csv").open("w", newline="", encoding="utf-8") as f:
  writer = csv.writer(f)
  writer.writerow(HEADER)
  writer.writerows(ROWS)
print("Creado: data/sample_holdings.csv")

try:
  from openpyxl import Workbook
except ImportError:
  print("openpyxl no está instalado: se omitió el .xlsx")
else:
  wb = Workbook()
  ws = wb.active
  ws.title = "Holdings"
  ws.append(["SAMPLE DATA - Fictional holdings report"])
  ws.append(["As of 2026-11-26"])
  ws.append([])
  ws.append(HEADER)
  for row in ROWS:
      ws.append(row)
  wb.save(OUT_DIR / "sample_holdings.xlsx")
  print("Creado: data/sample_holdings.xlsx (con filas de título antes del encabezado)")