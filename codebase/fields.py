import re

def get_repeatable_fields(template, non_repeatable_fields):
    return [
        field for field, value in template.items()
        if isinstance(value, list) and field not in non_repeatable_fields
    ]

def detect_mediatype(filename):
    """
    Detect the mediatype based on file extension.
    Returns one of: 'movies', 'audio', 'image', 'texts', 'data'
    """
    ext = filename.lower().split('.')[-1]
    # Movies
    movie_exts = {'mp4', 'mov', 'avi', 'mpg', 'mpeg', 'ogv', 'wmv', 'mkv', 'webm', 'flv', 'm4v'}
    # Audio
    audio_exts = {'wav', 'mp3', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'aiff', 'alac'}
    # Images
    image_exts = {'jpg', 'jpeg', 'tif', 'tiff', 'gif', 'bmp', 'png', 'webp', 'jp2', 'svg', 'heic'}
    # Texts
    text_exts = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'epub', 'csv', 'xls', 'xlsx', 'ppt', 'pptx'}
    if ext in movie_exts:
        return 'movies'
    elif ext in audio_exts:
        return 'audio'
    elif ext in image_exts:
        return 'image'
    elif ext in text_exts:
        return 'texts'
    else:
        return 'data'

def normalize_rights_statement_field(fieldname):
    """Normalize rights-statement field names to 'rights-statement'."""
    if fieldname.lower().replace('_', '').replace('-', '') in ['rightsstatement', 'rightsstatement']:
        return 'rights-statement'
    return fieldname

def is_valid_rights_statement(url):
    """
    Accepts only:
    - URLs from rightsstatements.org (current statements)
    - URLs for current Creative Commons licenses/dedications
    """
    # RightsStatements.org
    rs_pattern = r'^https?://rightsstatements\.org/vocab/[A-Z]{3}/1\.0/?$'
    # Creative Commons licenses/dedications
    cc_pattern = r'^https?://creativecommons\.org/(licenses|publicdomain)/[a-z\-]+/[0-9\.]+/?$'
    return bool(re.match(rs_pattern, url)) or bool(re.match(cc_pattern, url))

def is_valid_licenseurl(url):
    """
    Accepts only:
    - URLs for current Creative Commons licenses/dedications
    """
    cc_pattern = r'^https?://creativecommons\.org/(licenses|publicdomain)/[a-z\-]+/[0-9\.]+/?$'
    return bool(re.match(cc_pattern, url))