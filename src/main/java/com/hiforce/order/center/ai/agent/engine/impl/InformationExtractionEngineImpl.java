package com.hiforce.order.center.ai.agent.engine.impl;

import com.hiforce.order.center.ai.agent.engine.InformationExtractionEngine;
import com.hiforce.order.center.ai.agent.model.Document;
import com.hiforce.order.center.ai.agent.model.ExtractionResult;
import com.hiforce.order.center.ai.agent.service.TextEmbeddingService;
import com.hiforce.order.center.ai.agent.service.VectorDatabaseService;
import com.hiforce.order.center.ai.agent.model.VectorDocument;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * 信息抽取引擎实现
 */
@Slf4j
@Service
public class InformationExtractionEngineImpl implements InformationExtractionEngine {
    
    @Autowired
    private TextEmbeddingService embeddingService;
    
    @Autowired
    private VectorDatabaseService vectorDatabaseService;
    
    // 常见实体模式
    private static final Map<String, Pattern> ENTITY_PATTERNS = new HashMap<>();
    
    // 常见关系模式
    private static final List<RelationPattern> RELATION_PATTERNS = new ArrayList<>();
    
    // 常见事件模式
    private static final List<EventPattern> EVENT_PATTERNS = new ArrayList<>();
    
    static {
        // 初始化实体模式
        ENTITY_PATTERNS.put("PERSON", Pattern.compile("[\\u4e00-\\u9fa5]{2,4}(?:先生|女士|同学|老师|教授)"));
        ENTITY_PATTERNS.put("ORGANIZATION", Pattern.compile("[\\u4e00-\\u9fa5]{2,10}(?:公司|企业|集团|学校|医院|机构)"));
        ENTITY_PATTERNS.put("LOCATION", Pattern.compile("[\\u4e00-\\u9fa5]{2,10}(?:省|市|区|县|镇|村)"));
        ENTITY_PATTERNS.put("DATE", Pattern.compile("\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}[日]?"));
        ENTITY_PATTERNS.put("MONEY", Pattern.compile("(?:约)?[¥$]?\\d+(?:\\.\\d+)?(?:万|亿)?元?"));
        
        // 初始化关系模式
        RELATION_PATTERNS.add(new RelationPattern(
            "WORKS_FOR",
            Pattern.compile("([\\u4e00-\\u9fa5]{2,4})在([\\u4e00-\\u9fa5]{2,10}(?:公司|企业))工作"),
            1, 2
        ));
        
        RELATION_PATTERNS.add(new RelationPattern(
            "LOCATED_IN",
            Pattern.compile("([\\u4e00-\\u9fa5]{2,10}(?:公司|学校))位于([\\u4e00-\\u9fa5]{2,10}(?:省|市))"),
            1, 2
        ));
        
        // 初始化事件模式
        EVENT_PATTERNS.add(new EventPattern(
            "MEETING",
            Pattern.compile("([\\d]{4}[-/年][\\d]{1,2}[-/月][\\d]{1,2}[日]?)召开(?:了)?(.{5,20}?)(?:会议|大会)"),
            "会议"
        ));
        
        EVENT_PATTERNS.add(new EventPattern(
            "LAUNCH",
            Pattern.compile("([\\d]{4}[-/年][\\d]{1,2}[-/月][\\d]{1,2}[日]?)发布(?:了)?(.{5,20}?)"),
            "发布"
        ));
    }
    
    @Override
    public ExtractionResult extract(Document document) {
        log.info("开始抽取文档信息: {}", document.getDocId());
        long startTime = System.currentTimeMillis();
        
        try {
            // 抽取实体
            List<ExtractionResult.ExtractedEntity> entities = extractEntities(document);
            
            // 抽取关系
            List<ExtractionResult.ExtractedRelation> relations = extractRelations(document);
            
            // 抽取事件
            List<ExtractionResult.ExtractedEvent> events = extractEvents(document);
            
            // 抽取关键事实
            List<ExtractionResult.KeyFact> keyFacts = extractKeyFacts(document);
            
            // 构建结构化数据
            Map<String, Object> structuredData = buildStructuredData(entities, relations, events, keyFacts);
            
            ExtractionResult result = ExtractionResult.builder()
                .entities(entities)
                .relations(relations)
                .events(events)
                .keyFacts(keyFacts)
                .structuredData(structuredData)
                .build();
            
            // 存储到向量数据库
            saveToVectorDatabase(document, entities, relations, events, keyFacts);
            
            long executionTime = System.currentTimeMillis() - startTime;
            log.info("信息抽取完成，耗时: {}ms", executionTime);
            
            return result;
        } catch (Exception e) {
            log.error("信息抽取失败", e);
            throw new RuntimeException("信息抽取失败: " + e.getMessage(), e);
        }
    }
    
    @Override
    public List<ExtractionResult.ExtractedEntity> extractEntities(Document document) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return Collections.emptyList();
        }
        
        List<ExtractionResult.ExtractedEntity> entities = new ArrayList<>();
        
        // 基于规则抽取实体
        for (Map.Entry<String, Pattern> entry : ENTITY_PATTERNS.entrySet()) {
            String entityType = entry.getKey();
            Pattern pattern = entry.getValue();
            Matcher matcher = pattern.matcher(content);
            
            while (matcher.find()) {
                ExtractionResult.ExtractedEntity entity = ExtractionResult.ExtractedEntity.builder()
                    .text(matcher.group())
                    .type(entityType)
                    .confidence(0.75)
                    .attributes(new HashMap<>())
                    .build();
                entities.add(entity);
            }
        }
        
        // 去重
        return entities.stream()
            .distinct()
            .collect(Collectors.toList());
    }
    
    @Override
    public List<ExtractionResult.ExtractedRelation> extractRelations(Document document) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return Collections.emptyList();
        }
        
        List<ExtractionResult.ExtractedRelation> relations = new ArrayList<>();
        
        // 基于模式抽取关系
        for (RelationPattern rp : RELATION_PATTERNS) {
            Matcher matcher = rp.pattern.matcher(content);
            
            while (matcher.find()) {
                String headEntity = matcher.group(rp.headGroup);
                String tailEntity = matcher.group(rp.tailGroup);
                
                ExtractionResult.ExtractedRelation relation = ExtractionResult.ExtractedRelation.builder()
                    .relationType(rp.relationType)
                    .headEntity(headEntity)
                    .tailEntity(tailEntity)
                    .description(headEntity + " " + getRelationDescription(rp.relationType) + " " + tailEntity)
                    .confidence(0.7)
                    .build();
                
                relations.add(relation);
            }
        }
        
        return relations;
    }
    
    @Override
    public List<ExtractionResult.ExtractedEvent> extractEvents(Document document) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return Collections.emptyList();
        }
        
        List<ExtractionResult.ExtractedEvent> events = new ArrayList<>();
        
        // 基于模式抽取事件
        for (EventPattern ep : EVENT_PATTERNS) {
            Matcher matcher = ep.pattern.matcher(content);
            
            while (matcher.find()) {
                String time = matcher.group(1);
                String description = matcher.group(2);
                
                ExtractionResult.ExtractedEvent event = ExtractionResult.ExtractedEvent.builder()
                    .eventType(ep.eventType)
                    .description(description)
                    .time(time)
                    .participants(Collections.emptyList())
                    .location("")
                    .confidence(0.65)
                    .build();
                
                events.add(event);
            }
        }
        
        return events;
    }
    
    @Override
    public List<ExtractionResult.KeyFact> extractKeyFacts(Document document) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return Collections.emptyList();
        }
        
        List<ExtractionResult.KeyFact> keyFacts = new ArrayList<>();
        
        // 提取包含关键信息的句子
        String[] sentences = content.split("[。！？]");
        
        int index = 0;
        for (String sentence : sentences) {
            sentence = sentence.trim();
            if (StringUtils.isBlank(sentence) || sentence.length() < 10) {
                continue;
            }
            
            // 判断是否为关键事实（简单规则：包含数字、日期或特定关键词）
            double importance = calculateFactImportance(sentence);
            
            if (importance > 0.5) {
                ExtractionResult.KeyFact fact = ExtractionResult.KeyFact.builder()
                    .description(sentence)
                    .factType(determineFactType(sentence))
                    .importance(importance)
                    .evidence(Collections.singletonList("原文第" + (index + 1) + "句"))
                    .build();
                
                keyFacts.add(fact);
            }
            
            index++;
        }
        
        // 按重要性排序
        return keyFacts.stream()
            .sorted(Comparator.comparing(ExtractionResult.KeyFact::getImportance).reversed())
            .limit(10)
            .collect(Collectors.toList());
    }
    
    /**
     * 构建结构化数据
     */
    private Map<String, Object> buildStructuredData(
            List<ExtractionResult.ExtractedEntity> entities,
            List<ExtractionResult.ExtractedRelation> relations,
            List<ExtractionResult.ExtractedEvent> events,
            List<ExtractionResult.KeyFact> keyFacts) {
        
        Map<String, Object> structuredData = new HashMap<>();
        
        // 按类型分组实体
        Map<String, List<String>> entitiesByType = entities.stream()
            .collect(Collectors.groupingBy(
                ExtractionResult.ExtractedEntity::getType,
                Collectors.mapping(ExtractionResult.ExtractedEntity::getText, Collectors.toList())
            ));
        
        structuredData.put("entities", entitiesByType);
        structuredData.put("relations", relations.size());
        structuredData.put("events", events.size());
        structuredData.put("keyFacts", keyFacts.size());
        
        return structuredData;
    }
    
    /**
     * 存储抽取结果到向量数据库
     */
    private void saveToVectorDatabase(Document document,
                                      List<ExtractionResult.ExtractedEntity> entities,
                                      List<ExtractionResult.ExtractedRelation> relations,
                                      List<ExtractionResult.ExtractedEvent> events,
                                      List<ExtractionResult.KeyFact> keyFacts) {
        try {
            List<VectorDocument> vectorDocs = new ArrayList<>();
            Date now = new Date();
            
            // 1. 存储完整文本向量
            if (StringUtils.isNotBlank(document.getContent())) {
                List<Float> contentVector = embeddingService.embed(document.getContent());
                
                Map<String, Object> metadata = new HashMap<>();
                metadata.put("docType", document.getDocType());
                metadata.put("source", document.getSource());
                metadata.put("entityCount", entities.size());
                metadata.put("relationCount", relations.size());
                metadata.put("eventCount", events.size());
                metadata.put("keyFactCount", keyFacts.size());
                
                VectorDocument vectorDoc = VectorDocument.builder()
                    .vectorId(document.getDocId() + "_full")
                    .docId(document.getDocId())
                    .title(document.getTitle())
                    .content(document.getContent())
                    .contentType("FULL_TEXT")
                    .vector(contentVector)
                    .dimension(contentVector.size())
                    .metadata(metadata)
                    .createTime(now)
                    .updateTime(now)
                    .build();
                
                vectorDocs.add(vectorDoc);
            }
            
            // 2. 存储实体向量
            for (ExtractionResult.ExtractedEntity entity : entities) {
                List<Float> entityVector = embeddingService.embed(entity.getText());
                
                Map<String, Object> metadata = new HashMap<>();
                metadata.put("entityType", entity.getType());
                metadata.put("confidence", entity.getConfidence());
                
                VectorDocument vectorDoc = VectorDocument.builder()
                    .vectorId(document.getDocId() + "_entity_" + entity.getText())
                    .docId(document.getDocId())
                    .title(document.getTitle())
                    .content(entity.getText())
                    .contentType("ENTITY")
                    .vector(entityVector)
                    .dimension(entityVector.size())
                    .metadata(metadata)
                    .createTime(now)
                    .updateTime(now)
                    .build();
                
                vectorDocs.add(vectorDoc);
            }
            
            // 3. 存储关系向量
            for (ExtractionResult.ExtractedRelation relation : relations) {
                String relationText = relation.getDescription();
                List<Float> relationVector = embeddingService.embed(relationText);
                
                Map<String, Object> metadata = new HashMap<>();
                metadata.put("relationType", relation.getRelationType());
                metadata.put("headEntity", relation.getHeadEntity());
                metadata.put("tailEntity", relation.getTailEntity());
                metadata.put("confidence", relation.getConfidence());
                
                VectorDocument vectorDoc = VectorDocument.builder()
                    .vectorId(document.getDocId() + "_relation_" + relation.getHeadEntity() + "_" + relation.getTailEntity())
                    .docId(document.getDocId())
                    .title(document.getTitle())
                    .content(relationText)
                    .contentType("RELATION")
                    .vector(relationVector)
                    .dimension(relationVector.size())
                    .metadata(metadata)
                    .createTime(now)
                    .updateTime(now)
                    .build();
                
                vectorDocs.add(vectorDoc);
            }
            
            // 4. 存储事件向量
            for (ExtractionResult.ExtractedEvent event : events) {
                String eventText = event.getDescription();
                List<Float> eventVector = embeddingService.embed(eventText);
                
                Map<String, Object> metadata = new HashMap<>();
                metadata.put("eventType", event.getEventType());
                metadata.put("time", event.getTime());
                metadata.put("location", event.getLocation());
                metadata.put("confidence", event.getConfidence());
                
                VectorDocument vectorDoc = VectorDocument.builder()
                    .vectorId(document.getDocId() + "_event_" + event.getDescription().substring(0, Math.min(20, event.getDescription().length())))
                    .docId(document.getDocId())
                    .title(document.getTitle())
                    .content(eventText)
                    .contentType("EVENT")
                    .vector(eventVector)
                    .dimension(eventVector.size())
                    .metadata(metadata)
                    .createTime(now)
                    .updateTime(now)
                    .build();
                
                vectorDocs.add(vectorDoc);
            }
            
            // 5. 存储关键事实向量
            for (ExtractionResult.KeyFact fact : keyFacts) {
                List<Float> factVector = embeddingService.embed(fact.getDescription());
                
                Map<String, Object> metadata = new HashMap<>();
                metadata.put("factType", fact.getFactType());
                metadata.put("importance", fact.getImportance());
                
                VectorDocument vectorDoc = VectorDocument.builder()
                    .vectorId(document.getDocId() + "_fact_" + fact.getDescription().substring(0, Math.min(20, fact.getDescription().length())))
                    .docId(document.getDocId())
                    .title(document.getTitle())
                    .content(fact.getDescription())
                    .contentType("KEY_FACT")
                    .vector(factVector)
                    .dimension(factVector.size())
                    .metadata(metadata)
                    .createTime(now)
                    .updateTime(now)
                    .build();
                
                vectorDocs.add(vectorDoc);
            }
            
            // 批量插入向量数据库
            if (!vectorDocs.isEmpty()) {
                int successCount = vectorDatabaseService.batchInsert(vectorDocs);
                log.info("向量数据存储完成，文档ID: {}, 总数: {}, 成功: {}", 
                    document.getDocId(), vectorDocs.size(), successCount);
            }
            
        } catch (Exception e) {
            log.error("存储向量数据失败，文档ID: {}", document.getDocId(), e);
            // 不抛出异常，避免影响主流程
        }
    }
    
    /**
     * 计算事实重要性
     */
    private double calculateFactImportance(String sentence) {
        double importance = 0.3; // 基础重要性
        
        // 包含数字
        if (sentence.matches(".*\\d+.*")) {
            importance += 0.2;
        }
        
        // 包含日期
        if (sentence.matches(".*\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}.*")) {
            importance += 0.2;
        }
        
        // 包含关键词
        String[] importantKeywords = {"重要", "关键", "核心", "主要", "首先", "总结"};
        for (String keyword : importantKeywords) {
            if (sentence.contains(keyword)) {
                importance += 0.15;
                break;
            }
        }
        
        return Math.min(1.0, importance);
    }
    
    /**
     * 确定事实类型
     */
    private String determineFactType(String sentence) {
        if (sentence.matches(".*\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}.*")) {
            return "TEMPORAL";
        }
        if (sentence.matches(".*\\d+.*")) {
            return "STATISTICAL";
        }
        if (sentence.contains("重要") || sentence.contains("关键")) {
            return "KEY_POINT";
        }
        return "GENERAL";
    }
    
    /**
     * 获取关系描述
     */
    private String getRelationDescription(String relationType) {
        switch (relationType) {
            case "WORKS_FOR":
                return "就职于";
            case "LOCATED_IN":
                return "位于";
            default:
                return "关联";
        }
    }
    
    /**
     * 关系模式
     */
    private static class RelationPattern {
        String relationType;
        Pattern pattern;
        int headGroup;
        int tailGroup;
        
        RelationPattern(String relationType, Pattern pattern, int headGroup, int tailGroup) {
            this.relationType = relationType;
            this.pattern = pattern;
            this.headGroup = headGroup;
            this.tailGroup = tailGroup;
        }
    }
    
    /**
     * 事件模式
     */
    private static class EventPattern {
        String eventType;
        Pattern pattern;
        String defaultDescription;
        
        EventPattern(String eventType, Pattern pattern, String defaultDescription) {
            this.eventType = eventType;
            this.pattern = pattern;
            this.defaultDescription = defaultDescription;
        }
    }
}
