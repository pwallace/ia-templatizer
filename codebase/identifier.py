import os
import re
import time

def sanitize_filename(filename):
    filename = filename.replace(' ', '_')
    return re.sub(r'[^A-Za-z0-9\-_]', '', filename)

def smart_truncate(identifier, max_length=80):
    if len(identifier) <= max_length:
        return identifier
    for delim in ['-_-', '_-_', '-', '_']:
        idx = identifier.rfind(delim, 0, max_length)
        if idx != -1 and idx > 0:
            return identifier[:idx]
    return identifier[:max_length]

def is_valid_date(val):
    pattern = r"^\d{2}[0-9x]{2}(-[0-9x]{2}){0,2}$"
    return isinstance(val, str) and bool(re.match(pattern, val))

def generate_identifier(row, template, identifier_date, existing_identifiers=None):
    if existing_identifiers is None:
        existing_identifiers = set()

    identifier_prefix = template.get('identifier_prefix', template.get('identifier-prefix', ''))
    identifier_basename = template.get('identifier_basename', '')
    date_part = identifier_date if identifier_date else ''

    if isinstance(identifier_date, str) and identifier_date.upper() == "TRUE":
        date_val = row.get('date', '')
        if is_valid_date(date_val):
            date_part = date_val

    if 'identifier' in row and row['identifier']:
        base_id = sanitize_filename(row['identifier'])
    elif 'file' in row and row['file']:
        file_name = os.path.basename(row['file'])
        base_name, _ = os.path.splitext(file_name)
        base_id = sanitize_filename(base_name)
    else:
        base_id = 'item'

    id_core = identifier_basename if identifier_basename else base_id

    parts = [identifier_prefix]
    if date_part:
        parts.append(date_part)
    parts.append(id_core)
    if not identifier_basename and base_id != id_core:
        parts.append(base_id)
    identifier = '_'.join([p for p in parts if p])

    truncated_identifier = smart_truncate(identifier, 80)

    final_identifier = truncated_identifier
    counter = 1
    while final_identifier in existing_identifiers:
        timestamp = str(int(time.time()))
        suffix = f"_{timestamp}-{counter:03d}"
        base_length = 80 - len(suffix)
        base = smart_truncate(truncated_identifier, base_length)
        final_identifier = f"{base}{suffix}"
        counter += 1

    existing_identifiers.add(final_identifier)
    return final_identifier