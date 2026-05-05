package com.hiforce.order.center.ai.agent.controller;

import com.hiforce.order.center.ai.agent.model.*;
import com.hiforce.order.center.ai.agent.service.DocumentIntelligenceService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 文档智能处理控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/ai-agent")
public class DocumentIntelligenceController {
    
    @Autowired
    private DocumentIntelligenceService documentIntelligenceService;
    
    @Autowired
    private com.hiforce.order.center.ai.agent.service.VectorDatabaseService vectorDatabaseService;
    
    /**
     * 处理单个文档
     */
    @PostMapping("/process")
    public ResponseEntity<Map<String, Object>> processDocument(@RequestBody Document document) {
        log.info("收到文档处理请求");
        
        try {
            AgentWorkflow workflow = documentIntelligenceService.processDocument(document);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("workflow", workflow);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("文档处理失败", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 批量处理文档
     */
    @PostMapping("/process/batch")
    public ResponseEntity<Map<String, Object>> processDocuments(@RequestBody List<Document> documents) {
        log.info("收到批量文档处理请求，数量: {}", documents.size());
        
        try {
            List<AgentWorkflow> workflows = documentIntelligenceService.processDocuments(documents);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("workflows", workflows);
            response.put("count", workflows.size());
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("批量文档处理失败", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 检索文档
     */
    @GetMapping("/search")
    public ResponseEntity<Map<String, Object>> searchDocuments(
            @RequestParam String query,
            @RequestParam(defaultValue = "10") int maxResults) {
        log.info("收到文档检索请求，查询: {}", query);
        
        try {
            RetrievalResult result = documentIntelligenceService.searchDocuments(query, maxResults);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("result", result);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("文档检索失败", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 理解文档
     */
    @PostMapping("/understand")
    public ResponseEntity<Map<String, Object>> understandDocument(@RequestBody Document document) {
        log.info("收到文档理解请求");
        
        try {
            UnderstandingResult result = documentIntelligenceService.understandDocument(document);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("result", result);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("文档理解失败", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 抽取文档信息
     */
    @PostMapping("/extract")
    public ResponseEntity<Map<String, Object>> extractInformation(@RequestBody Document document) {
        log.info("收到信息抽取请求");
        
        try {
            ExtractionResult result = documentIntelligenceService.extractInformation(document);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("result", result);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("信息抽取失败", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 分析文档
     */
    @PostMapping("/analyze")
    public ResponseEntity<Map<String, Object>> analyzeDocument(@RequestBody Document document) {
        log.info("收到文档分析请求");
        
        try {
            AnalysisResult result = documentIntelligenceService.analyzeDocument(document);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("result", result);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("文档分析失败", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 健康检查
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "UP");
        response.put("service", "AI Agent Document Intelligence");
        
        return ResponseEntity.ok(response);
    }
    
    /**
     * 向量相似度搜索
     */
    @PostMapping("/vector/search")
    public ResponseEntity<Map<String, Object>> vectorSearch(
            @RequestBody Map<String, Object> request) {
        log.info("收到向量搜索请求");
        
        try {
            String queryText = (String) request.get("queryText");
            Integer topK = request.get("topK") != null ? 
                ((Number) request.get("topK")).intValue() : 10;
            
            if (queryText == null || queryText.isEmpty()) {
                Map<String, Object> response = new HashMap<>();
                response.put("success", false);
                response.put("error", "查询文本不能为空");
                return ResponseEntity.badRequest().body(response);
            }
            
            List<Map<String, Object>> results = vectorDatabaseService.searchByText(queryText, topK);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("results", results);
            response.put("count", results.size());
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("向量搜索失败", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 删除向量文档
     */
    @DeleteMapping("/vector/{docId}")
    public ResponseEntity<Map<String, Object>> deleteVectorDocument(@PathVariable String docId) {
        log.info("收到删除向量文档请求，docId: {}", docId);
        
        try {
            boolean success = vectorDatabaseService.delete(docId);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", success);
            response.put("docId", docId);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("删除向量文档失败", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.internalServerError().body(response);
        }
    }
    
    /**
     * 清空向量数据库
     */
    @PostMapping("/vector/clear")
    public ResponseEntity<Map<String, Object>> clearVectorDatabase() {
        log.info("收到清空向量数据库请求");
        
        try {
            vectorDatabaseService.clear();
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "向量数据库已清空");
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("清空向量数据库失败", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.internalServerError().body(response);
        }
    }
}
