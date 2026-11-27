import re

from fastapi import UploadFile

from app import config

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".csv", ".txt"}

# Los formatos binarios se reconocen por sus primeros bytes (no solo por la extensión)
SIGNATURES = {
  ".pdf": b"%PDF-",
  ".xlsx": b"PK\x03\x04",  # .xlsx es un ZIP
}


class ValidationError(Exception):
  def __init__(self, message: str, status_code: int = 400):
    super().__init__(message)
    self.message = message
    self.status_code = status_code


def sanitize_filename(name: str) -> str:
  """Quita cualquier ruta y caracteres raros; evita path traversal."""
  base = re.split(r"[\\/]", name)[-1]
  base = re.sub(r"[^A-Za-z0-9._ -]", "_", base).strip(" .")
  return base[:150]


def read_upload(upload: UploadFile) -> bytes:
  """Lee el archivo sin pasar el límite de tamaño."""
  data = upload.file.read(config.MAX_UPLOAD_BYTES + 1)
  if len(data) > config.MAX_UPLOAD_BYTES:
    raise ValidationError(
      f"{upload.filename} exceeds the {config.MAX_UPLOAD_MB} MB limit.", 413
    )
  return data


def validate_file(original_filename: str, data: bytes) -> str:
  """Valida el archivo y devuelve el nombre seguro con el que se guardará."""
  safe_name = sanitize_filename(original_filename)
  if not safe_name:
    raise ValidationError("A file has an invalid name.")

  extension = "." + safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
  if extension not in ALLOWED_EXTENSIONS:
    raise ValidationError(
      f"Unsupported file type: {safe_name}. "
      f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
    )

  if not data:
    raise ValidationError(f"{safe_name} is empty.")

  signature = SIGNATURES.get(extension)
  if signature and not data.startswith(signature):
    raise ValidationError(f"{safe_name} does not look like a valid {extension} file.")

  if extension in {".csv", ".txt"} and b"\x00" in data[:8192]:
    raise ValidationError(f"{safe_name} looks like a binary file, not text.")

  return safe_name