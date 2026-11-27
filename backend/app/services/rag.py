import os
import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET = os.environ["DOCS_BUCKET"]
KB_ID = os.environ["KB_ID"]
DS_ID = os.environ["KB_DATA_SOURCE_ID"]
MODEL_ARN = os.environ["BEDROCK_MODEL_ARN"]

s3 = boto3.client("s3", region_name=REGION)
agent = boto3.client("bedrock-agent", region_name=REGION)
runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)


def upload_document(analysis_id: str, filename: str, fileobj) -> str:
  key = f"documents/{analysis_id}/{filename}"
  s3.upload_fileobj(fileobj, BUCKET, key)
  return key


def start_ingestion() -> str:
  """Le dice a Bedrock que re-indexe lo que haya en S3."""
  r = agent.start_ingestion_job(knowledgeBaseId=KB_ID, dataSourceId=DS_ID)
  return r["ingestionJob"]["ingestionJobId"]


def ingestion_status(job_id: str) -> str:
  r = agent.get_ingestion_job(
    knowledgeBaseId=KB_ID, dataSourceId=DS_ID, ingestionJobId=job_id
  )
  return r["ingestionJob"]["status"]  # STARTING | IN_PROGRESS | COMPLETE | FAILED


def ask(question: str, top_k: int = 5) -> dict:
  r = runtime.retrieve_and_generate(
    input={"text": question},
    retrieveAndGenerateConfiguration={
      "type": "KNOWLEDGE_BASE",
      "knowledgeBaseConfiguration": {
        "knowledgeBaseId": KB_ID,
        "modelArn": MODEL_ARN,
        "retrievalConfiguration": {
          "vectorSearchConfiguration": {"numberOfResults": top_k}
        },
      },
    },
  )
  return {"answer": r["output"]["text"], "citations": r.get("citations", [])}