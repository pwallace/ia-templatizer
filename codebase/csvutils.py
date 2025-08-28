import csv
import os
import warnings
import re

def load_csv(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file '{csv_path}' does not exist.")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def write_output_csv(output_path, output_data, fieldnames):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)

def is_valid_date(val):
    if not isinstance(val, str):
        return False
    pattern = r"^\d{2}[0-9x]{2}(-[0-9x]{2}){0,2}$"
    return bool(re.match(pattern, val))

def is_valid_url(url):
    url_pattern = r"^https?://[^\s]+$"
    return isinstance(url, str) and bool(re.match(url_pattern, url))

def validate_csv(csv_data):
    if not csv_data:
        warnings.warn("CSV file is empty or has no valid rows.")
        return

    required_fields = ['identifier']
    missing_fields = [field for field in required_fields if field not in csv_data[0]]
    if missing_fields:
        warnings.warn(f"CSV is missing required fields: {', '.join(missing_fields)}")

    valid_mediatypes = ['movies', 'audio', 'texts', 'software', 'image']
    if 'mediatype' in csv_data[0]:
        for row in csv_data:
            if row['mediatype'] not in valid_mediatypes:
                warnings.warn(f"Invalid mediatype '{row['mediatype']}' in CSV. Must be one of {valid_mediatypes}.")

    # Validate rights-statement
    if 'rights-statement' in csv_data[0]:
        from fields import is_valid_rights_statement
        for row in csv_data:
            if not is_valid_rights_statement(row['rights-statement']):
                warnings.warn(f"Invalid rights statement '{row['rights-statement']}' in CSV.")

    # Validate inclusive-description-statement
    if 'inclusive-description-statement' in csv_data[0]:
        for row in csv_data:
            val = row['inclusive-description-statement']
            if not is_valid_url(val):
                warnings.warn(f"Inclusive description statement must be a valid URL. Got '{val}'.")

    # Validate date format
    if 'date' in csv_data[0]:
        for row in csv_data:
            date_val = row['date']
            if date_val and not is_valid_date(date_val):
                warnings.warn(f"Invalid date format '{date_val}' in CSV. Expected format is YYYY-MM-DD, YYYY-MM, or YYYY, with 'x' allowed for digits.")

    # Validate licenseurl
    if 'licenseurl' in csv_data[0]:
        from fields import is_valid_licenseurl
        for row in csv_data:
            if not is_valid_licenseurl(row['licenseurl']):
                warnings.warn(f"Invalid license URL '{row['licenseurl']}' in CSV.")