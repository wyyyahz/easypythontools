package com.hiforce.order.center.ai.agent.engine;

import com.hiforce.order.center.ai.agent.model.Document;
import com.hiforce.order.center.ai.agent.model.ExtractionResult;

/**
 * 信息抽取引擎接口
 */
public interface InformationExtractionEngine {
    
    /**
     * 从文档中抽取信息
     *
     * @param document 文档对象
     * @return 抽取结果
     */
    ExtractionResult extract(Document document);
    
    /**
     * 抽取实体
     *
     * @param document 文档对象
     * @return 抽取的实体列表
     */
    java.util.List<ExtractionResult.ExtractedEntity> extractEntities(Document document);
    
    /**
     * 抽取关系
     *
     * @param document 文档对象
     * @return 抽取的关系列表
     */
    java.util.List<ExtractionResult.ExtractedRelation> extractRelations(Document document);
    
    /**
     * 抽取事件
     *
     * @param document 文档对象
     * @return 抽取的事件列表
     */
    java.util.List<ExtractionResult.ExtractedEvent> extractEvents(Document document);
    
    /**
     * 抽取关键事实
     *
     * @param document 文档对象
     * @return 关键事实列表
     */
    java.util.List<ExtractionResult.KeyFact> extractKeyFacts(Document document);
}
