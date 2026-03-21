import os
import uuid
from werkzeug.utils import secure_filename

# Allowed file extensions for images
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def validate_file(filename, allowed_extensions=None):
    """Validate file extension"""
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS
    
    if not filename:
        return False, "No file selected"
    
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if extension not in allowed_extensions:
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    return True, "File is valid"

def generate_secure_filename(filename):
    """Generate a secure filename using UUID"""
    if not filename:
        return None
    
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    secure_name = str(uuid.uuid4())
    
    return f"{secure_name}.{extension}" if extension else secure_name

def ensure_upload_directory(upload_dir):
    """Ensure upload directory exists"""
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def save_file_securely(file, upload_dir, filename=None):
    """Save file securely with generated filename"""
    if file is None:
        return None, "No file provided"
    
    if filename is None:
        filename = generate_secure_filename(file.filename)
    
    file_path = os.path.join(upload_dir, filename)
    
    try:
        file.save(file_path)
        return filename, "File saved successfully"
    except Exception as e:
        return None, f"Error saving file: {str(e)}"

def get_file_url(filename, upload_url_prefix):
    """Get the URL for a file"""
    if not filename:
        return None
    
    return f"{upload_url_prefix}/{filename}"

def create_upload_response(success, message=None, filename=None, file_url=None):
    """Create standardized upload response"""
    response = {"success": success}
    
    if message:
        response["message"] = message
    if filename:
        response["filename"] = filename
    if file_url:
        response["file_url"] = file_url
    
    return response
