import sys
from ia_templatizer.template import load_template
from ia_templatizer.csvutils import load_csv, write_output_csv
from ia_templatizer.identifier import generate_identifier
from ia_templatizer.fields import get_repeatable_fields

def main():
    if len(sys.argv) != 4:
        print("Usage: python ia-templatizer.py <template_path> <csv_path> <output_path>")
        sys.exit(1)
    template_path = sys.argv[1]
    csv_path = sys.argv[2]
    output_path = sys.argv[3]

    template = load_template(template_path)
    csv_data = load_csv(csv_path)
    # ...apply template, generate identifiers, handle fields...
    # ...write output...

if __name__ == "__main__":
    main()