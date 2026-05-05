package com.hiforce.order.center.ai.agent.engine.impl;

import com.hiforce.order.center.ai.agent.engine.DocumentUnderstandingEngine;
import com.hiforce.order.center.ai.agent.model.Document;
import com.hiforce.order.center.ai.agent.model.UnderstandingResult;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * 文档理解引擎实现
 */
@Slf4j
@Service
public class DocumentUnderstandingEngineImpl implements DocumentUnderstandingEngine {
    
    // 常见停用词
    private static final Set<String> STOP_WORDS = new HashSet<>(Arrays.asList(
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
        "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
        "自己", "这", "他", "她", "它", "们", "那", "些", "什么", "怎么", "如何"
    ));
    
    // 实体识别模式
    private static final Map<String, Pattern> ENTITY_PATTERNS = new HashMap<>();
    
    static {
        // 日期模式
        ENTITY_PATTERNS.put("DATE", Pattern.compile("\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}[日]?"));
        // 邮箱模式
        ENTITY_PATTERNS.put("EMAIL", Pattern.compile("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"));
        // 电话模式
        ENTITY_PATTERNS.put("PHONE", Pattern.compile("1[3-9]\\d{9}"));
        // 金额模式
        ENTITY_PATTERNS.put("MONEY", Pattern.compile("¥?\\d+(\\.\\d+)?[万元]?"));
    }
    
    @Override
    public UnderstandingResult understand(Document document) {
        log.info("开始理解文档: {}", document.getDocId());
        long startTime = System.currentTimeMillis();
        
        try {
            // 提取主题
            String topic = extractTopic(document);
            
            // 生成摘要
            String summary = generateSummary(document, 200);
            
            // 提取关键词
            List<String> keywords = extractKeywords(document, 10);
            
            // 识别实体
            List<UnderstandingResult.Entity> entities = recognizeEntities(document);
            
            // 分类文档
            String category = classifyDocument(document);
            
            // 分析情感
            UnderstandingResult.SentimentAnalysis sentiment = analyzeSentiment(document);
            
            // 检测语言
            String language = detectLanguage(document.getContent());
            
            // 计算置信度
            Double confidence = calculateConfidence(document, topic, keywords, entities);
            
            UnderstandingResult result = UnderstandingResult.builder()
                .topic(topic)
                .summary(summary)
                .keywords(keywords)
                .entities(entities)
                .category(category)
                .sentiment(sentiment)
                .language(language)
                .confidence(confidence)
                .build();
            
            long executionTime = System.currentTimeMillis() - startTime;
            log.info("文档理解完成，耗时: {}ms", executionTime);
            
            return result;
        } catch (Exception e) {
            log.error("文档理解失败", e);
            throw new RuntimeException("文档理解失败: " + e.getMessage(), e);
        }
    }
    
    @Override
    public String extractTopic(Document document) {
        if (StringUtils.isNotBlank(document.getTitle())) {
            return document.getTitle();
        }
        
        // 从内容中提取主题（取第一段或前100个字符）
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return "未知主题";
        }
        
        // 尝试提取第一句话作为主题
        int endIndex = Math.min(content.length(), 100);
        int sentenceEnd = content.indexOf('。', 0);
        if (sentenceEnd > 0 && sentenceEnd < 100) {
            endIndex = sentenceEnd;
        }
        
        return content.substring(0, endIndex).trim();
    }
    
    @Override
    public String generateSummary(Document document, int maxLength) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return "";
        }
        
        // 简单摘要：提取关键句子
        String[] sentences = content.split("[。！？]");
        if (sentences.length == 0) {
            return content.substring(0, Math.min(content.length(), maxLength));
        }
        
        StringBuilder summary = new StringBuilder();
        for (String sentence : sentences) {
            sentence = sentence.trim();
            if (StringUtils.isBlank(sentence)) {
                continue;
            }
            
            if (summary.length() + sentence.length() > maxLength) {
                break;
            }
            
            summary.append(sentence).append("。");
        }
        
        return summary.toString();
    }
    
    @Override
    public List<String> extractKeywords(Document document, int maxKeywords) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return Collections.emptyList();
        }
        
        // 简单的中文分词和词频统计
        Map<String, Integer> wordFreq = new HashMap<>();
        
        // 使用简单的正则表达式分词（实际项目中应使用专业的中文分词工具）
        String[] words = content.split("[\\s\\p{Punct}]+");
        
        for (String word : words) {
            word = word.trim();
            if (StringUtils.isBlank(word) || word.length() < 2) {
                continue;
            }
            
            // 过滤停用词
            if (STOP_WORDS.contains(word)) {
                continue;
            }
            
            wordFreq.merge(word, 1, Integer::sum);
        }
        
        // 按词频排序，取前maxKeywords个
        return wordFreq.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(maxKeywords)
            .map(Map.Entry::getKey)
            .collect(Collectors.toList());
    }
    
    @Override
    public List<UnderstandingResult.Entity> recognizeEntities(Document document) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return Collections.emptyList();
        }
        
        List<UnderstandingResult.Entity> entities = new ArrayList<>();
        
        // 基于规则识别实体
        for (Map.Entry<String, Pattern> entry : ENTITY_PATTERNS.entrySet()) {
            String entityType = entry.getKey();
            Pattern pattern = entry.getValue();
            Matcher matcher = pattern.matcher(content);
            
            while (matcher.find()) {
                UnderstandingResult.Entity entity = UnderstandingResult.Entity.builder()
                    .text(matcher.group())
                    .type(entityType)
                    .position(matcher.start())
                    .confidence(0.8)
                    .build();
                entities.add(entity);
            }
        }
        
        return entities;
    }
    
    @Override
    public String classifyDocument(Document document) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return "UNKNOWN";
        }
        
        // 简单的基于关键词的分类
        Map<String, String[]> categoryKeywords = new HashMap<>();
        categoryKeywords.put("TECHNOLOGY", new String[]{"技术", "科技", "软件", "硬件", "互联网"});
        categoryKeywords.put("FINANCE", new String[]{"金融", "银行", "投资", "股票", "基金"});
        categoryKeywords.put("HEALTH", new String[]{"健康", "医疗", "医院", "医生", "药物"});
        categoryKeywords.put("EDUCATION", new String[]{"教育", "学校", "学生", "老师", "课程"});
        categoryKeywords.put("BUSINESS", new String[]{"商业", "企业", "公司", "市场", "销售"});
        
        int maxScore = 0;
        String bestCategory = "GENERAL";
        
        for (Map.Entry<String, String[]> entry : categoryKeywords.entrySet()) {
            int score = 0;
            for (String keyword : entry.getValue()) {
                if (content.contains(keyword)) {
                    score++;
                }
            }
            
            if (score > maxScore) {
                maxScore = score;
                bestCategory = entry.getKey();
            }
        }
        
        return bestCategory;
    }
    
    @Override
    public UnderstandingResult.SentimentAnalysis analyzeSentiment(Document document) {
        String content = document.getContent();
        if (StringUtils.isBlank(content)) {
            return UnderstandingResult.SentimentAnalysis.builder()
                .polarity("NEUTRAL")
                .score(0.0)
                .labels(Collections.singletonList("中性"))
                .build();
        }
        
        // 简单的情感分析（基于情感词典）
        Map<String, Double> positiveWords = new HashMap<>();
        positiveWords.put("好", 0.5);
        positiveWords.put("优秀", 0.8);
        positiveWords.put("成功", 0.7);
        positiveWords.put("满意", 0.6);
        
        Map<String, Double> negativeWords = new HashMap<>();
        negativeWords.put("差", -0.5);
        negativeWords.put("失败", -0.7);
        negativeWords.put("问题", -0.4);
        negativeWords.put("错误", -0.6);
        
        double totalScore = 0.0;
        List<String> labels = new ArrayList<>();
        
        for (Map.Entry<String, Double> entry : positiveWords.entrySet()) {
            if (content.contains(entry.getKey())) {
                totalScore += entry.getValue();
                labels.add("积极");
            }
        }
        
        for (Map.Entry<String, Double> entry : negativeWords.entrySet()) {
            if (content.contains(entry.getKey())) {
                totalScore += entry.getValue();
                labels.add("消极");
            }
        }
        
        // 归一化到[-1, 1]区间
        totalScore = Math.max(-1.0, Math.min(1.0, totalScore));
        
        String polarity;
        if (totalScore > 0.2) {
            polarity = "POSITIVE";
        } else if (totalScore < -0.2) {
            polarity = "NEGATIVE";
        } else {
            polarity = "NEUTRAL";
        }
        
        if (labels.isEmpty()) {
            labels.add("中性");
        }
        
        return UnderstandingResult.SentimentAnalysis.builder()
            .polarity(polarity)
            .score(totalScore)
            .labels(labels)
            .build();
    }
    
    /**
     * 检测语言类型
     */
    private String detectLanguage(String content) {
        if (StringUtils.isBlank(content)) {
            return "UNKNOWN";
        }
        
        // 简单的中文字符检测
        int chineseCount = 0;
        for (char c : content.toCharArray()) {
            if (c >= '\u4e00' && c <= '\u9fff') {
                chineseCount++;
            }
        }
        
        double ratio = (double) chineseCount / content.length();
        return ratio > 0.3 ? "ZH" : "EN";
    }
    
    /**
     * 计算置信度
     */
    private Double calculateConfidence(Document document, String topic, 
                                       List<String> keywords, 
                                       List<UnderstandingResult.Entity> entities) {
        double confidence = 0.5; // 基础置信度
        
        // 根据内容长度调整
        int contentLength = document.getContent() != null ? document.getContent().length() : 0;
        if (contentLength > 100) {
            confidence += 0.1;
        }
        if (contentLength > 500) {
            confidence += 0.1;
        }
        
        // 根据关键词数量调整
        if (keywords.size() > 5) {
            confidence += 0.1;
        }
        
        // 根据实体数量调整
        if (entities.size() > 3) {
            confidence += 0.1;
        }
        
        return Math.min(1.0, confidence);
    }
}
