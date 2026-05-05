package com.hiforce.order.center.ai.agent.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.List;

/**
 * 文档检索结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RetrievalResult implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * 查询语句
     */
    private String query;
    
    /**
     * 检索到的文档列表
     */
    private List<RetrievedDocument> documents;
    
    /**
     * 检索总数
     */
    private Integer totalCount;
    
    /**
     * 检索耗时（毫秒）
     */
    private Long retrievalTime;
    
    /**
     * 检索到的文档
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RetrievedDocument implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 文档ID
         */
        private String docId;
        
        /**
         * 文档标题
         */
        private String title;
        
        /**
         * 文档片段
         */
        private String snippet;
        
        /**
         * 相关性得分
         */
        private Double relevanceScore;
        
        /**
         * 匹配位置
         */
        private List<Integer> matchPositions;
        
        /**
         * 文档来源
         */
        private String source;
    }
}
