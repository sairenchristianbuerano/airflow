# Repository Structure

**Last Updated:** 2026-01-20
**Status:** Reorganized and Cleaned

---

## Root Directory

```
airflow/
├── .env                      # Environment variables (API keys - DO NOT COMMIT)
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore patterns
├── docker-compose.yml        # Docker Compose configuration
├── LICENSE                   # Project license
├── README.md                 # Project overview and quick start
└── component-generator/      # ⭐ Main component generator directory
```

**Root contains only essential configuration files.**

---

## Component Generator Structure

```
component-generator/
├── src/                      # Source code
│   ├── airflow_agent.py      # Main AI agent for code generation (Phase 1 integrated)
│   ├── pattern_extractor.py  # Phase 1: Pattern extraction from successful code
│   ├── pattern_storage.py    # Phase 1: Pattern database storage/retrieval
│   ├── base_classes.py       # Data models and base classes
│   ├── airflow_validator.py  # Code validation logic
│   ├── dependency_validator.py # Dependency checking
│   ├── test_generator.py     # Test file generation
│   ├── documentation_generator.py # Documentation generation
│   ├── error_tracker.py      # Error tracking system
│   ├── learning_database.py  # Learning database interface
│   └── service.py            # FastAPI service endpoints
│
├── data/                     # Data storage
│   ├── patterns.db           # Phase 1: Pattern learning database (SQLite)
│   ├── learning.db           # General learning database
│   ├── rag_success_patterns.json # RAG database for pattern retrieval
│   └── generated_operators/  # Legacy generated operators
│
├── scripts/                  # Utility scripts
│   ├── extract_and_store_patterns.py # Phase 1: Pattern extraction runner
│   └── index_successful_component.py # RAG indexing script
│
├── examples/                 # Example components and DAGs
│   ├── successful_components/
│   │   └── nemo_question_answering/ # Preserved NeMo QA component (Phase 1)
│   ├── generated/            # Generated sample components
│   ├── custom_operators/     # Custom operator examples
│   └── dags/                 # Example DAG files
│
├── docs/                     # Documentation
│   ├── API.md                # API endpoint documentation
│   ├── AIRFLOW_SETUP.md      # Airflow setup guide
│   ├── ARCHITECTURE_SEQUENCE_DIAGRAM.md # System architecture
│   ├── COMPONENT_IMPROVEMENT_PLAN.md # Improvement roadmap
│   ├── COMPONENT_SPEC_FORMAT.yaml # Component specification format
│   ├── SELF_LEARNING_GENERATOR_PLAN.md # Phase 1-6 master plan
│   ├── PHASE1_MVP_COMPLETE.md # Phase 1 completion summary
│   ├── PHASE1_INTEGRATION_TEST_RESULTS.md # Phase 1 test results
│   ├── PHASE1_COMPLETE_READY_FOR_PHASE2.md # Phase 1 readiness
│   ├── SELF_LEARNING_PROGRESS.md # Overall progress tracking
│   ├── NEMO_COMPONENT_SUCCESS_SUMMARY.md # NeMo case study
│   ├── PRESERVATION_CHECKLIST.md # Component preservation process
│   └── ... (other documentation)
│
├── tests/                    # Test files
│   ├── test_generate.py      # Generation tests
│   ├── test_generate_endpoint.py # API endpoint tests
│   ├── test_phase1.py        # Phase 1 tests
│   ├── test_phase1.sh        # Phase 1 test script
│   ├── check_*.py            # Validation scripts
│   ├── verify_*.py           # Verification scripts
│   └── ... (test files)
│
├── test-outputs/             # Test output files
│   ├── sentiment*.json       # Sentiment operator test outputs
│   ├── phase2*.json          # Phase 2 test outputs
│   ├── nemo*.json            # NeMo test outputs
│   └── ... (other test outputs)
│
├── temp/                     # Temporary files
│
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Service composition (if exists)
├── start_service.bat         # Windows service starter
├── start_service.sh          # Linux/Mac service starter
├── sample_operator_spec.yaml # Sample operator specification
├── sample_sensor_spec.yaml   # Sample sensor specification
├── sample_comprehensive_spec.yaml # Comprehensive spec example
└── REPO_STRUCTURE.md         # This file
```

---

## Directory Purposes

### `/src` - Source Code
**Purpose:** Core application code for the component generator

**Key Files:**
- `airflow_agent.py` - Main AI-powered code generation logic
  - ✅ Phase 1 integrated: Pattern retrieval and injection
  - Uses Claude Sonnet 4 API for code generation
  - Automatic pattern extraction after successful generation

- `pattern_extractor.py` - Phase 1: Pattern extraction
  - Extracts 11 pattern types from successful code
  - Structural, import, execution, error handling, etc.

- `pattern_storage.py` - Phase 1: Pattern database
  - SQLite database for pattern storage/retrieval
  - Confidence-based pattern scoring
  - Similar component matching

- `service.py` - FastAPI REST API
  - `/generate` - Generate component from spec
  - `/generate/sample` - Generate sample component
  - `/feasibility` - Check generation feasibility
  - `/health` - Health check

### `/data` - Data Storage
**Purpose:** Databases and persistent storage

**Key Files:**
- `patterns.db` - Phase 1 pattern learning database
  - 10 patterns from NeMo component
  - Confidence scoring, usage tracking
  - Pattern combinations

- `learning.db` - General learning database
  - Component generation history
  - Error tracking
  - Performance metrics

- `rag_success_patterns.json` - RAG database
  - NeMo component indexed (165/165 score)
  - Code patterns and metadata

### `/scripts` - Utility Scripts
**Purpose:** Helper scripts for data processing and testing

**Key Files:**
- `extract_and_store_patterns.py` - Pattern extraction runner
  - Extracts patterns from successful components
  - Stores in patterns.db
  - Tests pattern retrieval

- `index_successful_component.py` - RAG indexing
  - Indexes components into RAG database
  - Calculates success scores
  - Generates embeddings

### `/examples` - Example Components
**Purpose:** Sample components and successful generations

**Structure:**
- `successful_components/nemo_question_answering/` - Preserved NeMo QA component
  - Full operator code
  - Test files
  - DAG examples
  - Metadata and README

- `generated/` - Generated sample components
  - Weather operator
  - Other test generations

- `custom_operators/` - Custom operator examples
- `dags/` - Example DAG files

### `/docs` - Documentation
**Purpose:** Project documentation and progress tracking

**Categories:**
- **API Docs:** API.md
- **Setup Guides:** AIRFLOW_SETUP.md, ARCHITECTURE_SEQUENCE_DIAGRAM.md
- **Plans:** SELF_LEARNING_GENERATOR_PLAN.md, COMPONENT_IMPROVEMENT_PLAN.md
- **Phase Reports:** PHASE1_MVP_COMPLETE.md, PHASE1_INTEGRATION_TEST_RESULTS.md
- **Progress:** SELF_LEARNING_PROGRESS.md
- **Case Studies:** NEMO_COMPONENT_SUCCESS_SUMMARY.md

### `/tests` - Test Files
**Purpose:** Test scripts and validation tools

**Types:**
- Unit tests (test_*.py)
- Integration tests (test_generate_endpoint.py)
- Validation scripts (check_*.py, verify_*.py)
- Phase-specific tests (test_phase1.py)

### `/test-outputs` - Test Outputs
**Purpose:** JSON outputs from test runs

**Contents:**
- Sentiment operator test outputs
- Phase 2 test results
- NeMo test results
- Sample test outputs

---

## File Naming Conventions

### Source Code
- `*_agent.py` - AI agent modules
- `*_generator.py` - Code/doc generation modules
- `*_validator.py` - Validation modules
- `*_storage.py` - Data storage modules
- `*_extractor.py` - Data extraction modules

### Documentation
- `*.md` - Markdown documentation
- `PHASE*_*.md` - Phase-specific documentation
- `*_PLAN.md` - Planning documents
- `*_SUMMARY.md` - Summary reports
- `*_GUIDE.md` - How-to guides

### Tests
- `test_*.py` - Python test files
- `test_*.json` - Test input/output data
- `test_*.yaml` - Test specifications
- `check_*.py` - Validation scripts
- `verify_*.py` - Verification scripts

### Examples
- `sample_*.yaml` - Sample specifications
- `generated_*.py` - Generated code examples

---

## Important Files

### Configuration
- `.env` - **NEVER COMMIT** - Contains API keys
- `.env.example` - Template for environment variables
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Docker services

### Entry Points
- `src/service.py` - FastAPI application entry point
- `start_service.sh` / `start_service.bat` - Service startup scripts

### Phase 1 (Pattern Learning)
- `src/pattern_extractor.py` - Pattern extraction logic
- `src/pattern_storage.py` - Pattern database
- `data/patterns.db` - Pattern storage (SQLite)
- `docs/PHASE1_COMPLETE_READY_FOR_PHASE2.md` - Phase 1 status

### Core Generator
- `src/airflow_agent.py` - Main code generation logic (Phase 1 integrated)
- `src/base_classes.py` - Data models
- `src/airflow_validator.py` - Code validation

---

## Quick Navigation

### Want to...

**Understand the system?**
→ Read `/docs/API.md` and `/docs/ARCHITECTURE_SEQUENCE_DIAGRAM.md`

**See successful examples?**
→ Check `/examples/successful_components/nemo_question_answering/`

**Learn about Phase 1?**
→ Read `/docs/PHASE1_COMPLETE_READY_FOR_PHASE2.md`

**Run tests?**
→ Use scripts in `/tests/`

**View pattern database?**
→ Query `/data/patterns.db` (SQLite)

**Generate a component?**
→ POST to `http://localhost:8095/api/airflow/component-generator/generate`

**Start the service?**
→ Run `./start_service.sh` (or `.bat` on Windows)

---

## Git Ignored Items

See `.gitignore` for full list. Key ignored items:

- `.env` - Environment variables (contains secrets)
- `__pycache__/` - Python cache
- `*.db` - SQLite databases (except tracked in data/)
- `*.log` - Log files
- `env/` - Virtual environment
- `test_*.json` - Test outputs (in gitignore, but moved to test-outputs/)
- `phase2_*.json` - Phase 2 outputs

---

## Development Workflow

### 1. Start Service
```bash
cd component-generator
./start_service.sh
```

### 2. Generate Component
```bash
curl -X POST http://localhost:8095/api/airflow/component-generator/generate \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

### 3. Patterns Are Automatically Learned
- On successful generation → patterns extracted → stored in patterns.db
- On next generation → patterns retrieved → injected into prompt
- Continuous improvement!

### 4. Run Tests
```bash
cd tests
python test_generate_endpoint.py
```

---

## Maintenance

### Keep Clean
- Test outputs → `/test-outputs`
- Documentation → `/docs`
- Examples → `/examples`
- Source code → `/src`

### Regular Tasks
- Update documentation in `/docs`
- Review patterns in `/data/patterns.db`
- Clean `/test-outputs` periodically
- Archive old examples

### Before Commit
- Check `.gitignore` to avoid committing secrets
- Update relevant docs
- Run tests
- Review changes in `/src`

---

## Repository Statistics

### Current State (2026-01-20)

**Root Files:** 6 essential files only
- Configuration: .env, .env.example, .gitignore
- Docker: docker-compose.yml
- Documentation: README.md, LICENSE

**component-generator/** ~120+ files organized in:
- `/src` - 12 Python modules
- `/data` - 3 databases + generated operators
- `/scripts` - 2 utility scripts
- `/examples` - 1 successful component preserved
- `/docs` - 40+ documentation files
- `/tests` - 30+ test files
- `/test-outputs` - 30+ test output files

**Total Documentation:** 40+ markdown files
**Total Tests:** 30+ test files
**Phase 1 Status:** ✅ Complete and Integrated
**Pattern Database:** 10 patterns from 1 component (NeMo QA)

---

## Next Steps

### Immediate
- Continue to Phase 2 (Error Learning)
- Generate more components to build pattern library
- Keep documentation updated in `/docs`

### Ongoing
- Monitor pattern match rates
- Track performance metrics
- Maintain clean structure

---

**Repository Structure - Last Updated: 2026-01-20**
**Status:** Reorganized, Clean, Ready for Phase 2
