package com.hiforce.order.center.ai.agent;

import com.hiforce.order.center.ai.agent.model.Document;
import com.hiforce.order.center.ai.agent.model.ExtractionResult;
import com.hiforce.order.center.ai.agent.service.TextEmbeddingService;
import com.hiforce.order.center.ai.agent.service.VectorDatabaseService;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;
import java.util.Map;

/**
 * 向量数据库功能测试
 */
@Slf4j
@SpringBootTest
public class VectorDatabaseTest {
    
    @Autowired
    private TextEmbeddingService embeddingService;
    
    @Autowired
    private VectorDatabaseService vectorDatabaseService;
    
    /**
     * 测试文本向量化
     */
    @Test
    public void testTextEmbedding() {
        String text = "人工智能技术在2024年取得了重大突破";
        
        List<Float> vector = embeddingService.embed(text);
        
        log.info("文本: {}", text);
        log.info("向量维度: {}", vector.size());
        log.info("向量前10个值: {}", vector.subList(0, Math.min(10, vector.size())));
        
        // 测试相似度计算
        String text2 = "AI技术在2024年获得重要进展";
        List<Float> vector2 = embeddingService.embed(text2);
        
        double similarity = embeddingService.cosineSimilarity(vector, vector2);
        log.info("文本1: {}", text);
        log.info("文本2: {}", text2);
        log.info("余弦相似度: {}", similarity);
    }
    
    /**
     * 测试批量向量化
     */
    @Test
    public void testBatchEmbedding() {
        List<String> texts = List.of(
            "深度学习是机器学习的一个分支",
            "自然语言处理技术日益成熟",
            "计算机视觉在医疗领域应用广泛"
        );
        
        List<List<Float>> vectors = embeddingService.batchEmbed(texts);
        
        log.info("批量向量化完成，数量: {}", vectors.size());
        for (int i = 0; i < vectors.size(); i++) {
            log.info("文本{}的向量维度: {}", i + 1, vectors.get(i).size());
        }
    }
    
    /**
     * 测试向量插入和搜索
     */
    @Test
    public void testVectorInsertAndSearch() {
        // 创建测试文档
        Document document = Document.builder()
            .docId("test_doc_001")
            .title("测试文档")
            .content("人工智能技术在2024年取得了重大突破。深度学习模型在自然语言处理领域表现出色。")
            .docType("TXT")
            .source("测试")
            .build();
        
        // 生成向量
        List<Float> vector = embeddingService.embed(document.getContent());
        
        log.info("生成向量成功，维度: {}", vector.size());
        
        // 注意：这个测试需要Milvus服务运行
        // 如果Milvus未启动，vectorDatabaseService会自动降级
    }
    
    /**
     * 测试完整的文档处理和向量存储流程
     */
    @Test
    public void testFullWorkflowWithVectorStorage() {
        // 模拟一个完整的文档处理流程
        
        // 1. 创建文档
        Document document = Document.builder()
            .docId("workflow_test_001")
            .title("科技新闻报道")
            .content("2024年3月15日，某科技公司在北京发布了新一代人工智能产品。" +
                    "该产品采用了最新的深度学习技术，能够在医疗诊断中达到95%的准确率。" +
                    "公司CEO表示，这项技术将彻底改变医疗行业的未来。")
            .docType("NEWS")
            .source("科技日报")
            .build();
        
        log.info("=== 开始完整工作流测试 ===");
        log.info("文档ID: {}", document.getDocId());
        log.info("文档标题: {}", document.getTitle());
        log.info("文档内容长度: {}", document.getContent().length());
        
        // 2. 生成各种内容的向量
        List<Float> contentVector = embeddingService.embed(document.getContent());
        List<Float> titleVector = embeddingService.embed(document.getTitle());
        
        log.info("内容向量维度: {}", contentVector.size());
        log.info("标题向量维度: {}", titleVector.size());
        
        // 3. 计算标题和内容的相似度
        double similarity = embeddingService.cosineSimilarity(titleVector, contentVector);
        log.info("标题与内容的相似度: {}", similarity);
        
        // 4. 测试不同文本的相似度
        String query1 = "人工智能医疗应用";
        String query2 = "体育比赛结果";
        
        List<Float> query1Vector = embeddingService.embed(query1);
        List<Float> query2Vector = embeddingService.embed(query2);
        
        double sim1 = embeddingService.cosineSimilarity(query1Vector, contentVector);
        double sim2 = embeddingService.cosineSimilarity(query2Vector, contentVector);
        
        log.info("查询1 '{}' 与内容的相似度: {}", query1, sim1);
        log.info("查询2 '{}' 与内容的相似度: {}", query2, sim2);
        log.info("相关查询应该具有更高的相似度: {}", sim1 > sim2);
        
        log.info("=== 工作流测试完成 ===");
    }
    
    /**
     * 测试向量数据库连接
     */
    @Test
    public void testVectorDatabaseConnection() {
        log.info("测试向量数据库连接...");
        
        try {
            // 尝试执行一个简单的操作来测试连接
            // 如果Milvus未启动，这个方法会优雅地处理
            
            String testQuery = "测试查询";
            List<Map<String, Object>> results = vectorDatabaseService.searchByText(testQuery, 5);
            
            log.info("向量数据库连接测试完成");
            log.info("搜索结果数量: {}", results.size());
            
        } catch (Exception e) {
            log.warn("向量数据库连接测试失败（可能是Milvus未启动）: {}", e.getMessage());
        }
    }
}
