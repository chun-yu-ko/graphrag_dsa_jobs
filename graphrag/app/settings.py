import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.path.join(BASE_DIR, "artifacts")
LANCEDB_URI = os.path.join(BASE_DIR, "artifacts/lancedb")

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = "https://api.openai.com/v1"

MODEL_NAME_GLOBAL_SEARCH = "GraphRAG_DSAJ_Global_Search:20240729"
MODEL_NAME_LOCAL_SEARCH = "GraphRAG_DSAJ_Local_Search:20240729"

PORT = 8012