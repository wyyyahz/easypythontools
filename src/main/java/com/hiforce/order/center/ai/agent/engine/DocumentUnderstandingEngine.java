package com.hiforce.order.center.ai.agent.engine;

import com.hiforce.order.center.ai.agent.model.Document;
import com.hiforce.order.center.ai.agent.model.UnderstandingResult;

/**
 * 文档理解引擎接口
 */
public interface DocumentUnderstandingEngine {
    
    /**
     * 理解文档内容
     *
     * @param document 文档对象
     * @return 理解结果
     */
    UnderstandingResult understand(Document document);
    
    /**
     * 提取文档主题
     *
     * @param document 文档对象
     * @return 文档主题
     */
    String extractTopic(Document document);
    
    /**
     * 生成文档摘要
     *
     * @param document 文档对象
     * @param maxLength 摘要最大长度
     * @return 文档摘要
     */
    String generateSummary(Document document, int maxLength);
    
    /**
     * 提取关键词
     *
     * @param document 文档对象
     * @param maxKeywords 最大关键词数量
     * @return 关键词列表
     */
    java.util.List<String> extractKeywords(Document document, int maxKeywords);
    
    /**
     * 识别实体
     *
     * @param document 文档对象
     * @return 实体列表
     */
    java.util.List<UnderstandingResult.Entity> recognizeEntities(Document document);
    
    /**
     * 分类文档
     *
     * @param document 文档对象
     * @return 文档类别
     */
    String classifyDocument(Document document);
    
    /**
     * 分析情感
     *
     * @param document 文档对象
     * @return 情感分析结果
     */
    UnderstandingResult.SentimentAnalysis analyzeSentiment(Document document);
}
