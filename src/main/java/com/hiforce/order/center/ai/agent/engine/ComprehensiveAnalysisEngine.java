package com.hiforce.order.center.ai.agent.engine;

import com.hiforce.order.center.ai.agent.model.*;

/**
 * 综合分析引擎接口
 */
public interface ComprehensiveAnalysisEngine {
    
    /**
     * 综合分析文档
     *
     * @param document 文档对象
     * @param understandingResult 理解结果
     * @param extractionResult 抽取结果
     * @return 分析结果
     */
    AnalysisResult analyze(Document document, 
                          UnderstandingResult understandingResult,
                          ExtractionResult extractionResult);
    
    /**
     * 生成分析摘要
     *
     * @param document 文档对象
     * @param understandingResult 理解结果
     * @return 分析摘要
     */
    String generateAnalysisSummary(Document document, UnderstandingResult understandingResult);
    
    /**
     * 发现关键洞察
     *
     * @param understandingResult 理解结果
     * @param extractionResult 抽取结果
     * @return 洞察列表
     */
    java.util.List<AnalysisResult.Insight> discoverInsights(UnderstandingResult understandingResult,
                                                            ExtractionResult extractionResult);
    
    /**
     * 评估质量
     *
     * @param document 文档对象
     * @return 质量评分
     */
    AnalysisResult.QualityScore evaluateQuality(Document document);
    
    /**
     * 评估风险
     *
     * @param extractionResult 抽取结果
     * @return 风险评估
     */
    AnalysisResult.RiskAssessment assessRisk(ExtractionResult extractionResult);
}
