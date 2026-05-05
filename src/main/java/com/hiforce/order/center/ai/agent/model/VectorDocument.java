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
 * 向量文档模型
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class VectorDocument implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * 向量ID（与文档ID对应）
     */
    private String vectorId;
    
    /**
     * 原始文档ID
     */
    private String docId;
    
    /**
     * 文档标题
     */
    private String title;
    
    /**
     * 文档内容或片段
     */
    private String content;
    
    /**
     * 内容类型（FULL_TEXT、SUMMARY、ENTITY、RELATION、EVENT、KEY_FACT）
     */
    private String contentType;
    
    /**
     * 向量数据
     */
    private List<Float> vector;
    
    /**
     * 向量维度
     */
    private Integer dimension;
    
    /**
     * 元数据（包含实体、关系等结构化信息）
     */
    private Map<String, Object> metadata;
    
    /**
     * 创建时间
     */
    private Date createTime;
    
    /**
     * 更新时间
     */
    private Date updateTime;
}
