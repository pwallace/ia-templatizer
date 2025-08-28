# IA Templatizer User & Developer Manual

---

## Overview

**IA Templatizer** is a command-line tool for batch-generating metadata CSV files for Internet Archive workflows.  
It applies a user-defined metadata template (JSON) to an input CSV, filling in missing fields, generating standardized identifiers, expanding repeatable fields, and validating metadata.  
The output is a new CSV formatted for compatibility with Internet Archive CLI tools and Python library.

This tool is designed for a wide range of archival materials, including historical photographs, scanned texts, audio/video, and born-digital data.

---

## Features

- **Template-driven metadata:** Fill in missing or default metadata from a JSON template.
- **Identifier generation:** Automatically create standardized identifiers using template rules and file names.
- **Repeatable fields:** Expand list fields (e.g., `subject`, `collection`) into indexed columns (`subject[0]`, `subject[1]`, etc.), with template values first, then deduplicated input values.
- **Input normalization:** Strips leading/trailing whitespace from all input CSV cell data before processing.
- **Validation:** Checks for valid media types, license URLs, rights statements, and date formats.
- **Custom column ordering:** Output CSV columns are ordered for Internet Archive workflows.
- **Control fields:** Template control fields (e.g., `identifier-date`, `identifier-prefix`) affect behavior but are not included in the output unless explicitly specified.
- **Robust error handling:** Clear error messages for missing files, invalid formats, and unsupported values.
- **Directory expansion:** Optionally expand directory paths in the input CSV to generate additional output sheets for their contents.
- **Extensible codebase:** Modular Python scripts for easy customization and extension.

---

## Usage

### Command

```bash
python ia-templatizer.py [flags] <template_path> <csv_path> <output_path>
```

- `<template_path>`: Path to your metadata template JSON file.
- `<csv_path>`: Path to your input CSV file.
- `<output_path>`: Path for the output CSV file.
- `[flags]`: Optional flags to control program behavior (see below).

### Example

```bash
python ia-templatizer.py --expand-directories templates/sample-template_01.json tests/sample-files-listing.csv tests/list-out.csv
```

### Option Flags

| Flag                   | Description                                                                                   |
|------------------------|-----------------------------------------------------------------------------------------------|
| `--expand-directories` | When a directory path is found in the `file` column, generate an additional output CSV sheet  |
| `-E`                   | Same as `--expand-directories`                                                               |

**Note:** Only the above flags are currently supported. Any other flags will result in an error.

---

## Directory Expansion

When the `--expand-directories` or `-E` flag is used:

- If a row in the input CSV has a directory path in its `file` column and the directory exists and is listable:
  - The row is **not** added to the main output CSV.
  - A new output CSV is created, named with `_{last-directory-name}` appended before the extension.
  - Each file in the directory is treated as a new item: a full metadata row is generated for it using the template and original row, and written to the directory output sheet.
  - Hidden files, subdirectories, and `Thumbs.db` are excluded.
  - After processing the directory, the script continues with the next row in the input CSV.
- If the directory does **not** exist or is not listable:
  - The row is added to the main output CSV as usual, with its `mediatype` set to `"data"`.

---

## Template File Format (JSON)

A well-formed template JSON file contains metadata fields and control fields. Example:

```json
{
  "identifier-prefix": "born-digital",
  "mediatype": "DETECT",
  "collection": ["middleburycollege"],
  "creator": "Middlebury College",
  "rights-statement": "http://rightsstatements.org/vocab/CNE/1.0/",
  "subject": ["Baseball", "Team photos", "Athletes"],
  "inclusive-description-statement": "This collection aims to represent diverse communities and experiences."
}
```

#### Control Fields

- `identifier-date`: If a valid date (YYYY, YYYY-MM, YYYY-MM-DD, or with 'x' for uncertainty), it is inserted in the identifier. If `"TRUE"`, the value from the input CSV's `date` column is used (if valid).
- `identifier-prefix` or `identifier_prefix`: Used to construct identifiers. Hyphen and underscore are both supported.
- `identifier-basename` or `identifier_basename`: Used as the core part of the identifier.
- Repeatable fields (lists) such as `subject`, `collection`, etc., are expanded into indexed columns.
- Control fields are **never** written to output CSVs.

---

## Input CSV File Format

A well-formed input CSV must have a header row. The `identifier` column is required unless `file` is present.

Example:

```csv
file,title,contributor,notes,date
02baseball/team1.jpg,"Middlebury College Baseball, 2002",,"Team photo",2020-05-01
02baseball/anderson.jpg,"Middlebury College Baseball, 2002: Nate Anderson",Nate Anderson,"Do you know something about this photograph? Email us!",2020-05-02
```

### Repeatable Fields in Input

- If the input CSV contains a column named (case-insensitive) `subject`, `subjects`, or `keywords`, its contents are treated as individual semicolon-delimited values for the repeatable field `subject[n]`.
- If the input CSV contains columns named `subject[0]`, `subject[1]`, etc., those are used directly.
- The same logic applies for other repeatable fields (e.g., `collection`, `collection[0]`, etc.).

---

## Output CSV File Format

The output CSV will contain:

- All original columns from the input CSV, except for control fields and non-indexed repeatable fields (e.g., `subject`, `keywords`, `subjects`, `collection`).
- Any fields from the template not present in the input (except control fields).
- Repeatable fields expanded into indexed columns (e.g., `subject[0]`, `subject[1]`), with template values first, then deduplicated input values.
- Columns ordered as follows:
  1. `identifier`
  2. `file`
  3. `mediatype`
  4. All `collection[n]` columns (in order)
  5. `title`
  6. `date`
  7. `creator`
  8. `description`
  9. All `subject[n]` columns (in order)
  10. Any other columns (in no particular order)

Example output:

```csv
identifier,file,mediatype,collection[0],collection[1],title,date,creator,description,subject[0],subject[1],subject[2],rights,notes,rights-statement,inclusive-description-statement
born-digital_middmag_finals-week_2011,a10_middmag_finals-week_2011.mp4,movies,middleburycollege,specialcollection,"Finals Week",2011,"Middlebury College","Description here","Baseball","Team photos","Athletes",...,...,http://rightsstatements.org/vocab/CNE/1.0/,"This collection aims to represent diverse communities and experiences."
```

---

## Best Practices

- **Validate your template and input CSV before running the script.**
- Use clear, consistent field names in your template and CSV.
- For repeatable fields, use lists in the template to ensure proper expansion.
- For uncertain dates, use 'x' in place of unknown digits (e.g., `19xx`).
- Always use supported flags and check error messages for guidance.
- Keep your codebase modular for easier maintenance and extension.

---

## Potential Issues & Common Mistakes

- **Control fields in output:** Control fields (e.g., `identifier-date`, `identifier-prefix`) should never appear in output CSVs. If they do, update your codebase to exclude them.
- **Identifier not generated correctly:** Ensure your template uses either `identifier-prefix` or `identifier_prefix`, and your code supports both.
- **Invalid date formats:** Dates must be in `YYYY`, `YYYY-MM`, or `YYYY-MM-DD` format, with 'x' allowed for uncertainty (e.g., `19xx`).
- **Invalid license or rights statement:** Only current Creative Commons licenses and rightsstatements.org statements are accepted.
- **File not found:** If the input CSV or template file does not exist, the script will exit with an error.
- **Output directory does not exist:** The script will create the output directory if needed.
- **Invalid flags:** If an unsupported flag is provided, the script will exit with an error and display allowed flags.
- **Repeatable fields not expanded:** Ensure repeatable fields are lists in the template.
- **Duplicate values in repeatable fields:** The script automatically deduplicates values for each repeatable field per row.

---

## Developer Guide

### Codebase Structure

- `ia-templatizer.py`: Main CLI script. Handles argument parsing, template and CSV loading, main processing loop, and output writing.
- `codebase/template.py`: Functions for loading and validating template files.
- `codebase/csvutils.py`: Functions for loading and writing CSV files, including whitespace normalization and deduplication utilities.
- `codebase/identifier.py`: Identifier generation logic. Handles control fields, uniqueness, and formatting.
- `codebase/fields.py`: Utility functions for repeatable fields, mediatype detection, and field normalization.
- `codebase/expand_directories.py`: Handles directory expansion logic and writing expanded output sheets.

### Adding New Functionality

- **Add new control fields:**  
  - Update the `control_fields` set in both `ia-templatizer.py` and `expand_directories.py`.
  - Implement logic for the new control field in the relevant module (e.g., identifier generation, field expansion).
  - Ensure new control fields are excluded from output CSVs unless explicitly required.

- **Add new validation rules:**  
  - Implement validation logic in `fields.py` or a new module.
  - Call validation functions from the main script as needed.

- **Add new repeatable fields:**  
  - Add the field to your template as a list.
  - Ensure `get_repeatable_fields` in `fields.py` recognizes it.
  - The main script will automatically expand it into indexed columns.

- **Change output column order:**  
  - Update the output column logic in `ia-templatizer.py` and `expand_directories.py`.

- **Integrate with other tools:**  
  - Add new modules to the `codebase/` directory.
  - Import and use them in the main script as needed.

### Best Practices for Developers

- Keep logic for control fields centralized and consistent.
- Always exclude control fields from output unless explicitly required.
- Use modular functions for validation, identifier generation, and field expansion.
- Document new features and changes in this README and in code comments.
- Test with a variety of templates and input CSVs to ensure robust behavior.

---

## Example Workflow

1. Prepare your template JSON and input CSV.
2. Run the script:

   ```bash
   python ia-templatizer.py --expand-directories templates/sample-template_01.json tests/sample-files-listing.csv tests/list-out.csv
   ```

3. Review the output CSV and any expanded directory sheets for completeness and accuracy.
4. Use the output CSV with Internet Archive CLI tools or other metadata workflows.

---

## Troubleshooting

- **Script fails to run:** Check that all dependencies are installed and the `codebase/` directory is present.
- **Unexpected output:** Verify your template and input CSV for correct field names and formats.
- **Validation errors:** Read the error message for details on which field or value is invalid.
- **Invalid flag error:** Ensure you are only using supported flags (`--expand-directories`, `-E`).
- **Control fields in output:** Update your codebase to exclude control fields from output rows and headers.

---

## Contact & Support

If you have questions about using IA Templatizer for your archival project, or need help with advanced configuration, please submit an issue to the project repository.

---

## Further Customization

IA Templatizer is designed to be modular and extensible. You can add new modules to the `codebase/` directory to support additional metadata standards, custom validation, or integration with other archival tools.

---

## Dependencies

IA Templatizer is written in Python 3 and relies only on standard Python libraries for its core functionality.  
To run the script successfully, you must have:

- **Python 3.7 or newer** installed on your system.
- The following standard Python modules (included with Python):
  - `os`
  - `sys`
  - `csv`
  - `re`
  - `json`
  - `warnings`
  - `time`

No third-party packages are required for basic operation.

### Optional: Development & Testing

For code editing, testing, and debugging, you may find these tools helpful:

- **Visual Studio Code** or another Python-aware IDE
- **pytest** (for unit testing, if you wish to add tests)
- **Git** (for version control)

### Installation

To check your Python version:

```bash
python3 --version
```

If you need to install Python, visit [python.org/downloads](https://www.python.org/downloads/).

---

**Note:**  
If you add new modules or features that require third-party packages, update this section to list those dependencies and provide installation instructions (e.g., using `pip install <package>`).
