import logging, re, os
from google.cloud import storage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_response(response):
    paragraphs = re.split(r'\n{2,}', response)
    formatted_paragraphs = []
    for para in paragraphs:
        if '```' in para:
            parts = para.split('```')
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    parts[i] = f"\n```\n{part.strip()}\n```\n"
            para = ''.join(parts)
        else:
            para = para.replace('. ', '.\n')

        formatted_paragraphs.append(para.strip())

    return '\n\n'.join(formatted_paragraphs)

def download_artifacts():
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(os.getenv("GCS_BUCKET_NAME"))
    blobs = bucket.list_blobs()
    destination_dir = "./"

    for blob in blobs:

        path = os.path.join(destination_dir, blob.name)
        dir = os.path.dirname(path)
        
        if not os.path.exists(dir):
            os.makedirs(dir)
        
        blob.download_to_filename(path)
        logger.info(f"Blob {blob.name} downloaded to {path}.")