# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Compile
mvn clean package

# Run
java -jar target/ai-agent.jar
# or: start.bat (also runs mvn clean package -DskipTests first)

# Run all tests
mvn test

# Run a single test class
mvn test -Dtest=DocumentIntelligenceTest

# Run a single test method
mvn test -Dtest=DocumentIntelligenceTest#testProcessDocument

# Skip tests during build
mvn package -DskipTests
```

## Architecture Overview

Spring Boot 2.7.18 app (Java 8) implementing a **pipeline document intelligence workflow** with four sequential engines:

```
Document → [Understanding Engine] → [Retrieval Engine (Index)] → [Extraction Engine] → [Analysis Engine] → Result
```

### Layers (controller → service → workflow → engine → model)

- **Controller**: `DocumentIntelligenceController` — REST API at `/api/ai-agent/*` (process, batch, search, understand, extract, analyze, vector/search)
- **Service**: `DocumentIntelligenceService` — facade that delegates to `AgentWorkflowOrchestrator` and `VectorDatabaseService`
- **Workflow**: `AgentWorkflowOrchestrator` — orchestrates the 4-step pipeline (Understanding → Indexing → Extraction → Analysis), tracks step status/timing, computes overall score, generates summary report
- **Engines** (interface in `engine/`, impl in `engine/impl/`):
  - `DocumentUnderstandingEngine` — topic, summary, keywords, entities, category, sentiment, language (rule+statistics based)
  - `DocumentRetrievalEngine` — in-memory inverted index, TF scoring, full-text + similarity search
  - `InformationExtractionEngine` — regex-based entity/relation/event/key-fact extraction
  - `ComprehensiveAnalysisEngine` — multi-dimension quality scoring (completeness, accuracy, consistency, readability), risk assessment, trend analysis
- **Models** in `model/`: `Document`, `AgentWorkflow` (with `WorkflowStep`, `WorkflowResult`), `UnderstandingResult`, `RetrievalResult`, `ExtractionResult`, `AnalysisResult` (with `QualityScore`), `VectorDocument`

### Vector Database (Milvus)

- `VectorDatabaseService` — Milvus client wrapper (auto-creates collection on startup, IVF_FLAT index, COSINE metric)
- `TextEmbeddingService` — mock embedding service (replace with real model like `text-embedding-ada-002`)
- Content types stored: FULL_TEXT, ENTITY, RELATION, EVENT, KEY_FACT
- Config in `application.yml`: host, port, dimension (768), enabled flag
- Graceful degradation: Milvus failures logged but don't block document processing

### Key Design Notes

- **No persistence**: Index is in-memory (lost on restart). No database. Engine results are rule-based, not ML-driven.
- **Workflow state machine**: `PENDING → RUNNING → COMPLETED/FAILED` (workflow), `PENDING → RUNNING → SUCCESS/FAILED` (steps)
- **Error handling**: Per-step try/catch in orchestrator propagates exceptions to fail the workflow; batch processing catches per-document failures individually
- **Configuration** in `src/main/resources/application.yml` — workflow timeout, concurrent limits, engine thresholds
- **Health check**: GET `/api/ai-agent/health` returns `{"status": "UP"}`
