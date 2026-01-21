import json

# Load generated component
with open('phase2_activated.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print("PHASE 2 ACTIVATION VERIFICATION")
print("=" * 80)
print()

# Check basic success
has_code = 'code' in data and len(data.get('code', '')) > 100
has_tests = 'tests' in data and len(data.get('tests', '')) > 100
has_docs = 'documentation' in data and len(data.get('documentation', '')) > 1000

print(f"✅ Code generated: {has_code}" if has_code else f"❌ Code generated: {has_code}")
print(f"✅ Tests generated: {has_tests}" if has_tests else f"❌ Tests generated: {has_tests}")
print(f"✅ Docs generated: {has_docs}" if has_docs else f"❌ Docs generated: {has_docs}")
print()

if has_tests:
    tests = data.get('tests', '')

    # Check for Phase 2 test features
    print("=== Phase 2 TEST Enhancements ===")
    features = {
        '✓ XCom fixture (_xcom_storage)': '_xcom_storage' in tests,
        '✓ XCom push test': 'test_xcom_push' in tests,
        '✓ XCom pull test': 'test_xcom_pull' in tests,
        '✓ Template rendering test': 'test_template_rendering' in tests,
        '✓ Edge case: none values': 'test_edge_case_none_values' in tests,
        '✓ Edge case: empty context': 'test_edge_case_empty_context' in tests,
    }

    phase2_test_features = sum(features.values())
    for feature, present in features.items():
        symbol = "✅" if present else "❌"
        print(f"{symbol} {feature}: {present}")

    print()

if has_docs:
    docs = data.get('documentation', '')

    # Check for Phase 2 documentation features
    print("=== Phase 2 DOCUMENTATION Enhancements ===")
    doc_features = {
        '✓ Troubleshooting section': 'Troubleshooting' in docs,
        '✓ Performance Considerations': 'Performance Considerations' in docs,
        '✓ Security Best Practices': 'Security Best Practices' in docs,
        '✓ XCom troubleshooting': 'XCom Push/Pull Issues' in docs,
        '✓ Advanced Debugging': 'Advanced Debugging Techniques' in docs,
    }

    phase2_doc_features = sum(doc_features.values())
    for feature, present in doc_features.items():
        symbol = "✅" if present else "❌"
        print(f"{symbol} {feature}: {present}")

    print()
    print(f"Documentation size: {len(docs):,} characters")
    print()

print("=" * 80)
if has_code and has_tests and has_docs:
    phase2_active = phase2_test_features >= 4 and phase2_doc_features >= 3

    if phase2_active:
        print("🎉🎉🎉 PHASE 2 IS FULLY ACTIVE! 🎉🎉🎉")
        print()
        print(f"Phase 2 Test Features: {phase2_test_features}/6")
        print(f"Phase 2 Doc Features: {phase2_doc_features}/5")
    else:
        print("⚠️  Phase 2 partially active - some features missing")
else:
    print("❌ Generation failed - check phase2_activated.json for errors")

print("=" * 80)
