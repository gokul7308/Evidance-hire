import os
from pathlib import Path
from typing import Tuple

SUPPORTED_EXTENSIONS = {'.pdf', '.docx'}

def validate_file(file_path: str) -> Tuple[bool, str, str]:
    """
    Validates a resume file.
    
    Returns:
        Tuple[bool, str, str]: (is_valid, file_extension_or_empty, error_message)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, "", "File does not exist."
        
    if not path.is_file():
        return False, "", "Path is not a regular file."
        
    try:
        if os.path.getsize(file_path) == 0:
            return False, "", "File is empty."
    except OSError as e:
        return False, "", f"Could not read file size: {str(e)}"
        
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False, ext, f"Unsupported file type: {ext}. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        
    # We could do magic number checking here for better security, 
    # but based on the prompt simple extension checking + library parsing is sufficient for now.
    
    return True, ext, ""
