#!/usr/bin/env python3
"""Remove duplicate Phase 2 methods from airflow_validator.py"""

file_path = 'component-generator/src/airflow_validator.py'

# Read all lines
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 713-900 (Python uses 0-indexed, so 712:900)
# Lines 712 to 900 contain the duplicate methods
new_lines = lines[:712] + lines[900:]

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Removed {900-712} duplicate lines from {file_path}")
print(f"New file has {len(new_lines)} lines (was {len(lines)} lines)")
