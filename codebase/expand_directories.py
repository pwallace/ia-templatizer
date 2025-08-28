import os
import csv
from identifier import generate_identifier
from fields import get_repeatable_fields, detect_mediatype, normalize_rights_statement_field
from csvutils import dedupe_preserve_order

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

def get_repeatable_input(row, field):
    # If subject[n] columns exist, use those values
    n_keys = sorted([k for k in row.keys() if k.startswith(f"{field}[")], key=lambda x: int(x.split("[")[1].split("]")[0]))
    vals = []
    if n_keys:
        for k in n_keys:
            val = row[k]
            if val:
                vals.append(val.strip() if isinstance(val, str) else val)
        for k in n_keys:
            del row[k]
    else:
        # Otherwise, look for subject/subjects/keywords and split on semicolons
        keys = [k for k in row.keys() if k.lower() == field or k.lower() == field + "s" or (field == "subject" and k.lower() == "keywords")]
        for k in keys:
            val = row[k]
            if val:
                if isinstance(val, list):
                    vals.extend([v.strip() for v in val if isinstance(v, str) and v.strip()])
                elif isinstance(val, str):
                    vals.extend([v.strip() for v in val.split(";") if v.strip()])
        for k in keys:
            if k in row:
                del row[k]
    return vals

def write_expanded_csv(base_output_path, directory_path, template, row):
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

        # Mediatype detection logic (matches main script)
        if template.get('mediatype', '').upper() == 'DETECT':
            detected_type = detect_mediatype(new_row['file'])
            if not detected_type or (new_row['file'] and os.path.isdir(new_row['file'])):
                new_row['mediatype'] = 'data'
            else:
                new_row['mediatype'] = detected_type

        # Expand repeatable fields: template values first, then input values, deduped
        for field in repeatable_fields:
            template_vals = repeatable_field_values.get(field, [])
            input_vals = get_repeatable_input(new_row, field)
            all_vals = dedupe_preserve_order(list(template_vals) + input_vals)
            for i, val in enumerate(all_vals):
                new_row[f"{field}[{i}]"] = val

        for field in repeatable_fields:
            if field in new_row and isinstance(new_row[field], list):
                del new_row[field]

        for field in control_fields:
            if field in new_row:
                del new_row[field]

        identifier_date = template.get('identifier-date', '')
        new_row['identifier'] = generate_identifier(new_row, template, identifier_date, existing_identifiers)

        output_rows.append(new_row)

    # Build fieldnames for output: identifier, file, mediatype, collection[n], title, date, creator, description, subject[n], extras
    if output_rows:
        all_cols = set().union(*(row.keys() for row in output_rows))
        exclude_subject_keys = {"subject", "subjects", "keywords"}
        exclude_collection_keys = {"collection", "collections"}

        collection_n_cols = sorted(
            [col for col in all_cols if col.startswith("collection[")],
            key=lambda x: int(x.split("[")[1].split("]")[0])
        )
        subject_n_cols = sorted(
            [col for col in all_cols if col.startswith("subject[")],
            key=lambda x: int(x.split("[")[1].split("]")[0])
        )
        extra_cols = [
            col for col in all_cols
            if col not in {
                "identifier", "file", "mediatype", "title", "date", "creator", "description"
            }
            and col not in control_fields
            and col.lower() not in exclude_subject_keys
            and col.lower() not in exclude_collection_keys
            and not col.startswith("subject[")
            and not col.startswith("collection[")
        ]

        fieldnames = [
            "identifier", "file", "mediatype"
        ] + collection_n_cols + [
            "title", "date", "creator", "description"
        ] + subject_n_cols + extra_cols

        with open(expanded_output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for out_row in output_rows:
                writer.writerow(out_row)
        print(f"Output of {directory_path} written to {expanded_output_path}")
        return True
    else:
        return False