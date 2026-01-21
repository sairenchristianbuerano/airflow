#!/usr/bin/env python3
"""
Extract and Store Patterns - Phase 1 MVP Test

This script extracts patterns from the successful NeMo QA component
and stores them in the pattern database.

Usage:
    python scripts/extract_and_store_patterns.py
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pattern_extractor import PatternExtractor
from pattern_storage import PatternStorage


def main():
    print("=" * 80)
    print("PATTERN EXTRACTION & STORAGE - Phase 1 MVP")
    print("=" * 80)
    print()

    # Paths
    base_path = Path(__file__).parent.parent
    component_path = base_path / "examples/successful_components/nemo_question_answering"
    db_path = base_path / "data/patterns.db"

    # Initialize extractor and storage
    print("📦 Initializing pattern extractor and storage...")
    extractor = PatternExtractor()
    storage = PatternStorage(str(db_path))
    print(f"✅ Database created at: {db_path}")
    print()

    # Load component files
    print("📖 Loading NeMo QA Operator files...")

    # Load operator code
    operator_file = component_path / "nemo_question_answering_operator.py"
    if not operator_file.exists():
        print(f"❌ Operator file not found: {operator_file}")
        return 1

    with open(operator_file) as f:
        operator_code = f.read()
    print(f"✅ Loaded operator code ({len(operator_code)} bytes)")

    # Load metadata
    metadata_file = component_path / "metadata.json"
    if not metadata_file.exists():
        print(f"❌ Metadata file not found: {metadata_file}")
        return 1

    with open(metadata_file) as f:
        metadata = json.load(f)
    print(f"✅ Loaded metadata for {metadata['component_name']}")
    print()

    # Create spec from metadata
    spec = {
        "name": metadata["component_name"],
        "category": metadata["category"],
        "subcategory": metadata["subcategory"],
        "component_type": metadata["component_type"],
        "inputs": metadata.get("inputs", []),
        "runtime_params": metadata.get("runtime_params", [])
    }

    # Extract patterns
    print("🔍 Extracting patterns from successful component...")
    patterns = extractor.extract_patterns(operator_code, spec, metadata["generation_metrics"])

    # Print extracted patterns summary
    print()
    print("📊 EXTRACTED PATTERNS:")
    print("-" * 80)

    for pattern_type, pattern_data in patterns.items():
        if pattern_type == "metadata":
            continue

        if pattern_data:
            count = len(pattern_data) if isinstance(pattern_data, dict) else 1
            print(f"  ✅ {pattern_type:25s} → {count} pattern(s)")

    print()
    print("METADATA:")
    print(f"  • Category: {patterns['metadata']['category']}")
    print(f"  • Component Type: {patterns['metadata']['component_type']}")
    print(f"  • Complexity: {patterns['metadata']['complexity']}")
    print(f"  • Libraries Used: {', '.join(patterns['metadata']['libraries_used']) or 'None'}")
    print()

    # Store patterns
    print("💾 Storing patterns in database...")
    storage.store_component_patterns(
        component_name=metadata["component_name"],
        code=operator_code,
        patterns=patterns,
        metadata=metadata["generation_metrics"],
        success=True
    )
    print("✅ Patterns stored successfully!")
    print()

    # Get statistics
    print("📈 PATTERN DATABASE STATISTICS:")
    print("-" * 80)
    stats = storage.get_pattern_statistics()

    print(f"  • Total Patterns: {stats['total_patterns']}")
    print(f"  • Total Components: {stats['total_components']}")
    print(f"  • High Confidence Patterns (≥90%): {stats['high_confidence_patterns']}")
    print(f"  • Average Confidence: {stats['average_confidence']:.1%}")
    print()

    if stats["patterns_by_category"]:
        print("  Patterns by Category:")
        for category, count in stats["patterns_by_category"].items():
            print(f"    - {category}: {count} patterns")
    print()

    # Test retrieval
    print("🔎 TESTING PATTERN RETRIEVAL:")
    print("-" * 80)

    retrieved_patterns = storage.get_best_patterns(
        category="ml",
        component_type="operator",
        min_confidence=0.7,
        limit=5
    )

    print(f"  Retrieved {len(retrieved_patterns)} high-confidence patterns for ML operators:")
    for i, pattern in enumerate(retrieved_patterns, 1):
        print(f"\n  {i}. {pattern['pattern_type']} - {pattern['pattern_name']}")
        print(f"     Confidence: {pattern['confidence_score']:.1%}")
        print(f"     Success: {pattern['success_count']} | Failures: {pattern['failure_count']}")

    print()

    # Test similar components retrieval
    print("🔎 TESTING SIMILAR COMPONENTS RETRIEVAL:")
    print("-" * 80)

    similar = storage.get_similar_components(
        category="ml",
        subcategory="nlp",
        min_success_score=150,
        limit=3
    )

    print(f"  Retrieved {len(similar)} similar components:")
    for i, comp in enumerate(similar, 1):
        print(f"\n  {i}. {comp['component_name']}")
        print(f"     Category: {comp['category']} / {comp['subcategory']}")
        print(f"     Success Score: {comp['success_score']}")
        print(f"     Complexity: {comp['complexity_score']}")
        print(f"     Patterns: {len(comp['extracted_patterns'])} types")

    print()
    print("=" * 80)
    print("✅ PATTERN EXTRACTION & STORAGE COMPLETE!")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("  1. Patterns are now stored and ready for retrieval")
    print("  2. Future generations can use these patterns as references")
    print("  3. The system will learn and improve with each generation")
    print()
    print(f"Database Location: {db_path}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
