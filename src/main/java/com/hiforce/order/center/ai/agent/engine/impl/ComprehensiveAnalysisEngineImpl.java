package com.hiforce.order.center.ai.agent.engine.impl;

import com.hiforce.order.center.ai.agent.engine.ComprehensiveAnalysisEngine;
import com.hiforce.order.center.ai.agent.model.*;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 综合分析引擎实现
 */
@Slf4j
@Service
public class ComprehensiveAnalysisEngineImpl implements ComprehensiveAnalysisEngine {
    
    @Override
    public AnalysisResult analyze(Document document,
                                  UnderstandingResult understandingResult,
                                  ExtractionResult extractionResult) {
        log.info("开始综合分析文档: {}", document.getDocId());
        long startTime = System.currentTimeMillis();
        
        try {
            // 生成分析摘要
            String summary = generateAnalysisSummary(document, understandingResult);
            
            // 发现关键洞察
            List<AnalysisResult.Insight> insights = discoverInsights(understandingResult, extractionResult);
            
            // 提取主要发现
            List<AnalysisResult.Finding> findings = extractFindings(understandingResult, extractionResult);
            
            // 趋势分析
            AnalysisResult.TrendAnalysis trendAnalysis = analyzeTrends(document, extractionResult);
            
            // 风险评估
            AnalysisResult.RiskAssessment riskAssessment = assessRisk(extractionResult);
            
            // 质量评分
            AnalysisResult.QualityScore qualityScore = evaluateQuality(document);
            
            // 附加信息
            Map<String, Object> additionalInfo = buildAdditionalInfo(understandingResult, extractionResult);
            
            AnalysisResult result = AnalysisResult.builder()
                .summary(summary)
                .findings(findings)
                .insights(insights)
                .trendAnalysis(trendAnalysis)
                .riskAssessment(riskAssessment)
                .qualityScore(qualityScore)
                .additionalInfo(additionalInfo)
                .build();
            
            long executionTime = System.currentTimeMillis() - startTime;
            log.info("综合分析完成，耗时: {}ms", executionTime);
            
            return result;
        } catch (Exception e) {
            log.error("综合分析失败", e);
            throw new RuntimeException("综合分析失败: " + e.getMessage(), e);
        }
    }
    
    @Override
    public String generateAnalysisSummary(Document document, UnderstandingResult understandingResult) {
        StringBuilder summary = new StringBuilder();
        
        // 文档主题
        if (StringUtils.isNotBlank(understandingResult.getTopic())) {
            summary.append("本文档主题为：").append(understandingResult.getTopic()).append("。");
        }
        
        // 文档分类
        if (StringUtils.isNotBlank(understandingResult.getCategory())) {
            summary.append("文档类别为：").append(understandingResult.getCategory()).append("。");
        }
        
        // 关键词
        if (understandingResult.getKeywords() != null && !understandingResult.getKeywords().isEmpty()) {
            summary.append("主要关键词包括：");
            summary.append(String.join("、", understandingResult.getKeywords().subList(0, 
                Math.min(5, understandingResult.getKeywords().size()))));
            summary.append("。");
        }
        
        // 情感倾向
        if (understandingResult.getSentiment() != null) {
            summary.append("整体情感倾向为：").append(understandingResult.getSentiment().getPolarity());
            summary.append("。");
        }
        
        return summary.toString();
    }
    
    @Override
    public List<AnalysisResult.Insight> discoverInsights(UnderstandingResult understandingResult,
                                                         ExtractionResult extractionResult) {
        List<AnalysisResult.Insight> insights = new ArrayList<>();
        
        // 基于实体发现的洞察
        if (extractionResult.getEntities() != null && !extractionResult.getEntities().isEmpty()) {
            Map<String, Long> entityTypeCount = extractionResult.getEntities().stream()
                .collect(Collectors.groupingBy(
                    ExtractionResult.ExtractedEntity::getType,
                    Collectors.counting()
                ));
            
            for (Map.Entry<String, Long> entry : entityTypeCount.entrySet()) {
                if (entry.getValue() > 2) {
                    AnalysisResult.Insight insight = AnalysisResult.Insight.builder()
                        .title(entry.getKey() + "实体分析")
                        .description("文档中包含" + entry.getValue() + "个" + entry.getKey() + "类型实体")
                        .recommendations(Arrays.asList(
                            "进一步分析这些实体之间的关系",
                            "验证实体的准确性和完整性"
                        ))
                        .confidence(0.7)
                        .build();
                    insights.add(insight);
                }
            }
        }
        
        // 基于情感的洞察
        if (understandingResult.getSentiment() != null) {
            String polarity = understandingResult.getSentiment().getPolarity();
            if ("NEGATIVE".equals(polarity)) {
                AnalysisResult.Insight insight = AnalysisResult.Insight.builder()
                    .title("负面情感检测")
                    .description("文档表现出负面情感倾向")
                    .recommendations(Arrays.asList(
                        "关注文档中提到的问题",
                        "制定改进措施"
                    ))
                    .confidence(0.65)
                    .build();
                insights.add(insight);
            }
        }
        
        // 基于关键事实的洞察
        if (extractionResult.getKeyFacts() != null && !extractionResult.getKeyFacts().isEmpty()) {
            List<ExtractionResult.KeyFact> highImportanceFacts = extractionResult.getKeyFacts().stream()
                .filter(fact -> fact.getImportance() > 0.7)
                .collect(Collectors.toList());
            
            if (!highImportanceFacts.isEmpty()) {
                AnalysisResult.Insight insight = AnalysisResult.Insight.builder()
                    .title("关键事实发现")
                    .description("发现" + highImportanceFacts.size() + "个高重要性事实")
                    .recommendations(Arrays.asList(
                        "重点关注这些关键事实",
                        "验证实据的准确性"
                    ))
                    .confidence(0.75)
                    .build();
                insights.add(insight);
            }
        }
        
        return insights;
    }
    
    @Override
    public AnalysisResult.QualityScore evaluateQuality(Document document) {
        String content = document.getContent();
        
        // 完整性评分
        double completeness = calculateCompleteness(content);
        
        // 准确性评分（基于置信度）
        double accuracy = 0.75; // 默认值
        
        // 一致性评分
        double consistency = calculateConsistency(content);
        
        // 可读性评分
        double readability = calculateReadability(content);
        
        // 综合评分
        double overall = (completeness + accuracy + consistency + readability) / 4.0;
        
        return AnalysisResult.QualityScore.builder()
            .completeness(completeness)
            .accuracy(accuracy)
            .consistency(consistency)
            .readability(readability)
            .overall(overall)
            .build();
    }
    
    @Override
    public AnalysisResult.RiskAssessment assessRisk(ExtractionResult extractionResult) {
        List<AnalysisResult.Risk> risks = new ArrayList<>();
        
        // 基于抽取结果评估风险
        if (extractionResult.getEvents() != null) {
            for (ExtractionResult.ExtractedEvent event : extractionResult.getEvents()) {
                if ("LAUNCH".equals(event.getEventType()) || "MEETING".equals(event.getEventType())) {
                    AnalysisResult.Risk risk = AnalysisResult.Risk.builder()
                        .description("事件相关风险：" + event.getDescription())
                        .riskLevel("MEDIUM")
                        .impact(0.5)
                        .probability(0.4)
                        .mitigationSuggestions(Arrays.asList(
                            "跟踪事件进展",
                            "准备应对方案"
                        ))
                        .build();
                    risks.add(risk);
                }
            }
        }
        
        // 确定整体风险等级
        String overallRiskLevel = determineOverallRiskLevel(risks);
        
        return AnalysisResult.RiskAssessment.builder()
            .risks(risks)
            .overallRiskLevel(overallRiskLevel)
            .build();
    }
    
    /**
     * 提取主要发现
     */
    private List<AnalysisResult.Finding> extractFindings(UnderstandingResult understandingResult,
                                                         ExtractionResult extractionResult) {
        List<AnalysisResult.Finding> findings = new ArrayList<>();
        
        // 基于实体数量的发现
        if (extractionResult.getEntities() != null && extractionResult.getEntities().size() > 5) {
            AnalysisResult.Finding finding = AnalysisResult.Finding.builder()
                .title("丰富的实体信息")
                .description("文档包含大量实体信息，共" + extractionResult.getEntities().size() + "个")
                .importanceLevel("MEDIUM")
                .evidence(Arrays.asList("实体数量统计"))
                .build();
            findings.add(finding);
        }
        
        // 基于关系的发现
        if (extractionResult.getRelations() != null && !extractionResult.getRelations().isEmpty()) {
            AnalysisResult.Finding finding = AnalysisResult.Finding.builder()
                .title("发现实体关系")
                .description("识别出" + extractionResult.getRelations().size() + "个实体关系")
                .importanceLevel("HIGH")
                .evidence(Arrays.asList("关系抽取结果"))
                .build();
            findings.add(finding);
        }
        
        // 基于情感的发现
        if (understandingResult.getSentiment() != null && 
            "NEGATIVE".equals(understandingResult.getSentiment().getPolarity())) {
            AnalysisResult.Finding finding = AnalysisResult.Finding.builder()
                .title("负面情感 detected")
                .description("文档表现出负面情感倾向，得分：" + understandingResult.getSentiment().getScore())
                .importanceLevel("HIGH")
                .evidence(Arrays.asList("情感分析结果"))
                .build();
            findings.add(finding);
        }
        
        return findings;
    }
    
    /**
     * 趋势分析
     */
    private AnalysisResult.TrendAnalysis analyzeTrends(Document document, ExtractionResult extractionResult) {
        // 简单的趋势分析实现
        return AnalysisResult.TrendAnalysis.builder()
            .description("基于当前文档内容的趋势分析")
            .direction("STABLE")
            .strength(0.5)
            .keyTimePoints(Collections.emptyList())
            .build();
    }
    
    /**
     * 构建附加信息
     */
    private Map<String, Object> buildAdditionalInfo(UnderstandingResult understandingResult,
                                                    ExtractionResult extractionResult) {
        Map<String, Object> additionalInfo = new HashMap<>();
        
        additionalInfo.put("topic", understandingResult.getTopic());
        additionalInfo.put("category", understandingResult.getCategory());
        additionalInfo.put("language", understandingResult.getLanguage());
        additionalInfo.put("entityCount", extractionResult.getEntities() != null ? 
            extractionResult.getEntities().size() : 0);
        additionalInfo.put("relationCount", extractionResult.getRelations() != null ? 
            extractionResult.getRelations().size() : 0);
        additionalInfo.put("eventCount", extractionResult.getEvents() != null ? 
            extractionResult.getEvents().size() : 0);
        
        return additionalInfo;
    }
    
    /**
     * 计算完整性
     */
    private double calculateCompleteness(String content) {
        if (StringUtils.isBlank(content)) {
            return 0.0;
        }
        
        int length = content.length();
        if (length < 100) {
            return 0.3;
        } else if (length < 500) {
            return 0.6;
        } else if (length < 1000) {
            return 0.8;
        } else {
            return 1.0;
        }
    }
    
    /**
     * 计算一致性
     */
    private double calculateConsistency(String content) {
        if (StringUtils.isBlank(content)) {
            return 0.0;
        }
        
        // 简单的一致性检查：段落之间的连贯性
        String[] paragraphs = content.split("\n\n");
        if (paragraphs.length <= 1) {
            return 0.7;
        }
        
        // 检查是否有重复内容
        Set<String> uniqueParagraphs = new HashSet<>(Arrays.asList(paragraphs));
        double ratio = (double) uniqueParagraphs.size() / paragraphs.length;
        
        return ratio * 0.8;
    }
    
    /**
     * 计算可读性
     */
    private double calculateReadability(String content) {
        if (StringUtils.isBlank(content)) {
            return 0.0;
        }
        
        // 基于句子长度的可读性评估
        String[] sentences = content.split("[。！？]");
        if (sentences.length == 0) {
            return 0.5;
        }
        
        double avgSentenceLength = Arrays.stream(sentences)
            .mapToDouble(String::length)
            .average()
            .orElse(0);
        
        // 理想句子长度在20-50字符之间
        if (avgSentenceLength >= 20 && avgSentenceLength <= 50) {
            return 0.9;
        } else if (avgSentenceLength < 20) {
            return 0.7;
        } else {
            return 0.6;
        }
    }
    
    /**
     * 确定整体风险等级
     */
    private String determineOverallRiskLevel(List<AnalysisResult.Risk> risks) {
        if (risks.isEmpty()) {
            return "LOW";
        }
        
        boolean hasHighRisk = risks.stream()
            .anyMatch(risk -> "HIGH".equals(risk.getRiskLevel()));
        
        if (hasHighRisk) {
            return "HIGH";
        }
        
        boolean hasMediumRisk = risks.stream()
            .anyMatch(risk -> "MEDIUM".equals(risk.getRiskLevel()));
        
        return hasMediumRisk ? "MEDIUM" : "LOW";
    }
}
