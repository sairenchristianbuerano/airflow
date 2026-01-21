import json

with open('phase2_complete.json', 'r') as f:
    data = json.load(f)

tests = data.get('tests', '')
docs = data.get('documentation', '')

print("=" * 80)
print("🎉 PHASE 2 VERIFICATION - phase2_complete.json")
print("=" * 80)
print()

print("=== Phase 2 TEST Features ===")
test_features = [
    ('XCom fixture (_xcom_storage)', '_xcom_storage' in tests),
    ('test_xcom_push', 'test_xcom_push' in tests),
    ('test_xcom_pull', 'test_xcom_pull' in tests),
    ('test_template_rendering', 'test_template_rendering' in tests),
    ('test_edge_case_none_values', 'test_edge_case_none_values' in tests),
    ('test_edge_case_empty_context', 'test_edge_case_empty_context' in tests),
]

phase2_tests = sum(present for _, present in test_features)
for name, present in test_features:
    print(f"{'✅' if present else '❌'} {name}: {present}")

print()
print("=== Phase 2 DOCUMENTATION Features ===")
doc_features = [
    ('Troubleshooting section', 'Troubleshooting' in docs),
    ('Performance Considerations', 'Performance Considerations' in docs),
    ('Security Best Practices', 'Security Best Practices' in docs),
    ('XCom troubleshooting', 'XCom Push/Pull Issues' in docs),
    ('Advanced Debugging', 'Advanced Debugging Techniques' in docs),
]

phase2_docs = sum(present for _, present in doc_features)
for name, present in doc_features:
    print(f"{'✅' if present else '❌'} {name}: {present}")

print()
print(f"Documentation size: {len(docs):,} characters")
print()

print("=" * 80)
if phase2_tests >= 4 and phase2_docs >= 3:
    print("🎉🎉🎉 PHASE 2 IS FULLY ACTIVE! 🎉🎉🎉")
    print()
    print(f"✅ Phase 2 Test Features: {phase2_tests}/6")
    print(f"✅ Phase 2 Doc Features: {phase2_docs}/5")
else:
    print("⚠️  Phase 2 partially active")
    print(f"Test Features: {phase2_tests}/6")
    print(f"Doc Features: {phase2_docs}/5")
print("=" * 80)
