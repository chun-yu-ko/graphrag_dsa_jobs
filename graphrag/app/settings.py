import os

INPUT_DIR = "./artifacts"
LANCEDB_URI = "./artifacts/lancedb"

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = "https://api.openai.com/v1"

MODEL_NAME_GLOBAL_SEARCH = "GraphRAG_DSAJ_Global_Search:20240729"
MODEL_NAME_LOCAL_SEARCH = "GraphRAG_DSAJ_Local_Search:20240729"

PORT = 8012