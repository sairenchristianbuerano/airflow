import ast
import sys

# Parse the airflow_validator.py file
with open('component-generator/src/airflow_validator.py', 'r') as f:
    code = f.read()

tree = ast.parse(code)

# Find the AirflowComponentValidator class
classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AirflowComponentValidator']

if not classes:
    print("ERROR: AirflowComponentValidator class not found!")
    sys.exit(1)

cls = classes[0]
methods = [m.name for m in cls.body if isinstance(m, ast.FunctionDef)]

print(f"Found AirflowComponentValidator class with {len(methods)} methods")
print()
print("Methods:")
for m in methods:
    print(f"  - {m}")

print()
print(f"Has _run_static_analysis: {' _run_static_analysis' in methods}")
print(f"Has _validate_with_mypy: {'_validate_with_mypy' in methods}")
print(f"Has _validate_with_ruff: {'_validate_with_ruff' in methods}")

# Check where the class ends
class_start = cls.lineno
class_end = cls.end_lineno
print()
print(f"Class definition: lines {class_start} to {class_end}")

# Check if line 525 is within the class
print(f"Line 525 (where _run_static_analysis should be) is {'INSIDE' if 525 >= class_start and 525 <= class_end else 'OUTSIDE'} the class")
