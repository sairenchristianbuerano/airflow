#!/usr/bin/env python3
"""
Quick verification script for the NeMo Question Answering Operator

Run this script to verify the operator is correctly set up.
"""

import sys
import os

# Add custom_operators to path
sys.path.insert(0, os.path.dirname(__file__))

def verify_operator():
    """Verify operator installation and basic functionality"""

    print("=" * 80)
    print("🔍 NeMo Question Answering Operator - Verification Script")
    print("=" * 80)
    print()

    # Test 1: Import operator
    print("Test 1: Importing operator...")
    try:
        from custom_operators import NeMoQuestionAnsweringOperator
        print("✅ Import successful!")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\nMake sure custom_operators/ directory exists with:")
        print("  - nemo_question_answering_operator.py")
        print("  - __init__.py")
        return False

    # Test 2: Create operator instance
    print("\nTest 2: Creating operator instance...")
    try:
        operator = NeMoQuestionAnsweringOperator(
            task_id='test_task',
            mode='inference',
            model_type='extractive',
            pretrained_model_name='bert-base-uncased',
        )
        print("✅ Operator instance created successfully!")
    except Exception as e:
        print(f"❌ Failed to create operator: {e}")
        return False

    # Test 3: Check operator attributes
    print("\nTest 3: Checking operator attributes...")
    try:
        assert operator.task_id == 'test_task'
        assert operator.mode == 'inference'
        assert operator.model_type == 'extractive'
        assert hasattr(operator, 'execute')
        assert hasattr(operator, 'template_fields')
        print("✅ All operator attributes present!")
        print(f"   - Task ID: {operator.task_id}")
        print(f"   - Mode: {operator.mode}")
        print(f"   - Model Type: {operator.model_type}")
        print(f"   - Template Fields: {operator.template_fields}")
    except (AssertionError, AttributeError) as e:
        print(f"❌ Attribute check failed: {e}")
        return False

    # Test 4: Check test file
    print("\nTest 4: Checking test file...")
    test_file = os.path.join(
        os.path.dirname(__file__),
        'custom_operators',
        'test_nemo_question_answering_operator.py'
    )
    if os.path.exists(test_file):
        print(f"✅ Test file found: {test_file}")
        print(f"   Size: {os.path.getsize(test_file):,} bytes")
    else:
        print(f"⚠️  Test file not found: {test_file}")

    # Test 5: Check test DAG
    print("\nTest 5: Checking test DAG...")
    dag_file = os.path.join(
        os.path.dirname(__file__),
        'dags',
        'test_nemo_qa_operator.py'
    )
    if os.path.exists(dag_file):
        print(f"✅ Test DAG found: {dag_file}")
        print(f"   Size: {os.path.getsize(dag_file):,} bytes")

        # Try to import the DAG
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("test_dag", dag_file)
            dag_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dag_module)
            print("✅ Test DAG imports successfully!")
        except Exception as e:
            print(f"⚠️  Test DAG import warning: {e}")
    else:
        print(f"⚠️  Test DAG not found: {dag_file}")

    print()
    print("=" * 80)
    print("✅ VERIFICATION COMPLETE!")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Install Airflow (if not already installed):")
    print("   pip install apache-airflow")
    print()
    print("2. Copy files to Airflow DAGs folder:")
    print("   cp -r custom_operators $AIRFLOW_HOME/dags/")
    print("   cp dags/test_nemo_qa_operator.py $AIRFLOW_HOME/dags/")
    print()
    print("3. Start Airflow and access UI:")
    print("   airflow webserver --port 8080")
    print("   airflow scheduler")
    print()
    print("4. See AIRFLOW_SETUP.md for detailed installation instructions")
    print()

    return True


if __name__ == "__main__":
    success = verify_operator()
    sys.exit(0 if success else 1)
