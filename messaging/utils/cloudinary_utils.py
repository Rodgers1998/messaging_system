# messaging/utils/cloudinary_utils.py
import os
import logging
import mimetypes
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

cloudinary.config(cloudinary_url=os.getenv("CLOUDINARY_URL", ""))


def upload_media_to_cloudinary(file, folder: str = "shofco_messaging"):
    """
    Upload a file to Cloudinary and return (secure_url, resource_type).
    Returns (None, None) if upload fails.

    Preserves file extension in the public_id so mimetypes.guess_type()
    works correctly when Infobip needs to determine media type.
    """
    try:
        original_name = getattr(file, 'name', 'upload')
        ext = os.path.splitext(original_name)[1].lower()  # e.g. '.jpg', '.pdf'

        # Determine resource_type for Cloudinary
        mime, _ = mimetypes.guess_type(original_name)
        if mime:
            if mime.startswith("video"):
                resource_type = "video"
            elif mime.startswith("audio"):
                resource_type = "video"   # Cloudinary uses 'video' for audio too
            else:
                resource_type = "image"   # images + PDFs + docs
        else:
            resource_type = "auto"

        # Use original filename as public_id so URL retains the extension
        import uuid
        public_id = f"{folder}/{uuid.uuid4().hex}{ext}"

        result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=False,
        )
        url = result.get("secure_url")
        logger.info("Cloudinary upload success: %s (type: %s)", url, resource_type)
        return url, resource_type

    except Exception as e:
        logger.exception("Cloudinary upload failed: %s", str(e))
        return None, None