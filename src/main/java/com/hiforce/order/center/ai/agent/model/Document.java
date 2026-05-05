package com.hiforce.order.center.ai.agent.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Date;
import java.util.List;
import java.util.Map;

/**
 * 文档模型
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Document implements Serializable {
    
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
     * 文档内容
     */
    private String content;
    
    /**
     * 文档类型（PDF、WORD、TXT、HTML等）
     */
    private String docType;
    
    /**
     * 文档来源
     */
    private String source;
    
    /**
     * 文档元数据
     */
    private Map<String, Object> metadata;
    
    /**
     * 文档分段列表
     */
    private List<DocumentSegment> segments;
    
    /**
     * 创建时间
     */
    private Date createTime;
    
    /**
     * 更新时间
     */
    private Date updateTime;
    
    /**
     * 文档分段
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DocumentSegment implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 分段ID
         */
        private String segmentId;
        
        /**
         * 分段内容
         */
        private String content;
        
        /**
         * 分段索引
         */
        private Integer index;
        
        /**
         * 分段元数据
         */
        private Map<String, Object> metadata;
    }
}
