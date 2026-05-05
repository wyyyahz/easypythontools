package com.hiforce.order.center.ai.agent.service;

import com.hiforce.order.center.ai.agent.model.*;
import com.hiforce.order.center.ai.agent.workflow.AgentWorkflowOrchestrator;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

/**
 * 文档智能处理服务
 */
@Slf4j
@Service
public class DocumentIntelligenceService {
    
    @Autowired
    private AgentWorkflowOrchestrator workflowOrchestrator;
    
    /**
     * 处理单个文档
     *
     * @param document 文档对象
     * @return 工作流结果
     */
    public AgentWorkflow processDocument(Document document) {
        // 如果文档ID为空，生成一个
        if (document.getDocId() == null || document.getDocId().isEmpty()) {
            document.setDocId(UUID.randomUUID().toString().replace("-", ""));
        }
        
        return workflowOrchestrator.executeWorkflow(document);
    }
    
    /**
     * 批量处理文档
     *
     * @param documents 文档列表
     * @return 工作流结果列表
     */
    public List<AgentWorkflow> processDocuments(List<Document> documents) {
        log.info("批量处理文档，数量: {}", documents.size());
        return workflowOrchestrator.executeBatchWorkflow(documents);
    }
    
    /**
     * 检索文档
     *
     * @param query 查询语句
     * @param maxResults 最大结果数
     * @return 检索结果
     */
    public RetrievalResult searchDocuments(String query, int maxResults) {
        log.info("检索文档，查询: {}", query);
        return workflowOrchestrator.executeRetrievalWorkflow(query, maxResults);
    }
    
    /**
     * 理解文档
     *
     * @param document 文档对象
     * @return 理解结果
     */
    public UnderstandingResult understandDocument(Document document) {
        log.info("理解文档: {}", document.getDocId());
        // 这里可以直接调用引擎，也可以通过工作流
        return workflowOrchestrator.executeWorkflow(document).getResult().getUnderstandingResult();
    }
    
    /**
     * 抽取文档信息
     *
     * @param document 文档对象
     * @return 抽取结果
     */
    public ExtractionResult extractInformation(Document document) {
        log.info("抽取文档信息: {}", document.getDocId());
        return workflowOrchestrator.executeWorkflow(document).getResult().getExtractionResult();
    }
    
    /**
     * 分析文档
     *
     * @param document 文档对象
     * @return 分析结果
     */
    public AnalysisResult analyzeDocument(Document document) {
        log.info("分析文档: {}", document.getDocId());
        return workflowOrchestrator.executeWorkflow(document).getResult().getAnalysisResult();
    }
}
