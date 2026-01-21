import json

# Load the generated component
with open('phase2_sample_test.json', 'r') as f:
    data = json.load(f)

print('=== PHASE 2 ACTIVATION CHECK ===')
print()
print('Generation Success:', data.get('success', False))
print()

if data.get('success'):
    # Check test features
    tests = data.get('tests', '')
    print('=== Test Features (Phase 2) ===')
    print('✓ XCom fixture (_xcom_storage):' if '_xcom_storage' in tests else '✗ XCom fixture (_xcom_storage):', '_xcom_storage' in tests)
    print('✓ test_xcom_push:' if 'test_xcom_push' in tests else '✗ test_xcom_push:', 'test_xcom_push' in tests)
    print('✓ test_xcom_pull:' if 'test_xcom_pull' in tests else '✗ test_xcom_pull:', 'test_xcom_pull' in tests)
    print('✓ test_template_rendering:' if 'test_template_rendering' in tests else '✗ test_template_rendering:', 'test_template_rendering' in tests)
    print('✓ test_edge_case_none_values:' if 'test_edge_case_none_values' in tests else '✗ test_edge_case_none_values:', 'test_edge_case_none_values' in tests)
    print('✓ test_edge_case_empty_context:' if 'test_edge_case_empty_context' in tests else '✗ test_edge_case_empty_context:', 'test_edge_case_empty_context' in tests)

    # Check documentation features
    doc = data.get('documentation', '')
    print()
    print('=== Documentation Features (Phase 2) ===')
    print(f'Documentation size: {len(doc):,} characters')
    print('✓ Troubleshooting section:' if 'Troubleshooting' in doc else '✗ Troubleshooting section:', 'Troubleshooting' in doc)
    print('✓ Performance Considerations:' if 'Performance Considerations' in doc else '✗ Performance Considerations:', 'Performance Considerations' in doc)
    print('✓ Security Best Practices:' if 'Security Best Practices' in doc else '✗ Security Best Practices:', 'Security Best Practices' in doc)
    print('✓ XCom troubleshooting:' if 'XCom Push/Pull Issues' in doc else '✗ XCom troubleshooting:', 'XCom Push/Pull Issues' in doc)
    print('✓ Advanced Debugging:' if 'Advanced Debugging Techniques' in doc else '✗ Advanced Debugging:', 'Advanced Debugging Techniques' in doc)

    print()
    has_phase2_tests = all([
        '_xcom_storage' in tests,
        'test_xcom_push' in tests,
        'test_template_rendering' in tests,
        'test_edge_case_none_values' in tests
    ])

    has_phase2_docs = all([
        'Troubleshooting' in doc,
        'Performance Considerations' in doc,
        'Security Best Practices' in doc,
        len(doc) > 15000
    ])

    if has_phase2_tests and has_phase2_docs:
        print('🎉 PHASE 2 IS ACTIVE! All enhancements are working!')
    else:
        print('⚠️  Phase 2 NOT active - service needs restart/rebuild')
        print('   Code exists in files but not loaded in running service')
        print('   See PHASE2_ACTIVATION_GUIDE.md for activation steps')
else:
    print('Error:', data.get('detail', data.get('error', 'Unknown error')))
