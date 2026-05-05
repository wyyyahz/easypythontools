package com.hiforce.order.center.ai.agent.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * 综合分析结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisResult implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * 分析摘要
     */
    private String summary;
    
    /**
     * 主要发现
     */
    private List<Finding> findings;
    
    /**
     * 洞察建议
     */
    private List<Insight> insights;
    
    /**
     * 趋势分析
     */
    private TrendAnalysis trendAnalysis;
    
    /**
     * 风险评估
     */
    private RiskAssessment riskAssessment;
    
    /**
     * 质量评分
     */
    private QualityScore qualityScore;
    
    /**
     * 附加信息
     */
    private Map<String, Object> additionalInfo;
    
    /**
     * 发现项
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Finding implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 发现标题
         */
        private String title;
        
        /**
         * 发现描述
         */
        private String description;
        
        /**
         * 重要性级别（HIGH、MEDIUM、LOW）
         */
        private String importanceLevel;
        
        /**
         * 支持证据
         */
        private List<String> evidence;
    }
    
    /**
     * 洞察项
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Insight implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 洞察标题
         */
        private String title;
        
        /**
         * 洞察描述
         */
        private String description;
        
        /**
         * 行动建议
         */
        private List<String> recommendations;
        
        /**
         * 置信度
         */
        private Double confidence;
    }
    
    /**
     * 趋势分析
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TrendAnalysis implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 趋势描述
         */
        private String description;
        
        /**
         * 趋势方向（UP、DOWN、STABLE）
         */
        private String direction;
        
        /**
         * 趋势强度
         */
        private Double strength;
        
        /**
         * 关键时间点
         */
        private List<String> keyTimePoints;
    }
    
    /**
     * 风险评估
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RiskAssessment implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 风险列表
         */
        private List<Risk> risks;
        
        /**
         * 整体风险等级（HIGH、MEDIUM、LOW）
         */
        private String overallRiskLevel;
    }
    
    /**
     * 风险项
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Risk implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 风险描述
         */
        private String description;
        
        /**
         * 风险等级
         */
        private String riskLevel;
        
        /**
         * 影响程度
         */
        private Double impact;
        
        /**
         * 发生概率
         */
        private Double probability;
        
        /**
         * 缓解建议
         */
        private List<String> mitigationSuggestions;
    }
    
    /**
     * 质量评分
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class QualityScore implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 完整性评分
         */
        private Double completeness;
        
        /**
         * 准确性评分
         */
        private Double accuracy;
        
        /**
         * 一致性评分
         */
        private Double consistency;
        
        /**
         * 可读性评分
         */
        private Double readability;
        
        /**
         * 综合评分
         */
        private Double overall;
    }
}
