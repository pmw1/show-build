import sys
import os
import re
from lxml import etree

if len(sys.argv) < 2:
    print("Usage: python convert_vmix_drive.py <input_file.vmix>")
    sys.exit(1)

input_file = sys.argv[1]
if not os.path.isfile(input_file):
    print(f"File not found: {input_file}")
    sys.exit(1)

# Clean file (remove null bytes)
with open(input_file, "rb") as f:
    raw = f.read()
cleaned = raw.replace(b"\x00", b"")

# Parse using forgiving XML parser
parser = etree.XMLParser(recover=True, encoding='utf-8')
try:
    root = etree.fromstring(cleaned, parser=parser)
except etree.XMLSyntaxError as e:
    print(f"lxml failed to parse XML: {e}")
    sys.exit(1)

# Find all <Filename> elements and extract drive letters
paths = root.xpath("//Filename[starts-with(text(), substring(text(), 1, 2))]")
drive_counts = {}
for p in paths:
    if p.text and re.match(r"^[a-zA-Z]:\\", p.text):
        drive = p.text[0].upper()
        drive_counts[drive] = drive_counts.get(drive, 0) + 1

print("Found drive letters in <Filename> elements:")
for drive, count in drive_counts.items():
    print(f"  {drive}:\\ — {count} path(s)")

# Prompt user for drive replacement
new_drive = input("\nEnter new drive letter (e.g., E): ").strip().upper()
if not re.match(r"^[A-Z]$", new_drive):
    print("Invalid drive letter.")
    sys.exit(1)

# Replace drive letter
for p in paths:
    if p.text and re.match(r"^[a-zA-Z]:\\", p.text):
        old = p.text
        p.text = new_drive + old[1:]

# Write out safely
output_file = os.path.splitext(input_file)[0] + "_converted.vmix"
tree = etree.ElementTree(root)
tree.write(output_file, encoding="utf-8", xml_declaration=True, pretty_print=True)

print(f"\n✅ Converted file saved to: {output_file}")

