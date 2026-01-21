#!/usr/bin/env python3
"""
Index Successful Component into RAG Database

This script indexes the NVIDIA NeMo QA Operator into the RAG database
for future pattern retrieval.

Usage:
    python scripts/index_successful_component.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def index_nemo_component():
    """Index the NeMo component into RAG database"""

    print("=" * 80)
    print("Indexing NVIDIA NeMo QA Operator into RAG Database")
    print("=" * 80)
    print()

    # Define paths
    base_path = Path(__file__).parent.parent
    component_path = base_path / "examples/successful_components/nemo_question_answering"

    # Load metadata
    print("📖 Loading component metadata...")
    metadata_path = component_path / "metadata.json"
    if not metadata_path.exists():
        print(f"❌ Metadata file not found: {metadata_path}")
        return False

    with open(metadata_path) as f:
        metadata = json.load(f)
    print(f"✅ Loaded metadata for {metadata['component_name']}")

    # Load operator code
    print("📖 Loading operator code...")
    operator_path = component_path / "nemo_question_answering_operator.py"
    if not operator_path.exists():
        print(f"❌ Operator file not found: {operator_path}")
        return False

    with open(operator_path) as f:
        operator_code = f.read()
    print(f"✅ Loaded operator code ({len(operator_code)} bytes)")

    # Load test code
    print("📖 Loading test code...")
    test_path = component_path / "test_nemo_question_answering_operator.py"
    test_code = ""
    if test_path.exists():
        with open(test_path) as f:
            test_code = f.read()
        print(f"✅ Loaded test code ({len(test_code)} bytes)")

    # Load DAG code
    print("📖 Loading DAG code...")
    dag_path = component_path / "test_nemo_qa_operator.py"
    dag_code = ""
    if dag_path.exists():
        with open(dag_path) as f:
            dag_code = f.read()
        print(f"✅ Loaded DAG code ({len(dag_code)} bytes)")

    # Create RAG entry
    print("\n🔨 Creating RAG entry...")
    rag_entry = {
        "id": f"nemo_qa_operator_success_{datetime.now().strftime('%Y_%m_%d')}",
        "component_name": metadata["component_name"],
        "category": metadata["category"],
        "subcategory": metadata["subcategory"],
        "framework": metadata["framework"],
        "component_type": metadata["component_type"],
        "operator_code": operator_code,
        "test_code": test_code,
        "dag_code": dag_code,
        "metadata": metadata,
        "embedding_text": generate_embedding_text(metadata, operator_code),
        "success_score": calculate_success_score(metadata),
        "relevance_keywords": metadata["rag_indexing"]["similarity_keywords"],
        "pattern_type": metadata["rag_indexing"]["pattern_category"],
        "indexed_at": datetime.now().isoformat(),
        "code_patterns": extract_code_patterns(operator_code),
    }

    print(f"✅ Created RAG entry with success score: {rag_entry['success_score']}")

    # Store in RAG database
    print("\n💾 Storing in RAG database...")
    success = store_in_rag(rag_entry)

    if success:
        print("\n" + "=" * 80)
        print("✅ SUCCESS: Component indexed successfully!")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  Component: {metadata['component_name']}")
        print(f"  Category: {metadata['category']} / {metadata['subcategory']}")
        print(f"  Success Score: {rag_entry['success_score']}")
        print(f"  Pattern Type: {rag_entry['pattern_type']}")
        print(f"  Keywords: {len(rag_entry['relevance_keywords'])} keywords")
        print()
    else:
        print("\n❌ Failed to index component")
        return False

    return True


def generate_embedding_text(metadata: dict, code: str) -> str:
    """Generate rich text for embeddings"""
    text_parts = [
        # Component identity
        f"Component: {metadata['component_name']}",
        f"Type: {metadata['component_type']}",
        f"Category: {metadata['category']} / {metadata['subcategory']}",
        f"Framework: {metadata['framework']}",

        # Searchable description
        metadata["rag_indexing"]["searchable_text"],

        # Features
        "Features:",
        " | ".join(f"{k.replace('_', ' ')}" for k, v in metadata['component_features'].items() if v),

        # Success factors
        "Success Factors:",
        " | ".join(metadata['success_factors']),

        # Inputs
        "Inputs:",
        " | ".join(inp['name'] for inp in metadata.get('inputs', [])),

        # Runtime parameters
        "Runtime Parameters:",
        " | ".join(rp['name'] for rp in metadata.get('runtime_params', [])),

        # Code preview (first 1000 chars for context)
        "Code Preview:",
        code[:1000]
    ]

    return "\n".join(text_parts)


def calculate_success_score(metadata: dict) -> int:
    """Calculate success score based on metrics"""
    score = 100

    # First attempt success: +20
    if metadata["generation_metrics"]["attempts"] == 1:
        score += 20
        print("  ✅ First-attempt success: +20")

    # Zero errors: +15
    validation = metadata["validation_results"]
    if (validation["syntax_errors"] == 0 and
        validation["import_errors"] == 0 and
        validation["security_issues"] == 0):
        score += 15
        print("  ✅ Zero validation errors: +15")

    # Production tested: +10
    if metadata["testing_results"]["dag_appeared_in_ui"]:
        score += 10
        print("  ✅ Production tested: +10")

    # Runtime parameters: +5
    if metadata["component_features"]["runtime_parameters"]:
        score += 5
        print("  ✅ Runtime parameters: +5")

    # Airflow 3.x compatible: +5
    if metadata["component_features"]["airflow_3x_compatible"]:
        score += 5
        print("  ✅ Airflow 3.x compatible: +5")

    # Mock execution: +5
    if metadata["component_features"]["mock_execution"]:
        score += 5
        print("  ✅ Mock execution mode: +5")

    # Low cost (< $0.10): +5
    if metadata["generation_metrics"]["cost_usd"] < 0.10:
        score += 5
        print("  ✅ Low cost generation: +5")

    return min(score, 165)  # Max 165


def extract_code_patterns(code: str) -> dict:
    """Extract key code patterns for reference"""
    patterns = {}

    # Extract __init__ method
    if "def __init__" in code:
        init_start = code.find("def __init__")
        init_end = code.find("\n    def ", init_start + 1)
        if init_end == -1:
            init_end = min(init_start + 2000, len(code))
        patterns["__init__"] = code[init_start:init_end].strip()

    # Extract execute method
    if "def execute" in code:
        exec_start = code.find("def execute")
        exec_end = code.find("\n    def ", exec_start + 1)
        if exec_end == -1:
            exec_end = min(exec_start + 3000, len(code))
        patterns["execute"] = code[exec_start:exec_end].strip()

    # Extract imports
    import_lines = [line for line in code.split('\n') if line.strip().startswith(('import ', 'from '))]
    patterns["imports"] = '\n'.join(import_lines[:20])  # First 20 imports

    # Extract class definition
    if "class " in code:
        class_start = code.find("class ")
        class_end = code.find(":", class_start)
        patterns["class_definition"] = code[class_start:class_end + 1].strip()

    # Extract template_fields
    if "template_fields" in code:
        tf_start = code.find("template_fields")
        tf_end = code.find("\n", tf_start)
        patterns["template_fields"] = code[tf_start:tf_end].strip()

    return patterns


def store_in_rag(entry: dict) -> bool:
    """Store entry in RAG database"""
    try:
        # Create data directory if it doesn't exist
        base_path = Path(__file__).parent.parent
        rag_db_path = base_path / "data/rag_success_patterns.json"
        rag_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing database
        if rag_db_path.exists():
            with open(rag_db_path) as f:
                db = json.load(f)
            print(f"  📂 Loaded existing database with {len(db.get('patterns', []))} patterns")
        else:
            db = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "patterns": []
            }
            print("  📂 Creating new RAG database")

        # Check for duplicates
        existing_ids = {p["id"] for p in db["patterns"]}
        if entry["id"] in existing_ids:
            print(f"  ⚠️  Updating existing entry: {entry['id']}")
            db["patterns"] = [p for p in db["patterns"] if p["id"] != entry["id"]]

        # Add new entry
        db["patterns"].append(entry)
        db["updated_at"] = datetime.now().isoformat()

        # Save to file
        with open(rag_db_path, 'w') as f:
            json.dump(db, f, indent=2)

        print(f"  ✅ Saved to: {rag_db_path}")
        print(f"  📊 Total patterns in database: {len(db['patterns'])}")

        return True

    except Exception as e:
        print(f"  ❌ Error storing in RAG database: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    success = index_nemo_component()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
