package com.hiforce.order.center.ai.agent.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Date;
import java.util.List;

/**
 * 智能体工作流模型
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AgentWorkflow implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * 工作流ID
     */
    private String workflowId;
    
    /**
     * 工作流名称
     */
    private String workflowName;
    
    /**
     * 工作流描述
     */
    private String description;
    
    /**
     * 工作流步骤列表
     */
    private List<WorkflowStep> steps;
    
    /**
     * 工作流状态（PENDING、RUNNING、COMPLETED、FAILED）
     */
    private WorkflowStatus status;
    
    /**
     * 创建时间
     */
    private Date createTime;
    
    /**
     * 完成时间
     */
    private Date completeTime;
    
    /**
     * 工作流结果
     */
    private WorkflowResult result;
    
    /**
     * 工作流步骤
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class WorkflowStep implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 步骤ID
         */
        private String stepId;
        
        /**
         * 步骤名称
         */
        private String stepName;
        
        /**
         * 步骤类型（UNDERSTANDING、RETRIEVAL、EXTRACTION、ANALYSIS）
         */
        private StepType stepType;
        
        /**
         * 步骤配置
         */
        private String stepConfig;
        
        /**
         * 步骤状态
         */
        private StepStatus status;
        
        /**
         * 步骤输入
         */
        private String input;
        
        /**
         * 步骤输出
         */
        private String output;
        
        /**
         * 执行时间（毫秒）
         */
        private Long executionTime;
        
        /**
         * 错误信息
         */
        private String errorMessage;
    }
    
    /**
     * 工作流结果
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class WorkflowResult implements Serializable {
        
        private static final long serialVersionUID = 1L;
        
        /**
         * 理解结果
         */
        private UnderstandingResult understandingResult;
        
        /**
         * 检索结果
         */
        private RetrievalResult retrievalResult;
        
        /**
         * 抽取结果
         */
        private ExtractionResult extractionResult;
        
        /**
         * 分析结果
         */
        private AnalysisResult analysisResult;
        
        /**
         * 综合评分
         */
        private Double overallScore;
        
        /**
         * 总结报告
         */
        private String summaryReport;
    }
    
    /**
     * 步骤类型枚举
     */
    public enum StepType {
        UNDERSTANDING,  // 文档理解
        RETRIEVAL,      // 文档检索
        EXTRACTION,     // 信息抽取
        ANALYSIS        // 综合分析
    }
    
    /**
     * 工作流状态枚举
     */
    public enum WorkflowStatus {
        PENDING,    // 待执行
        RUNNING,    // 执行中
        COMPLETED,  // 已完成
        FAILED      // 失败
    }
    
    /**
     * 步骤状态枚举
     */
    public enum StepStatus {
        PENDING,    // 待执行
        RUNNING,    // 执行中
        SUCCESS,    // 成功
        FAILED      // 失败
    }
}
