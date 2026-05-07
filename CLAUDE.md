# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Overview

**Dual-purpose project**: a Java AI Agent workflow system (Spring Boot) + Python web scraping tools (Selenium). The Java side is a document intelligence pipeline; the Python side scrapes Agoda hotel data.

## Build & Run Commands (Java)

```bash
# Compile and package
mvn clean package

# Run (port 8080)
java -jar target/ai-agent.jar
# or: start.bat (runs mvn clean + mvn package -DskipTests then launches)

# Run all tests
mvn test

# Run a single test class (JUnit 4 style)
mvn test -Dtest=DocumentIntelligenceTest

# Run a single test method (JUnit 4)
mvn test -Dtest=DocumentIntelligenceTest#testProcessDocument

# Run JUnit 5 tests (VectorDatabaseTest uses JUnit 5)
mvn test -Dtest=VectorDatabaseTest

# Skip tests during build
mvn package -DskipTests

# Use dev profile
java -jar target/ai-agent.jar --spring.profiles.active=dev
```

**Test mix**: `DocumentIntelligenceTest` uses JUnit 4 (`@RunWith(SpringRunner.class)`), `VectorDatabaseTest` uses JUnit 5 (`@Test` from `org.junit.jupiter.api`). Both are `@SpringBootTest`.

## Python Scripts

```bash
# Install Python dependencies
pip install requests selenium openpyxl pandas beautifulsoup4 lxml

# Run a scraper (root level: 3 versions of Agoda scraper)
python agoda_scraper.py
python agoda_scraper_v2.py
python agoda_scraper_v3.py

# Run openclaw scraper (35+ scripts with different strategies)
python openclaw/full_scraper.py
```

### Python Scraping Strategies (openclaw/)

The `openclaw/` directory contains a diverse set of scraping approaches for Agoda:
- **CDP-based**: `cdp_capture.py`, `cdp_capture2.py`, `cdp_scraper.py` — Chrome DevTools Protocol for stealth
- **Session-based**: `session2.py`, `session3.py`, `fresh_session.py`, `multi_session.py`, `multi_session_v2.py` — session management for avoiding detection
- **Batch/API**: `batch_api.py`, `batch_scroll.py`, `batch_brackets_plan.py` — batch data collection
- **Full scrapers**: `full_scraper.py` through `full_scraper_v4.py` — comprehensive implementations
- **Data management**: `save_excel.py`, `save_hotels.py`, `merge_final.py`, `update_data.py`, `report.py` — output processing
- **Agent system docs**: `AGENTS.md`, `HANDOVER.md`, `HEARTBEAT.md`, `IDENTITY.md`, `SOUL.md`, `TOOLS.md`, `USER.md`, `IMPLEMENTATION_GUIDE.md`, `SETUP_GUIDE.md`

Data storage: SQLite (`hotels.db`, `openclaw/*.db`) and Excel (`hotels_*.xlsx`). Uses ChromeDriver (`chromedriver.exe`) for browser automation.

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
