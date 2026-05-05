package com.hiforce.order.center.ai.agent.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * 文档理解结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UnderstandingResult implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * 文档主题
     */
    private String topic;
    
    /**
     * 文档摘要
     */
    private String summary;
    
    /**
     * 关键词列表
     */
    private List<String> keywords;
    
    /**
     * 实体识别结果
     */
    private List<Entity> entities;
    
    /**
     * 文档分类
     */
    private String category;
    
    /**
     * 情感分析结果
     */
    private SentimentAnalysis sentiment;
    
    /**
     * 语言类型
     */
    private String language;
    
    /**
     * 置信度
     */
    private Double confidence;
    
    /**
     * 实体
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Entity implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 实体文本
         */
        private String text;
        
        /**
         * 实体类型（PERSON、ORGANIZATION、LOCATION、DATE等）
         */
        private String type;
        
        /**
         * 实体位置
         */
        private Integer position;
        
        /**
         * 置信度
         */
        private Double confidence;
    }
    
    /**
     * 情感分析
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SentimentAnalysis implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 情感极性（POSITIVE、NEGATIVE、NEUTRAL）
         */
        private String polarity;
        
        /**
         * 情感得分
         */
        private Double score;
        
        /**
         * 情感标签
         */
        private List<String> labels;
    }
}
