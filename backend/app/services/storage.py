import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app import config

logger = logging.getLogger("corpactions.storage")

_s3 = boto3.client("s3", region_name=config.AWS_REGION)


class StorageError(Exception):
  pass


@dataclass
class PreparedFile:
  role: str                       # announcement | holdings | pasted_text
  original_filename: str
  filename: str                   # nombre ya saneado
  data: bytes
  client_content_type: str | None


def save_analysis(analysis_id: str, prepared: list[PreparedFile]) -> list[dict]:
  """Sube los archivos a S3 y escribe el log de auditoría. Devuelve el detalle de cada archivo."""
  if not config.DOCS_BUCKET:
    raise StorageError("DOCS_BUCKET is not configured")

  created_at = datetime.now(timezone.utc)
  stored: list[dict] = []

  try:
    for item in prepared:
      key = f"uploads/{analysis_id}/{item.role}/{item.filename}"
      _s3.put_object(
        Bucket=config.DOCS_BUCKET,
        Key=key,
        Body=item.data,
        ContentType="application/octet-stream",
      )
      stored.append(
        {
          "role": item.role,
          "original_filename": item.original_filename,
          "filename": item.filename,
          "stored_key": key,
          "size_bytes": len(item.data),
          "client_content_type": item.client_content_type,
          "sha256": hashlib.sha256(item.data).hexdigest(),
          "validation": "passed",
        }
      )

    # El log no incluye el contenido de los documentos, solo metadatos y hash
    log_entry = {
      "analysis_id": analysis_id,
      "created_at": created_at.isoformat(),
      "status": "uploaded",
      "files": stored,
    }
    _s3.put_object(
      Bucket=config.DOCS_BUCKET,
      Key=f"logs/uploads/{created_at:%Y-%m-%d}/{analysis_id}.json",
      Body=json.dumps(log_entry, indent=2).encode("utf-8"),
      ContentType="application/json",
    )
  except (BotoCoreError, ClientError) as exc:
    logger.exception("S3 write failed for analysis %s", analysis_id)
    raise StorageError("Could not store the uploaded files.") from exc

  logger.info("Analysis %s stored (%d files)", analysis_id, len(stored))
  return stored