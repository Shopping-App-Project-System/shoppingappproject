import cloudinary
import cloudinary.uploader

from settings import CLOUDINARY_CLOUD_NAME,CLOUDINARY_API_KEY,CLOUDINARY_API_SECRET
cloudinary.config(
    cloud_name = CLOUDINARY_CLOUD_NAME,
    api_key = CLOUDINARY_API_KEY,
    api_secret = CLOUDINARY_API_SECRET,
    secure = True
    )

def save_image(file, folder, filename=None):
    if file and file.filename:
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            public_id=filename
        )
        return result["secure_url"]
    return None
