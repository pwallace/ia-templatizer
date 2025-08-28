import json
import os
import re
import warnings

def load_template(template_path):
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file '{template_path}' does not exist.")
    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)
    validate_template(template)
    return template

def is_valid_date(val):
    if not isinstance(val, str):
        return False
    pattern = r"^\d{2}[0-9x]{2}(-[0-9x]{2}){0,2}$"
    return bool(re.match(pattern, val))

def is_valid_url(url):
    url_pattern = r"^https?://[^\s]+$"
    return isinstance(url, str) and bool(re.match(url_pattern, url))

def validate_template(template):
    if "subject" not in template:
        raise ValueError("Template must contain a 'subject' field.")
    if not isinstance(template["subject"], list):
        raise ValueError("Template 'subject' field must be a list (even if empty).")
    valid_mediatypes = ['movies', 'audio', 'texts', 'software', 'image', 'data', 'DETECT']
    if "mediatype" in template and template["mediatype"] not in valid_mediatypes:
        warnings.warn(f"Invalid mediatype '{template['mediatype']}' in template. Must be one of {valid_mediatypes}.")

    # Validate rights-statement
    if 'rights-statement' in template:
        from fields import is_valid_rights_statement
        if not is_valid_rights_statement(template['rights-statement']):
            warnings.warn(f"Invalid rights statement '{template['rights-statement']}' in template.")

    # Validate inclusive-description-statement
    if 'inclusive-description-statement' in template:
        val = template['inclusive-description-statement']
        if not is_valid_url(val):
            warnings.warn(f"Inclusive description statement must be a valid URL. Got '{val}'.")

    # Validate date format
    if 'date' in template and not is_valid_date(template['date']):
        warnings.warn(f"Invalid date format '{template['date']}' in template. Expected format is YYYY-MM-DD, YYYY-MM, or YYYY, with 'x' allowed for digits.")

    # Validate licenseurl
    if 'licenseurl' in template:
        from fields import is_valid_licenseurl
        if not is_valid_licenseurl(template['licenseurl']):
            warnings.warn(f"Invalid license URL '{template['licenseurl']}' in template.")

    # Validate identifier-date
    if 'identifier-date' in template:
        val = template['identifier-date']
        if not (is_valid_date(val) or (isinstance(val, str) and val.upper() == "TRUE")):
            warnings.warn("identifier-date must be a date in YYYY, YYYY-MM, or YYYY-MM-DD format, or the string 'TRUE'.")