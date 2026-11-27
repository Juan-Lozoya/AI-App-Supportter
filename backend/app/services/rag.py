import boto3

from app import config

_runtime = boto3.client("bedrock-agent-runtime", region_name=config.AWS_REGION)


def retrieve(query: str, top_k: int = 5, metadata_filter: dict | None = None) -> list[dict]:
  """Devuelve los chunks más relevantes de la Knowledge Base, sin generar texto."""
  if not config.KB_ID:
    raise RuntimeError("KB_ID is not configured")

  vector_config: dict = {"numberOfResults": top_k}
  if metadata_filter:
    vector_config["filter"] = metadata_filter

  response = _runtime.retrieve(
    knowledgeBaseId=config.KB_ID,
    retrievalQuery={"text": query},
    retrievalConfiguration={"vectorSearchConfiguration": vector_config},
  )

  return [
    {
      "text": item["content"]["text"],
      "score": item.get("score"),
      "source": item.get("location", {}).get("s3Location", {}).get("uri"),
      "metadata": item.get("metadata", {}),
    }
    for item in response["retrievalResults"]
  ]