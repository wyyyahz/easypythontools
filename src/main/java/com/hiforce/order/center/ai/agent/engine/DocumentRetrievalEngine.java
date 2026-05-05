package com.hiforce.order.center.ai.agent.engine;

import com.hiforce.order.center.ai.agent.model.Document;
import com.hiforce.order.center.ai.agent.model.RetrievalResult;

import java.util.List;

/**
 * 文档检索引擎接口
 */
public interface DocumentRetrievalEngine {
    
    /**
     * 索引文档
     *
     * @param document 文档对象
     */
    void indexDocument(Document document);
    
    /**
     * 批量索引文档
     *
     * @param documents 文档列表
     */
    void indexDocuments(List<Document> documents);
    
    /**
     * 检索文档
     *
     * @param query 查询语句
     * @param maxResults 最大返回结果数
     * @return 检索结果
     */
    RetrievalResult search(String query, int maxResults);
    
    /**
     * 相似度检索
     *
     * @param document 文档对象
     * @param maxResults 最大返回结果数
     * @return 检索结果
     */
    RetrievalResult similaritySearch(Document document, int maxResults);
    
    /**
     * 删除文档索引
     *
     * @param docId 文档ID
     */
    void deleteDocument(String docId);
    
    /**
     * 清空索引
     */
    void clearIndex();
}
