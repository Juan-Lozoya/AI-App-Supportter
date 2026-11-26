import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Corporate Actions Analyzer")

app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://localhost:5173"],
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED = {".pdf", ".xlsx", ".xls", ".csv", ".txt"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyses")
async def create_analysis(
    files: list[UploadFile] = File(default=[]),
    pasted_text: str | None = Form(default=None),
    holdings_file: UploadFile | None = File(default=None),
):
    if not files and not pasted_text:
        raise HTTPException(400, "Sube al menos un documento o pega texto.")

    analysis_id = str(uuid.uuid4())
    folder = UPLOAD_DIR / analysis_id
    folder.mkdir(parents=True)

    saved = []
    for f in [*files, *([holdings_file] if holdings_file else [])]:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            raise HTTPException(400, f"Formato no soportado: {f.filename}")
        (folder / f.filename).write_bytes(await f.read())
        saved.append(f.filename)

    if pasted_text:
        (folder / "pasted_text.txt").write_text(pasted_text, encoding="utf-8")
        saved.append("pasted_text.txt")

    return {"status": "queued"}
    # TODO (paso 2): extraer campos con los parsers y devolver resultados
    return {"analysis_id": analysis_id, "status": "queued", "files": saved}