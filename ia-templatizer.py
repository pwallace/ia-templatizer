"""
ia-templatizer.py

-------------------------------------------------------------------------------
DESCRIPTION
-------------------------------------------------------------------------------
Main CLI application for applying a metadata template (JSON) to a CSV file for Internet Archive workflows.

This script loads a template and an input CSV, fills missing fields, generates identifiers, expands repeatable fields, validates metadata, and writes a new output CSV suitable for Internet Archive CLI tools and Python library.

-------------------------------------------------------------------------------
USAGE
-------------------------------------------------------------------------------
    python ia-templatizer.py [flags] <template_path> <csv_path> <output_path>

Example:
    python ia-templatizer.py --expand-directories template.json input.csv output.csv

-------------------------------------------------------------------------------
DETAILS
-------------------------------------------------------------------------------
- The template JSON may contain control fields and repeatable fields (lists).
- Identifiers are generated using template rules and file names if missing.
- Repeatable fields (lists) are expanded into indexed columns (e.g., subject[0], subject[1]).
- Output CSV columns are ordered for Internet Archive workflows.
- Control fields are not included in the output unless explicitly specified.
-------------------------------------------------------------------------------
"""

import sys
import os
import re
import warnings

# Import modules from codebase directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "codebase"))
from template import load_template
from csvutils import load_csv, write_output_csv, dedupe_preserve_order
from identifier import generate_identifier
from fields import get_repeatable_fields, detect_mediatype, normalize_rights_statement_field, is_valid_rights_statement, is_valid_licenseurl
from expand_directories import write_expanded_csv

def is_valid_url(url):
    url_pattern = r'^https?://[^\s]+$'
    return bool(re.match(url_pattern, url))

def validate_metadata_fields(metadata, context="row"):
    rs_val = metadata.get('rights-statement', metadata.get('rightsstatement', ''))
    if rs_val and not is_valid_rights_statement(rs_val):
        warnings.warn(f"Warning: Invalid rights-statement URL '{rs_val}' in {context}")

    lic_val = metadata.get('licenseurl', '')
    if lic_val and not is_valid_licenseurl(lic_val):
        warnings.warn(f"Warning: Invalid licenseurl '{lic_val}' in {context}")

    incl_val = metadata.get('inclusive-language-statement', '')
    if incl_val and not is_valid_url(incl_val):
        warnings.warn(f"Warning: Invalid inclusive-language-statement URL '{incl_val}' in {context}")

def main():
    if len(sys.argv) < 4:
        print("Usage: python ia-templatizer.py [flags] <template_path> <csv_path> <output_path>")
        sys.exit(1)

    template_path = sys.argv[-3]
    csv_path = sys.argv[-2]
    output_path = sys.argv[-1]
    flags = sys.argv[1:-3]
    allowed_flags = {'--expand-directories', '-E'}
    for flag in flags:
        if flag not in allowed_flags:
            print(f"Error: Unknown flag '{flag}'")
            print(f"Allowed flags: {', '.join(allowed_flags)}")
            sys.exit(1)
    expand_dirs = '--expand-directories' in flags or '-E' in flags

    template = load_template(template_path)
    validate_metadata_fields(template, context="template")
    csv_data = load_csv(csv_path)

    # Control fields used for logic, not output (support both hyphen and underscore)
    control_fields = {
        "identifier-date", "identifier_prefix", "identifier-prefix", "identifier_basename"
    }

    # Non-repeatable fields (for repeatable field detection)
    non_repeatable_fields = {
        "identifier", "file", "mediatype", "color", "date", "licenseurl", "rights",
        "rights-statement", "publisher", "summary", "ai-note", "ai-summary",
        "title", "volume", "year", "issue"
    }.union(control_fields)

    repeatable_fields = get_repeatable_fields(template, non_repeatable_fields)
    repeatable_field_values = {field: template[field] for field in repeatable_fields}

    output_data = []
    existing_identifiers = set()

    # We'll collect subject[n] and collection[n] columns for final ordering
    def get_repeatable_input(row, field):
        # If subject[n] columns exist, use those values
        n_keys = sorted([k for k in row.keys() if k.startswith(f"{field}[")], key=lambda x: int(x.split("[")[1].split("]")[0]))
        vals = []
        if n_keys:
            for k in n_keys:
                val = row[k]
                if val:
                    vals.append(val.strip() if isinstance(val, str) else val)
            # Remove subject[n] columns from row
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
            # Remove original fields from row
            for k in keys:
                if k in row:
                    del row[k]
        return vals

    for row in csv_data:
        # Normalize field names
        normalized_row = {}
        for k, v in row.items():
            norm_k = normalize_rights_statement_field(k)
            normalized_row[norm_k] = v.strip() if isinstance(v, str) else v
        row = normalized_row

        # Expand all repeatable fields: template values first, then input values, deduped
        for field in repeatable_fields:
            template_vals = repeatable_field_values.get(field, [])
            input_vals = get_repeatable_input(row, field)
            all_vals = dedupe_preserve_order(list(template_vals) + input_vals)
            for i, val in enumerate(all_vals):
                row[f"{field}[{i}]"] = val

        validate_metadata_fields(row, context="row")

        file_val = row.get('file', '')
        # We'll build fieldnames after collecting all output_data

        # Directory expansion logic
        if expand_dirs and file_val and os.path.isdir(file_val):
            try:
                os.listdir(file_val)
                expanded = write_expanded_csv(output_path, file_val, template, row)
                if expanded:
                    continue
            except Exception:
                pass

            # Treat as normal "data" item if expansion failed or directory not listable
            new_row = row.copy()
            new_row['mediatype'] = 'data'
            for field, value in template.items():
                if field == "identifier":
                    continue
                if field in control_fields:
                    continue
                if field not in new_row or not new_row[field]:
                    new_row[field] = value
            # Expand repeatable fields for directory row
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
            output_data.append(new_row)
            continue

        # Fill in missing fields from the template
        new_row = row.copy()
        for field, value in template.items():
            if field == "identifier":
                continue
            if field in control_fields:
                continue
            if field not in new_row or not new_row[field]:
                new_row[field] = value

        # Special mediatype detection
        if template.get('mediatype', '').upper() == 'DETECT':
            file_val = new_row.get('file', '')
            detected_type = detect_mediatype(file_val)
            # If file is a directory or unknown type, set mediatype to "data"
            if not detected_type or (file_val and os.path.isdir(file_val)):
                new_row['mediatype'] = 'data'
            else:
                new_row['mediatype'] = detected_type

        # Expand repeatable fields for main output row
        for field in repeatable_fields:
            template_vals = repeatable_field_values.get(field, [])
            input_vals = get_repeatable_input(new_row, field)
            all_vals = dedupe_preserve_order(list(template_vals) + input_vals)
            for i, val in enumerate(all_vals):
                new_row[f"{field}[{i}]"] = val

        # Remove original repeatable fields from output
        for field in repeatable_fields:
            if field in new_row and isinstance(new_row[field], list):
                del new_row[field]

        # Remove control fields from output
        for field in control_fields:
            if field in new_row:
                del new_row[field]

        identifier_date = template.get('identifier-date', '')
        new_row['identifier'] = generate_identifier(new_row, template, identifier_date, existing_identifiers)

        output_data.append(new_row)

    # Build fieldnames for output: identifier, file, mediatype, collection[n], title, date, creator, description, subject[n], extras
    all_cols = set().union(*(row.keys() for row in output_data))
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

    # Insert collection[n] after mediatype, subject[n] after description
    fieldnames = [
        "identifier", "file", "mediatype"
    ] + collection_n_cols + [
        "title", "date", "creator", "description"
    ] + subject_n_cols + extra_cols

    write_output_csv(output_path, output_data, fieldnames)
    print(f"Output written to '{output_path}'")

if __name__ == "__main__":
    main()

# End of ia-templatizer.py