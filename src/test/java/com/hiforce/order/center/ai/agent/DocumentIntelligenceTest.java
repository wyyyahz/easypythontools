package com.hiforce.order.center.ai.agent;

import com.hiforce.order.center.ai.agent.model.*;
import com.hiforce.order.center.ai.agent.service.DocumentIntelligenceService;
import lombok.extern.slf4j.Slf4j;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Arrays;
import java.util.List;

/**
 * 文档智能处理测试
 */
@Slf4j
@RunWith(SpringRunner.class)
@SpringBootTest
public class DocumentIntelligenceTest {
    
    @Autowired
    private DocumentIntelligenceService documentIntelligenceService;
    
    /**
     * 测试单个文档处理
     */
    @Test
    public void testProcessDocument() {
        // 创建测试文档
        Document document = Document.builder()
            .title("人工智能技术发展报告")
            .content("人工智能技术在近年来取得了快速发展。2024年，各大科技公司纷纷加大了对AI技术的投入。" +
                "深度学习、自然语言处理、计算机视觉等领域都取得了重要突破。" +
                "预计未来几年，AI技术将在医疗、金融、教育等行业得到更广泛的应用。" +
                "然而，AI技术的发展也带来了一些挑战，如数据隐私、算法偏见等问题需要解决。")
            .docType("TXT")
            .source("测试来源")
            .build();
        
        // 处理文档
        AgentWorkflow workflow = documentIntelligenceService.processDocument(document);
        
        // 输出结果
        log.info("工作流ID: {}", workflow.getWorkflowId());
        log.info("工作流状态: {}", workflow.getStatus());
        
        if (workflow.getResult() != null) {
            AgentWorkflow.WorkflowResult result = workflow.getResult();
            
            // 理解结果
            if (result.getUnderstandingResult() != null) {
                UnderstandingResult understanding = result.getUnderstandingResult();
                log.info("文档主题: {}", understanding.getTopic());
                log.info("文档分类: {}", understanding.getCategory());
                log.info("关键词: {}", understanding.getKeywords());
            }
            
            // 抽取结果
            if (result.getExtractionResult() != null) {
                ExtractionResult extraction = result.getExtractionResult();
                log.info("抽取实体数: {}", 
                    extraction.getEntities() != null ? extraction.getEntities().size() : 0);
                log.info("抽取关系数: {}", 
                    extraction.getRelations() != null ? extraction.getRelations().size() : 0);
            }
            
            // 分析结果
            if (result.getAnalysisResult() != null) {
                AnalysisResult analysis = result.getAnalysisResult();
                log.info("分析摘要: {}", analysis.getSummary());
                log.info("质量评分: {}", 
                    analysis.getQualityScore() != null ? analysis.getQualityScore().getOverall() : 0);
            }
            
            // 总结报告
            log.info("总结报告:\n{}", result.getSummaryReport());
        }
    }
    
    /**
     * 测试文档检索
     */
    @Test
    public void testSearchDocuments() {
        // 先索引一些文档
        Document doc1 = Document.builder()
            .docId("doc1")
            .title("机器学习入门")
            .content("机器学习是人工智能的一个重要分支。它通过算法让计算机从数据中学习。")
            .docType("TXT")
            .build();
        
        Document doc2 = Document.builder()
            .docId("doc2")
            .title("深度学习应用")
            .content("深度学习在图像识别、自然语言处理等领域有广泛应用。")
            .docType("TXT")
            .build();
        
        documentIntelligenceService.processDocument(doc1);
        documentIntelligenceService.processDocument(doc2);
        
        // 执行检索
        RetrievalResult result = documentIntelligenceService.searchDocuments("机器学习", 10);
        
        log.info("检索到 {} 个文档", result.getTotalCount());
        result.getDocuments().forEach(doc -> {
            log.info("文档: {}, 相关性: {}", doc.getTitle(), doc.getRelevanceScore());
        });
    }
    
    /**
     * 测试批量文档处理
     */
    @Test
    public void testBatchProcessDocuments() {
        List<Document> documents = Arrays.asList(
            Document.builder()
                .title("文档1")
                .content("这是第一个测试文档的内容。")
                .docType("TXT")
                .build(),
            Document.builder()
                .title("文档2")
                .content("这是第二个测试文档的内容。")
                .docType("TXT")
                .build()
        );
        
        List<AgentWorkflow> workflows = documentIntelligenceService.processDocuments(documents);
        
        log.info("批量处理完成，共处理 {} 个文档", workflows.size());
        workflows.forEach(workflow -> {
            log.info("文档: {}, 状态: {}", 
                workflow.getWorkflowId(), workflow.getStatus());
        });
    }
}
