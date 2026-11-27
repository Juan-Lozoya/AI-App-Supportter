from typing import Literal
from pydantic import BaseModel, Field

class UploadedFileInfo(BaseModel):
  role: Literal["announcement", "holdings", "pasted_text"]
  filename: str
  size_bytes: int
  sha256: str

class AnalysisCreated(BaseModel):
  analysis_id: str
  status: Literal["uploaded"]
  files: list[UploadedFileInfo]

class KbSearchRequest(BaseModel):
  query: str = Field(min_length=3, max_length=500)
  top_k: int = Field(default=5, ge=1, le=20)
