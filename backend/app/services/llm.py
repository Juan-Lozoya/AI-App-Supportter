import logging
from dataclasses import dataclass

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app import config

logger = logging.getLogger("corpactions.llm")

_client = boto3.client(
  "bedrock-runtime",
  region_name=config.AWS_REGION,
  config=Config(connect_timeout=10, read_timeout=180, retries={"max_attempts": 3, "mode": "standard"}),
)


class LLMError(Exception):
    pass


@dataclass
class ToolResult:
  data: dict
  model_id: str
  input_tokens: int
  output_tokens: int
  latency_ms: int


def call_tool(*, model_id: str, system: str, user_text: str, tool_name: str,
              tool_description: str, input_schema: dict, max_tokens: int = 3000) -> ToolResult:
  """Llama al modelo obligándolo a responder con una herramienta (salida estructurada)."""
  if not model_id:
    raise LLMError("BEDROCK_MODEL_ID is not configured.")
  try:
    response = _client.converse(
      modelId=model_id,
      system=[{"text": system}],
      messages=[{"role": "user", "content": [{"text": user_text}]}],
      toolConfig={
        "tools": [{"toolSpec": {
          "name": tool_name,
          "description": tool_description,
          "inputSchema": {"json": input_schema},
        }}],
        "toolChoice": {"tool": {"name": tool_name}},
      },
      inferenceConfig={"maxTokens": max_tokens},
    )
  except (BotoCoreError, ClientError) as exc:
    logger.exception("Bedrock converse failed (model=%s)", model_id)
    raise LLMError("The language model request failed. Check backend logs.") from exc

  if response.get("stopReason") == "max_tokens":
    raise LLMError("The model response was cut off before completion.")

  for block in response["output"]["message"]["content"]:
    if "toolUse" in block:
      usage = response.get("usage", {})
      return ToolResult(
        data=block["toolUse"]["input"],
        model_id=model_id,
        input_tokens=int(usage.get("inputTokens", 0)),
        output_tokens=int(usage.get("outputTokens", 0)),
        latency_ms=int(response.get("metrics", {}).get("latencyMs", 0)),
      )
  raise LLMError("The model did not return structured output.")