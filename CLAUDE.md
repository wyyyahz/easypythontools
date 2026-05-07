# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Dual-purpose project**: a Java AI Agent workflow system (Spring Boot 2.7.18, Java 8) + Python web scraping tools (Selenium/requests). The Java side is a rule-based document intelligence pipeline; the Python side scrapes Agoda hotel data. Output data (Excel, JSON, SQLite, screenshots) lives at the repo root and in `openclaw/`.

## Build & Run Commands (Java)

```bash
# Compile and package → target/ai-agent.jar
mvn clean package

# Run (port 8080): JAR or batch script
java -jar target/ai-agent.jar
./start.bat    # mvn clean → package -DskipTests → launch

# Run all tests
mvn test

# Single test (JUnit 4 style)
mvn test -Dtest=DocumentIntelligenceTest

# Single test method (JUnit 4)
mvn test -Dtest=DocumentIntelligenceTest#testProcessDocument

# JUnit 5 tests (VectorDatabaseTest)
mvn test -Dtest=VectorDatabaseTest

# Dev profile
java -jar target/ai-agent.jar --spring.profiles.active=dev
```

**Test mix**: `DocumentIntelligenceTest` uses JUnit 4 (`@RunWith(SpringRunner.class)`), `VectorDatabaseTest` uses JUnit 5. Both are `@SpringBootTest`.

## Python Scripts

```bash
# Install Python deps (from requirements.txt or manually)
pip install -r requirements.txt
# Dependencies: requests, selenium, openpyxl, pandas, beautifulsoup4, lxml

# Unified entry point (orchestrates multiple strategies)
python run.py

# Root-level scrapers (standalone versions)
python agoda_scraper.py           # v1 Selenium (original)
python agoda_scraper_v2.py        # v2
python agoda_scraper_v3.py        # v3
python agoda_scraper_v4.py        # v4
python agoda_scraper_final.py     # Final comprehensive version
python agoda_api_scraper.py       # API-based approach
python agoda_cdp_scraper.py       # Chrome DevTools Protocol
python agoda_js_scraper.py        # JavaScript injection

# Debug utilities
python debug_api.py               # Debug API requests
python debug_network.py           # Network-level debugging
python debug_session.py           # Session debugging

# Openclaw scrapers (35+ scripts)
python openclaw/full_scraper.py
```

### Python Scraping Strategies (openclaw/)

The `openclaw/` directory contains diverse scraping approaches for Agoda:

| Category | Scripts | Approach |
|---|---|---|
| **CDP-based** | `cdp_capture.py`, `cdp_capture2.py`, `cdp_scraper.py` | Chrome DevTools Protocol for stealth |
| **Session-based** | `session2.py`, `session3.py`, `fresh_session.py`, `multi_session.py`, `multi_session_v2.py` | Session management to avoid detection |
| **Batch/API** | `batch_api.py`, `batch_scroll.py`, `batch_brackets_plan.py` | Batch data collection |
| **Full scrapers** | `full_scraper.py`–`full_scraper_v8.py`, `scrape_full_v6.py`–`v9.py`, `final_scraper.py`, `final_scrape.py`, `mass_scraper.py`, `scrape_agoda.py` | Comprehensive implementations |
| **Data management** | `final_save.py`, `save_excel.py`, `save_hotels.py`, `merge_final.py`, `merge_final_excel.py`, `update_data.py`, `report.py` | Output processing and merging |
| **Utilities** | `area_scraper.py`, `date_scraper.py`, `multi_sort.py`, `multi_sort2.py`, `run_paginate.py`, `quick_test.py`, `capture_api_request.py`, `capture_npc.py`, `capture_summary.py`, `test_api.py`, `test_body.py` | Support and analysis |
| **Agent system** | `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, `IDENTITY.md`, `HEARTBEAT.md`, `HANDOVER.md`, `IMPLEMENTATION_GUIDE.md`, `SETUP_GUIDE.md` | Meta-instructions for AI agents operating in this workspace |

### Data Storage

- **SQLite**: `hotels.db` (root), `openclaw/agoda_wuhan.db`
- **Excel**: `hotels_*.xlsx` (root + openclaw, e.g. `agoda_wuhan_hotels_最终_2023条.xlsx`)
- **JSON**: `hotels_all.json`, `hotels_all_final.json`, `hotels_data.json`
- **HTML captures**: `agoda_homepage.html`, `agoda_search_result.html`, `agoda_overlay.html`, `page_debug.html`, `page_debug2.html`
- **Screenshots**: `screenshots/`, `openclaw/ScreenShot_*.png`

Uses `chromedriver.exe` (bundled) for Selenium-based browser automation.

## Java Architecture

Spring Boot 2.7.18 app (Java 8) implementing a **pipeline document intelligence workflow**:

```
Document → [Understanding Engine] → [Retrieval Engine (Index)] → [Extraction Engine] → [Analysis Engine] → Result
```

### Package Structure
```
com.hiforce.order.center.ai.agent
├── AIAgentApplication.java          # @SpringBootApplication entry point
├── controller/
│   └── DocumentIntelligenceController.java  # REST API at /api/ai-agent/*
├── service/
│   ├── DocumentIntelligenceService.java     # Facade → orchestrator + vector DB
│   ├── TextEmbeddingService.java            # Mock embedding (hash-based, 768-dim)
│   └── VectorDatabaseService.java           # Milvus client wrapper
├── workflow/
│   └── AgentWorkflowOrchestrator.java       # 4-step pipeline orchestrator
├── engine/
│   ├── DocumentUnderstandingEngine.java     # Interface
│   ├── DocumentRetrievalEngine.java         # Interface
│   ├── InformationExtractionEngine.java     # Interface
│   ├── ComprehensiveAnalysisEngine.java     # Interface
│   └── impl/
│       ├── DocumentUnderstandingEngineImpl.java  # Rule+stats: topic, summary, keywords, entities, category, sentiment, language
│       ├── DocumentRetrievalEngineImpl.java      # In-memory inverted index, TF scoring, full-text search
│       ├── InformationExtractionEngineImpl.java  # Regex-based entity/relation/event/key-fact extraction
│       └── ComprehensiveAnalysisEngineImpl.java  # Quality scoring, risk assessment, trend analysis
└── model/
    ├── Document.java                 # Input document (id, title, content, docType, source, segments)
    ├── AgentWorkflow.java            # Workflow with steps + result, state machine enums
    ├── UnderstandingResult.java      # topic, summary, keywords, entities, category, sentiment, language, confidence
    ├── RetrievalResult.java          # query, documents list with relevance scores
    ├── ExtractionResult.java         # entities, relations, events, keyFacts, structuredData
    ├── AnalysisResult.java           # summary, findings, insights, trendAnalysis, riskAssessment, qualityScore
    └── VectorDocument.java           # Vector DB document (vector ID, docId, contentType, vector, metadata)
```

### Engine Details

| Engine | Approach | Key Output |
|---|---|---|
| **Understanding** | Rule+statistics (stop words, regex entities, keyword-based classification, sentiment dictionary) | Topic, summary, keywords, entities, category, sentiment, language |
| **Retrieval** | In-memory `ConcurrentHashMap` inverted index, TF scoring, query-term matching with snippet extraction | Ranked document list with relevance scores |
| **Extraction** | Regex patterns for person/organization/location/date/money entities, relation patterns, event patterns | Entities, relations, events, key facts; also stores vectors in Milvus |
| **Analysis** | Heuristic quality scoring (completeness, accuracy, consistency, readability), risk level assessment | Quality scores, risk assessment, insights, findings |

### Workflow State Machine
- **Workflow**: `PENDING → RUNNING → COMPLETED / FAILED`
- **Steps**: `PENDING → RUNNING → SUCCESS / FAILED`
- Per-step try/catch; any step failure fails the entire workflow; batch mode catches per-document failures individually

### API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/ai-agent/health` | Health check → `{"status": "UP"}` |
| POST | `/api/ai-agent/process` | Process single document |
| POST | `/api/ai-agent/process/batch` | Batch process documents |
| GET | `/api/ai-agent/search` | Full-text search (query, maxResults) |
| POST | `/api/ai-agent/understand` | Document understanding only |
| POST | `/api/ai-agent/extract` | Information extraction only |
| POST | `/api/ai-agent/analyze` | Document analysis only |
| POST | `/api/ai-agent/vector/search` | Vector similarity search |
| DELETE | `/api/ai-agent/vector/{docId}` | Delete vector document |
| POST | `/api/ai-agent/vector/clear` | Clear vector database |

### Vector Database (Milvus)

- `VectorDatabaseService` — Milvus client via `milvus-sdk-java 2.3.5`
- Collection: `document_vectors`, 768-dim `FloatVector`, IVF_FLAT index, COSINE metric
- Content types: `FULL_TEXT`, `ENTITY`, `RELATION`, `EVENT`, `KEY_FACT`
- `TextEmbeddingService` — simulated embedding using character hash + bigram features + L2 normalization (replace with real model)
- Config in `application.yml`: host, port, dimension, enabled flag
- Graceful degradation: Milvus failures logged but don't block processing; `init()` catches exceptions and sets client to null

**Known bug**: In `VectorDatabaseService.insert()` (~line 225), `com.fasterxml.jackson.databind.ObjectMapper()` should be `new com.fasterxml.jackson.databind.ObjectMapper()` — static method call on class won't compile.

### Key Design Notes

- **No persistence**: In-memory index only (lost on restart). No database on the Java side.
- **All engine results are rule-based**, not ML-driven (no real NLP/ML models)
- Configuration in `src/main/resources/application.yml` — workflow timeout (300s), max concurrent (10), engine thresholds
- Dev profile at `src/main/resources/application-dev.yml` (same port, DEBUG logging for agent package)
- Logging via Logback (`logback.xml`): console + rolling file (30-day retention, 100MB per file) in `./logs/`
- Lombok used extensively (`@Data`, `@Builder`, `@Slf4j`)
- Utility libraries: `hutool-all 5.8.25`, `commons-lang3`, `commons-collections4`

### Environment & Git

- **OS**: Windows 11 (paths use `/` in bash, `\` in cmd — `.bat` scripts are Windows-native)
- **Java build output**: `target/` (gitignored)
- **ChromeDriver**: bundled at root as `chromedriver.exe`
- **Output data directories** (gitignored): `导出数据/`, `导出数据_全部原始数据/`, `导出数据_完整版/`, `screenshots/`
- **Claude session state**: `.claude/` (gitignored) — worktrees, memory, scheduled tasks
