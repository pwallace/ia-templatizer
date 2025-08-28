import os
import csv
from identifier import generate_identifier
from fields import get_repeatable_fields, detect_mediatype

def is_valid_file(filename):
    basename = os.path.basename(filename)
    if basename.startswith('.'):
        return False
    if basename.lower() == 'thumbs.db':
        return False
    if os.path.isdir(filename):
        return False
    return True

def list_directory_files(directory_path):
    files = []
    for entry in os.listdir(directory_path):
        full_path = os.path.join(directory_path, entry)
        if os.path.isfile(full_path) and is_valid_file(full_path):
            files.append(full_path)
    return files

def write_expanded_csv(base_output_path, directory_path, template, row, base_order):
    dir_name = os.path.basename(os.path.normpath(directory_path))
    base, ext = os.path.splitext(base_output_path)
    expanded_output_path = f"{base}_{dir_name}{ext}"

    files = list_directory_files(directory_path)
    output_rows = []
    existing_identifiers = set()

    control_fields = {
        "identifier-date", "identifier_prefix", "identifier-prefix", "identifier_basename"
    }

    non_repeatable_fields = {
        "identifier", "file", "mediatype", "color", "date", "licenseurl", "rights",
        "rights-statement", "publisher", "summary", "ai-note", "ai-summary",
        "title", "volume", "year", "issue"
    }.union(control_fields)
    repeatable_fields = get_repeatable_fields(template, non_repeatable_fields)
    repeatable_field_values = {field: template[field] for field in repeatable_fields}

    for file_path in files:
        new_row = row.copy()
        new_row['file'] = file_path

        for field, value in template.items():
            if field == "identifier":
                continue
            if field in control_fields:
                continue
            if field not in new_row or not new_row[field]:
                new_row[field] = value

        if template.get('mediatype', '').upper() == 'DETECT':
            detected_type = detect_mediatype(new_row['file'])
            new_row['mediatype'] = detected_type

        for field, values in repeatable_field_values.items():
            for i, item in enumerate(values):
                new_row[f"{field}[{i}]"] = item

        for field in repeatable_fields:
            if field in new_row and isinstance(new_row[field], list):
                del new_row[field]

        for field in control_fields:
            if field in new_row:
                del new_row[field]

        identifier_date = template.get('identifier-date', '')
        new_row['identifier'] = generate_identifier(new_row, template, identifier_date, existing_identifiers)

        output_rows.append(new_row)

    # Use base_order for output columns, then add any extras found in output_rows
    if output_rows:
        all_cols = set().union(*(row.keys() for row in output_rows))
        extra_cols = [col for col in all_cols if col not in base_order and col not in control_fields]
        output_fieldnames = base_order + extra_cols

        with open(expanded_output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            for out_row in output_rows:
                writer.writerow(out_row)
        print(f"Output of {directory_path} written to {expanded_output_path}")
        return True
    else:
        return False