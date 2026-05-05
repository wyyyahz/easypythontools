package com.hiforce.order.center.ai.agent.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * 信息抽取结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ExtractionResult implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * 抽取的实体列表
     */
    private List<ExtractedEntity> entities;
    
    /**
     * 抽取的关系列表
     */
    private List<ExtractedRelation> relations;
    
    /**
     * 抽取的事件列表
     */
    private List<ExtractedEvent> events;
    
    /**
     * 抽取的关键事实
     */
    private List<KeyFact> keyFacts;
    
    /**
     * 结构化数据
     */
    private Map<String, Object> structuredData;
    
    /**
     * 抽取的实体
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ExtractedEntity implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 实体文本
         */
        private String text;
        
        /**
         * 实体类型
         */
        private String type;
        
        /**
         * 实体属性
         */
        private Map<String, Object> attributes;
        
        /**
         * 置信度
         */
        private Double confidence;
    }
    
    /**
     * 抽取的关系
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ExtractedRelation implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 关系类型
         */
        private String relationType;
        
        /**
         * 头实体
         */
        private String headEntity;
        
        /**
         * 尾实体
         */
        private String tailEntity;
        
        /**
         * 关系描述
         */
        private String description;
        
        /**
         * 置信度
         */
        private Double confidence;
    }
    
    /**
     * 抽取的事件
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ExtractedEvent implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 事件类型
         */
        private String eventType;
        
        /**
         * 事件描述
         */
        private String description;
        
        /**
         * 事件参与者
         */
        private List<String> participants;
        
        /**
         * 事件时间
         */
        private String time;
        
        /**
         * 事件地点
         */
        private String location;
        
        /**
         * 置信度
         */
        private Double confidence;
    }
    
    /**
     * 关键事实
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class KeyFact implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 事实描述
         */
        private String description;
        
        /**
         * 事实类型
         */
        private String factType;
        
        /**
         * 重要性评分
         */
        private Double importance;
        
        /**
         * 支持证据
         */
        private List<String> evidence;
    }
}
