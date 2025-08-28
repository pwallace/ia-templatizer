import re
import mimetypes

def get_repeatable_fields(template, non_repeatable_fields):
    return [k for k, v in template.items() if isinstance(v, list) and k not in non_repeatable_fields]

def detect_mediatype(filepath):
    if not filepath:
        return ""
    ext = filepath.lower().split('.')[-1]
    if ext in ['mp4', 'mov', 'avi', 'mkv']:
        return 'movies'
    if ext in ['mp3', 'wav', 'flac', 'aac']:
        return 'audio'
    if ext in ['pdf', 'epub', 'txt', 'doc', 'docx']:
        return 'texts'
    if ext in ['zip', 'tar', 'gz', 'rar']:
        return 'software'
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
        return 'image'
    # fallback to mimetypes
    mime, _ = mimetypes.guess_type(filepath)
    if mime:
        if mime.startswith('video'):
            return 'movies'
        if mime.startswith('audio'):
            return 'audio'
        if mime.startswith('image'):
            return 'image'
        if mime.startswith('application'):
            return 'software'
        if mime.startswith('text'):
            return 'texts'
    return ''

def normalize_rights_statement_field(fieldname):
    # Normalize rights-statement field names
    if fieldname.lower().replace("_", "-") in ("rights-statement", "rightsstatement"):
        return "rights-statement"
    return fieldname

def is_valid_rights_statement(val):
    # Accept only valid rightsstatements.org URLs
    if not isinstance(val, str):
        return False
    return val.startswith("http://rightsstatements.org/vocab/") or val.startswith("https://rightsstatements.org/vocab/")

def is_valid_licenseurl(val):
    # Accept only valid Creative Commons URLs
    if not isinstance(val, str):
        return False
    return val.startswith("https://creativecommons.org/") or val.startswith("http://creativecommons.org/")