# messaging/utils/cloudinary_utils.py
import os
import logging
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configure Cloudinary from env var CLOUDINARY_URL
# Format: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
cloudinary.config(
    cloudinary_url=os.getenv("CLOUDINARY_URL", "")
)


def upload_media_to_cloudinary(file, folder: str = "shofco_messaging") -> str | None:
    """
    Upload a file object to Cloudinary and return its public URL.
    Returns None if upload fails.

    Usage:
        url = upload_media_to_cloudinary(request.FILES['media'])
    """
    try:
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type="auto",   # handles images, videos, PDFs automatically
        )
        url = result.get("secure_url")
        logger.info("Cloudinary upload success: %s", url)
        return url
    except Exception as e:
        logger.exception("Cloudinary upload failed: %s", str(e))
        return None