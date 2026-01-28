#!/usr/bin/env python3
"""
Official Airflow Pattern Extractor

Extracts patterns from the official Apache Airflow repository to enhance
the component generator's RAG database. This script learns structural patterns,
not full implementations (respecting Apache License).

Usage:
    python extract_official_patterns.py --source /path/to/airflow/providers --output ../data/rag_success_patterns.json
"""

import os
import sys
import json
import ast
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import argparse


class AirflowPatternExtractor:
    """Extracts patterns from official Airflow provider components."""

    # High-value providers to extract patterns from
    PRIORITY_PROVIDERS = [
        'amazon',      # AWS - S3, SQS, Lambda, ECS
        'google',      # GCP - GCS, BigQuery, Dataflow
        'http',        # HTTP operator patterns
        'slack',       # Notification patterns
        'databricks',  # Data engineering
        'cncf',        # Kubernetes
        'postgres',    # Database patterns
        'mysql',       # Database patterns
        'mongo',       # NoSQL patterns
        'redis',       # Cache patterns
        'docker',      # Container patterns
        'ssh',         # Remote execution
        'sftp',        # File transfer
        'smtp',        # Email
    ]

    def __init__(self, source_path: str, verbose: bool = False):
        self.source_path = Path(source_path)
        self.verbose = verbose
        self.patterns = []
        self.stats = {
            'operators_scanned': 0,
            'sensors_scanned': 0,
            'hooks_scanned': 0,
            'patterns_extracted': 0,
            'providers_processed': 0
        }

    def extract_all(self) -> List[Dict[str, Any]]:
        """Extract patterns from all priority providers."""
        print(f"Scanning providers in: {self.source_path}")

        for provider in self.PRIORITY_PROVIDERS:
            provider_path = self.source_path / provider
            if provider_path.exists():
                self._extract_from_provider(provider, provider_path)
                self.stats['providers_processed'] += 1
            else:
                if self.verbose:
                    print(f"  Provider not found: {provider}")

        print(f"\nExtraction complete:")
        print(f"  Providers processed: {self.stats['providers_processed']}")
        print(f"  Operators scanned: {self.stats['operators_scanned']}")
        print(f"  Sensors scanned: {self.stats['sensors_scanned']}")
        print(f"  Hooks scanned: {self.stats['hooks_scanned']}")
        print(f"  Patterns extracted: {self.stats['patterns_extracted']}")

        return self.patterns

    def _extract_from_provider(self, provider_name: str, provider_path: Path):
        """Extract patterns from a single provider."""
        print(f"\nProcessing provider: {provider_name}")

        # Find source directories (handle different provider structures)
        src_paths = list(provider_path.glob('**/src/airflow/providers/**'))
        if not src_paths:
            src_paths = [provider_path]

        for src_path in src_paths:
            # Extract operators
            for op_file in src_path.glob('**/operators/*.py'):
                if op_file.name.startswith('__'):
                    continue
                self._extract_from_file(op_file, 'operator', provider_name)
                self.stats['operators_scanned'] += 1

            # Extract sensors
            for sensor_file in src_path.glob('**/sensors/*.py'):
                if sensor_file.name.startswith('__'):
                    continue
                self._extract_from_file(sensor_file, 'sensor', provider_name)
                self.stats['sensors_scanned'] += 1

            # Extract hooks
            for hook_file in src_path.glob('**/hooks/*.py'):
                if hook_file.name.startswith('__'):
                    continue
                self._extract_from_file(hook_file, 'hook', provider_name)
                self.stats['hooks_scanned'] += 1

    def _extract_from_file(self, file_path: Path, component_type: str, provider_name: str):
        """Extract patterns from a single Python file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    pattern = self._extract_class_pattern(node, content, component_type, provider_name, file_path)
                    if pattern:
                        self.patterns.append(pattern)
                        self.stats['patterns_extracted'] += 1
                        if self.verbose:
                            print(f"    Extracted: {pattern['component_name']}")

        except SyntaxError as e:
            if self.verbose:
                print(f"    Syntax error in {file_path}: {e}")
        except Exception as e:
            if self.verbose:
                print(f"    Error processing {file_path}: {e}")

    def _extract_class_pattern(self, node: ast.ClassDef, content: str,
                                component_type: str, provider_name: str,
                                file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract pattern from a class definition."""
        class_name = node.name

        # Skip base classes, test classes, and private classes
        if class_name.startswith('_'):
            return None
        if 'Base' in class_name and class_name.endswith('Base'):
            return None
        if 'Mixin' in class_name:
            return None

        # Check if it's a valid Airflow component
        base_classes = [self._get_base_name(base) for base in node.bases]

        is_operator = any('Operator' in b or 'BaseOperator' in b for b in base_classes)
        is_sensor = any('Sensor' in b or 'BaseSensor' in b for b in base_classes)
        is_hook = any('Hook' in b or 'BaseHook' in b for b in base_classes)

        if not (is_operator or is_sensor or is_hook):
            return None

        # Determine actual component type from inheritance
        if is_sensor:
            component_type = 'sensor'
        elif is_hook:
            component_type = 'hook'
        elif is_operator:
            component_type = 'operator'

        # Extract docstring
        docstring = ast.get_docstring(node) or ""

        # Extract template_fields
        template_fields = self._extract_template_fields(node, content)

        # Extract __init__ parameters
        init_params = self._extract_init_params(node)

        # Extract key code patterns
        code_patterns = self._extract_code_patterns(node, content, component_type)

        # Determine category and subcategory
        category, subcategory = self._determine_category(provider_name, class_name, file_path)

        # Build pattern entry
        pattern = {
            'id': f"official_{class_name.lower()}_{datetime.now().strftime('%Y%m%d')}",
            'component_name': class_name,
            'category': category,
            'subcategory': subcategory,
            'provider': provider_name,
            'component_type': component_type,
            'source': 'apache-airflow-official',
            'metadata': {
                'component_name': class_name,
                'component_type': component_type,
                'category': category,
                'provider': provider_name,
                'base_classes': base_classes,
                'template_fields': template_fields,
                'has_deferrable': 'deferrable' in content.lower(),
                'has_trigger': 'trigger' in content.lower() and 'Trigger' in content,
                'airflow_3x_compatible': 'from __future__ import annotations' in content,
            },
            'inputs': init_params,
            'success_factors': self._generate_success_factors(class_name, component_type, base_classes, code_patterns),
            'code_patterns': code_patterns,
            'docstring_summary': docstring[:500] if docstring else "",
            'success_score': self._calculate_score(code_patterns, template_fields, docstring),
            'pattern_type': f"official_{category}_{component_type}",
            'indexed_at': datetime.now().isoformat(),
            'relevance_keywords': self._generate_keywords(class_name, category, provider_name, component_type)
        }

        return pattern

    def _get_base_name(self, base) -> str:
        """Get the name of a base class."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        elif isinstance(base, ast.Subscript):
            return self._get_base_name(base.value)
        return str(base)

    def _extract_template_fields(self, node: ast.ClassDef, content: str) -> List[str]:
        """Extract template_fields from class."""
        template_fields = []

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                if item.target.id == 'template_fields':
                    if isinstance(item.value, (ast.Tuple, ast.List)):
                        for elt in item.value.elts:
                            if isinstance(elt, ast.Constant):
                                template_fields.append(elt.value)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == 'template_fields':
                        if isinstance(item.value, (ast.Tuple, ast.List)):
                            for elt in item.value.elts:
                                if isinstance(elt, ast.Constant):
                                    template_fields.append(elt.value)

        return template_fields

    def _extract_init_params(self, node: ast.ClassDef) -> List[Dict[str, Any]]:
        """Extract __init__ parameters."""
        params = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                for i, arg in enumerate(item.args.args):
                    if arg.arg in ('self', 'kwargs'):
                        continue

                    param = {
                        'name': arg.arg,
                        'type': self._get_annotation_type(arg.annotation) if arg.annotation else 'Any',
                        'required': True
                    }

                    # Check for default value
                    defaults_offset = len(item.args.args) - len(item.args.defaults)
                    if i >= defaults_offset:
                        default_idx = i - defaults_offset
                        if default_idx < len(item.args.defaults):
                            default = item.args.defaults[default_idx]
                            param['required'] = False
                            param['default'] = self._get_default_value(default)

                    params.append(param)

                # Handle keyword-only args
                for i, arg in enumerate(item.args.kwonlyargs):
                    if arg.arg == 'kwargs':
                        continue

                    param = {
                        'name': arg.arg,
                        'type': self._get_annotation_type(arg.annotation) if arg.annotation else 'Any',
                        'required': False
                    }

                    if i < len(item.args.kw_defaults) and item.args.kw_defaults[i]:
                        param['default'] = self._get_default_value(item.args.kw_defaults[i])

                    params.append(param)

                break

        return params[:15]  # Limit to first 15 params

    def _get_annotation_type(self, annotation) -> str:
        """Get type annotation as string."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            return f"{self._get_annotation_type(annotation.value)}[...]"
        elif isinstance(annotation, ast.BinOp):
            return "Union"
        return "Any"

    def _get_default_value(self, default) -> Any:
        """Get default value from AST node."""
        if isinstance(default, ast.Constant):
            return default.value
        elif isinstance(default, ast.Name):
            if default.id == 'None':
                return None
            elif default.id == 'True':
                return True
            elif default.id == 'False':
                return False
            return f"<{default.id}>"
        elif isinstance(default, (ast.List, ast.Tuple)):
            return []
        elif isinstance(default, ast.Dict):
            return {}
        return "<computed>"

    def _extract_code_patterns(self, node: ast.ClassDef, content: str, component_type: str) -> Dict[str, Any]:
        """Extract key code patterns from the class."""
        patterns = {}

        # Extract imports pattern (first 10 lines of imports)
        import_lines = []
        for line in content.split('\n')[:30]:
            if line.startswith('from ') or line.startswith('import '):
                import_lines.append(line)
        if import_lines:
            patterns['imports'] = '\n'.join(import_lines[:10])

        # Extract class attributes
        class_attrs = []
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                class_attrs.append(item.target.id)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_attrs.append(target.id)
        patterns['class_attributes'] = class_attrs[:10]

        # Extract method names
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
        patterns['methods'] = methods

        # Component-specific patterns
        if component_type == 'sensor':
            patterns['has_poke'] = 'poke' in methods
            patterns['has_execute_complete'] = 'execute_complete' in methods
        elif component_type == 'hook':
            patterns['has_get_conn'] = 'get_conn' in methods
            patterns['has_close'] = 'close' in methods
        elif component_type == 'operator':
            patterns['has_execute'] = 'execute' in methods
            patterns['has_execute_complete'] = 'execute_complete' in methods

        # Check for advanced features
        patterns['uses_cached_property'] = '@cached_property' in content
        patterns['uses_property'] = '@property' in content
        patterns['has_trigger_support'] = 'defer(' in content or 'TriggerEvent' in content

        return patterns

    def _determine_category(self, provider: str, class_name: str, file_path: Path) -> Tuple[str, str]:
        """Determine category and subcategory."""
        provider_categories = {
            'amazon': ('cloud', 'aws'),
            'google': ('cloud', 'gcp'),
            'azure': ('cloud', 'azure'),
            'databricks': ('data-engineering', 'databricks'),
            'http': ('integration', 'http'),
            'slack': ('notification', 'messaging'),
            'smtp': ('notification', 'email'),
            'postgres': ('database', 'postgresql'),
            'mysql': ('database', 'mysql'),
            'mongo': ('database', 'mongodb'),
            'redis': ('cache', 'redis'),
            'docker': ('container', 'docker'),
            'cncf': ('container', 'kubernetes'),
            'ssh': ('remote', 'ssh'),
            'sftp': ('remote', 'sftp'),
            'ftp': ('remote', 'ftp'),
        }

        if provider in provider_categories:
            return provider_categories[provider]

        # Fallback based on class name
        class_lower = class_name.lower()
        if 's3' in class_lower:
            return ('cloud', 'aws-s3')
        elif 'gcs' in class_lower or 'bigquery' in class_lower:
            return ('cloud', 'gcp')
        elif 'sql' in class_lower:
            return ('database', 'sql')

        return ('integration', provider)

    def _generate_success_factors(self, class_name: str, component_type: str,
                                   base_classes: List[str], code_patterns: Dict) -> List[str]:
        """Generate success factors based on extracted patterns."""
        factors = []

        if component_type == 'operator':
            factors.append(f"Inherits from {', '.join(base_classes)}")
            if code_patterns.get('has_execute'):
                factors.append("Implements execute() method")
            if code_patterns.get('has_execute_complete'):
                factors.append("Supports deferrable execution with execute_complete()")
            if code_patterns.get('has_trigger_support'):
                factors.append("Integrates with Airflow Triggers for async operations")

        elif component_type == 'sensor':
            factors.append(f"Inherits from {', '.join(base_classes)}")
            if code_patterns.get('has_poke'):
                factors.append("Implements poke() method for polling")
            if code_patterns.get('has_execute_complete'):
                factors.append("Supports deferrable mode for resource efficiency")

        elif component_type == 'hook':
            factors.append(f"Inherits from {', '.join(base_classes)}")
            if code_patterns.get('has_get_conn'):
                factors.append("Implements get_conn() for connection management")
            if code_patterns.get('has_close'):
                factors.append("Implements close() for proper resource cleanup")

        if code_patterns.get('uses_cached_property'):
            factors.append("Uses @cached_property for lazy initialization")

        if 'template_fields' in code_patterns.get('class_attributes', []):
            factors.append("Defines template_fields for Jinja templating support")

        return factors

    def _calculate_score(self, code_patterns: Dict, template_fields: List, docstring: str) -> int:
        """Calculate quality score for the pattern."""
        score = 150  # Base score for official patterns

        # Bonus for good documentation
        if len(docstring) > 200:
            score += 10
        if ':param' in docstring or 'Args:' in docstring:
            score += 10

        # Bonus for template fields
        score += min(len(template_fields) * 3, 15)

        # Bonus for advanced features
        if code_patterns.get('has_trigger_support'):
            score += 15
        if code_patterns.get('uses_cached_property'):
            score += 5

        return score

    def _generate_keywords(self, class_name: str, category: str,
                           provider: str, component_type: str) -> List[str]:
        """Generate relevance keywords."""
        keywords = [
            component_type,
            category,
            provider,
            class_name.lower(),
        ]

        # Add words from class name
        words = re.findall(r'[A-Z][a-z]+', class_name)
        keywords.extend([w.lower() for w in words])

        # Add provider-specific keywords
        provider_keywords = {
            'amazon': ['aws', 's3', 'ec2', 'lambda', 'sqs', 'ecs'],
            'google': ['gcp', 'gcs', 'bigquery', 'dataflow', 'pubsub'],
            'slack': ['slack', 'notification', 'message', 'channel'],
            'http': ['http', 'rest', 'api', 'request', 'webhook'],
        }
        if provider in provider_keywords:
            keywords.extend(provider_keywords[provider][:3])

        return list(set(keywords))[:15]


def merge_patterns(existing_path: Path, new_patterns: List[Dict]) -> Dict:
    """Merge new patterns with existing RAG database."""

    # Load existing patterns
    existing_data = {'patterns': [], 'pattern_summary': {}}
    if existing_path.exists():
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)

    existing_patterns = existing_data.get('patterns', [])
    existing_ids = {p['id'] for p in existing_patterns}

    # Add new patterns (avoid duplicates by component name)
    existing_names = {p['component_name'] for p in existing_patterns}
    added = 0

    for pattern in new_patterns:
        # Skip if we already have this component
        if pattern['component_name'] in existing_names:
            continue

        # Generate unique ID
        pattern['id'] = f"official_{pattern['component_name'].lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        existing_patterns.append(pattern)
        existing_names.add(pattern['component_name'])
        added += 1

    # Update summary
    by_type = {}
    by_category = {}
    for p in existing_patterns:
        comp_type = p.get('component_type', 'unknown')
        category = p.get('category', 'unknown')
        by_type[comp_type] = by_type.get(comp_type, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1

    result = {
        'patterns': existing_patterns,
        'updated_at': datetime.now().isoformat(),
        'pattern_summary': {
            'total_patterns': len(existing_patterns),
            'by_component_type': by_type,
            'by_category': by_category
        }
    }

    print(f"\nMerge complete: Added {added} new patterns")
    print(f"Total patterns: {len(existing_patterns)}")

    return result


def main():
    parser = argparse.ArgumentParser(description='Extract patterns from official Airflow providers')
    parser.add_argument('--source', required=True, help='Path to Airflow providers directory')
    parser.add_argument('--output', required=True, help='Output path for RAG patterns JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Extract but do not save')

    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)

    if not source_path.exists():
        print(f"Error: Source path does not exist: {source_path}")
        sys.exit(1)

    # Extract patterns
    extractor = AirflowPatternExtractor(str(source_path), verbose=args.verbose)
    new_patterns = extractor.extract_all()

    if args.dry_run:
        print(f"\nDry run - would add {len(new_patterns)} patterns")
        for p in new_patterns[:10]:
            print(f"  - {p['component_name']} ({p['component_type']})")
        if len(new_patterns) > 10:
            print(f"  ... and {len(new_patterns) - 10} more")
        return

    # Merge with existing and save
    merged_data = merge_patterns(output_path, new_patterns)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    print(f"\nPatterns saved to: {output_path}")


if __name__ == '__main__':
    main()
