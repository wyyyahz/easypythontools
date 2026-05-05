package com.hiforce.order.center.ai.agent.engine.impl;

import com.hiforce.order.center.ai.agent.engine.DocumentRetrievalEngine;
import com.hiforce.order.center.ai.agent.model.Document;
import com.hiforce.order.center.ai.agent.model.RetrievalResult;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * 文档检索引擎实现（基于内存的简单实现）
 */
@Slf4j
@Service
public class DocumentRetrievalEngineImpl implements DocumentRetrievalEngine {
    
    // 文档索引存储
    private final Map<String, Document> documentIndex = new ConcurrentHashMap<>();
    
    // 倒排索引：关键词 -> 文档ID列表
    private final Map<String, Set<String>> invertedIndex = new ConcurrentHashMap<>();
    
    @Override
    public void indexDocument(Document document) {
        log.info("索引文档: {}", document.getDocId());
        
        // 添加到文档索引
        documentIndex.put(document.getDocId(), document);
        
        // 构建倒排索引
        buildInvertedIndex(document);
        
        log.info("文档索引完成: {}", document.getDocId());
    }
    
    @Override
    public void indexDocuments(List<Document> documents) {
        log.info("批量索引文档，数量: {}", documents.size());
        for (Document document : documents) {
            indexDocument(document);
        }
        log.info("批量索引完成");
    }
    
    @Override
    public RetrievalResult search(String query, int maxResults) {
        log.info("执行检索，查询: {}, 最大结果数: {}", query, maxResults);
        long startTime = System.currentTimeMillis();
        
        if (StringUtils.isBlank(query)) {
            return RetrievalResult.builder()
                .query(query)
                .documents(Collections.emptyList())
                .totalCount(0)
                .retrievalTime(0L)
                .build();
        }
        
        // 计算每个文档的相关性得分
        Map<String, Double> docScores = new HashMap<>();
        
        // 分词查询
        String[] queryTerms = query.split("[\\s\\p{Punct}]+");
        
        for (String term : queryTerms) {
            term = term.toLowerCase().trim();
            if (StringUtils.isBlank(term)) {
                continue;
            }
            
            // 查找包含该词的文档
            Set<String> matchedDocs = invertedIndex.getOrDefault(term, Collections.emptySet());
            
            for (String docId : matchedDocs) {
                docScores.merge(docId, 1.0, Double::sum);
            }
        }
        
        // 按得分排序
        List<RetrievalResult.RetrievedDocument> results = docScores.entrySet().stream()
            .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
            .limit(maxResults)
            .map(entry -> {
                String docId = entry.getKey();
                Document doc = documentIndex.get(docId);
                
                if (doc == null) {
                    return null;
                }
                
                // 提取相关片段
                String snippet = extractRelevantSnippet(doc.getContent(), query);
                
                return RetrievalResult.RetrievedDocument.builder()
                    .docId(docId)
                    .title(doc.getTitle())
                    .snippet(snippet)
                    .relevanceScore(entry.getValue())
                    .source(doc.getSource())
                    .build();
            })
            .filter(Objects::nonNull)
            .collect(Collectors.toList());
        
        long retrievalTime = System.currentTimeMillis() - startTime;
        
        RetrievalResult result = RetrievalResult.builder()
            .query(query)
            .documents(results)
            .totalCount(results.size())
            .retrievalTime(retrievalTime)
            .build();
        
        log.info("检索完成，找到 {} 个结果，耗时: {}ms", results.size(), retrievalTime);
        
        return result;
    }
    
    @Override
    public RetrievalResult similaritySearch(Document document, int maxResults) {
        log.info("执行相似度检索");
        
        if (document == null || StringUtils.isBlank(document.getContent())) {
            return RetrievalResult.builder()
                .query("similarity_search")
                .documents(Collections.emptyList())
                .totalCount(0)
                .retrievalTime(0L)
                .build();
        }
        
        // 使用文档内容作为查询
        String query = document.getContent().substring(0, Math.min(200, document.getContent().length()));
        return search(query, maxResults);
    }
    
    @Override
    public void deleteDocument(String docId) {
        log.info("删除文档索引: {}", docId);
        
        Document document = documentIndex.remove(docId);
        if (document != null) {
            // 从倒排索引中移除
            removeFromInvertedIndex(docId, document);
        }
        
        log.info("文档索引删除完成: {}", docId);
    }
    
    @Override
    public void clearIndex() {
        log.info("清空所有索引");
        documentIndex.clear();
        invertedIndex.clear();
        log.info("索引清空完成");
    }
    
    /**
     * 构建倒排索引
     */
    private void buildInvertedIndex(Document document) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return;
        }
        
        // 简单的分词
        String[] words = content.toLowerCase().split("[\\s\\p{Punct}]+");
        
        for (String word : words) {
            if (StringUtils.isBlank(word) || word.length() < 2) {
                continue;
            }
            
            invertedIndex.computeIfAbsent(word, k -> ConcurrentHashMap.newKeySet())
                .add(document.getDocId());
        }
    }
    
    /**
     * 从倒排索引中移除
     */
    private void removeFromInvertedIndex(String docId, Document document) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return;
        }
        
        String[] words = content.toLowerCase().split("[\\s\\p{Punct}]+");
        
        for (String word : words) {
            Set<String> docIds = invertedIndex.get(word);
            if (docIds != null) {
                docIds.remove(docId);
                if (docIds.isEmpty()) {
                    invertedIndex.remove(word);
                }
            }
        }
    }
    
    /**
     * 提取相关片段
     */
    private String extractRelevantSnippet(String content, String query) {
        if (StringUtils.isBlank(content)) {
            return "";
        }
        
        // 查找查询词在内容中的位置
        int maxLength = 200;
        int startIndex = 0;
        
        String lowerContent = content.toLowerCase();
        String lowerQuery = query.toLowerCase();
        
        int queryPos = lowerContent.indexOf(lowerQuery);
        if (queryPos >= 0) {
            // 以查询词为中心提取片段
            startIndex = Math.max(0, queryPos - 50);
        }
        
        int endIndex = Math.min(startIndex + maxLength, content.length());
        String snippet = content.substring(startIndex, endIndex);
        
        // 添加省略号
        if (startIndex > 0) {
            snippet = "..." + snippet;
        }
        if (endIndex < content.length()) {
            snippet = snippet + "...";
        }
        
        return snippet;
    }
}
