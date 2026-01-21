#!/usr/bin/env python3
"""
Test script to generate a component with runtime params
"""
import requests
import json

# Read the spec file
with open('test_weather_with_params.yaml', 'r') as f:
    spec_content = f.read()

# Make the API request
response = requests.post(
    'http://localhost:8095/api/airflow/component-generator/generate',
    json={'spec': spec_content},
    headers={'Content-Type': 'application/json'}
)

# Check response
if response.status_code == 200:
    result = response.json()

    # Save the generated files
    with open('generated_weather_operator.py', 'w') as f:
        f.write(result['code'])
    print("✅ Operator code saved to: generated_weather_operator.py")

    with open('generated_weather_test.py', 'w') as f:
        f.write(result['tests'])
    print("✅ Test code saved to: generated_weather_test.py")

    if 'test_dag' in result:
        with open('generated_weather_dag.py', 'w') as f:
            f.write(result['test_dag'])
        print("✅ Test DAG saved to: generated_weather_dag.py")
    else:
        print("⚠️ No test_dag in response (check service.py implementation)")

    with open('generated_weather_docs.md', 'w') as f:
        f.write(result['documentation'])
    print("✅ Documentation saved to: generated_weather_docs.md")

    print("\n🎉 Component generated successfully with runtime params support!")
    print("\nCheck the generated_weather_dag.py file to see the Params implementation.")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
