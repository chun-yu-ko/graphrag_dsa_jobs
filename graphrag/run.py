from app.main import app
import uvicorn
from app.settings import PORT
from app.utils import logger

if __name__ == "__main__":
    logger.info(f"Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)