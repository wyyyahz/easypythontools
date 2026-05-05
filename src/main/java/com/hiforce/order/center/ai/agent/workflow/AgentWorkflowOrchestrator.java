package com.hiforce.order.center.ai.agent.workflow;

import com.hiforce.order.center.ai.agent.engine.*;
import com.hiforce.order.center.ai.agent.model.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * 智能体工作流编排器
 */
@Slf4j
@Component
public class AgentWorkflowOrchestrator {
    
    @Autowired
    private DocumentUnderstandingEngine understandingEngine;
    
    @Autowired
    private DocumentRetrievalEngine retrievalEngine;
    
    @Autowired
    private InformationExtractionEngine extractionEngine;
    
    @Autowired
    private ComprehensiveAnalysisEngine analysisEngine;
    
    /**
     * 执行完整的文档处理工作流
     *
     * @param document 文档对象
     * @return 工作流结果
     */
    public AgentWorkflow executeWorkflow(Document document) {
        log.info("开始执行智能体工作流，文档ID: {}", document.getDocId());
        
        // 创建工作流
        AgentWorkflow workflow = createWorkflow(document);
        
        try {
            // 步骤1: 文档理解
            executeUnderstandingStep(workflow, document);
            
            // 步骤2: 文档索引（用于后续检索）
            executeIndexingStep(workflow, document);
            
            // 步骤3: 信息抽取
            executeExtractionStep(workflow, document);
            
            // 步骤4: 综合分析
            executeAnalysisStep(workflow, document);
            
            // 更新工作流状态为完成
            workflow.setStatus(AgentWorkflow.WorkflowStatus.COMPLETED);
            workflow.setCompleteTime(new Date());
            
            log.info("智能体工作流执行完成，工作流ID: {}", workflow.getWorkflowId());
            
        } catch (Exception e) {
            log.error("智能体工作流执行失败", e);
            workflow.setStatus(AgentWorkflow.WorkflowStatus.FAILED);
            workflow.setCompleteTime(new Date());
            
            // 记录错误信息到最后一个执行的步骤
            List<AgentWorkflow.WorkflowStep> steps = workflow.getSteps();
            if (!steps.isEmpty()) {
                AgentWorkflow.WorkflowStep lastStep = steps.get(steps.size() - 1);
                lastStep.setStatus(AgentWorkflow.StepStatus.FAILED);
                lastStep.setErrorMessage(e.getMessage());
            }
        }
        
        return workflow;
    }
    
    /**
     * 执行文档检索工作流
     *
     * @param query 查询语句
     * @param maxResults 最大结果数
     * @return 检索结果
     */
    public RetrievalResult executeRetrievalWorkflow(String query, int maxResults) {
        log.info("执行检索工作流，查询: {}", query);
        
        long startTime = System.currentTimeMillis();
        RetrievalResult result = retrievalEngine.search(query, maxResults);
        long executionTime = System.currentTimeMillis() - startTime;
        
        log.info("检索工作流完成，找到 {} 个结果，耗时: {}ms", 
            result.getTotalCount(), executionTime);
        
        return result;
    }
    
    /**
     * 执行批量文档处理工作流
     *
     * @param documents 文档列表
     * @return 工作流结果列表
     */
    public List<AgentWorkflow> executeBatchWorkflow(List<Document> documents) {
        log.info("开始执行批量文档处理工作流，文档数量: {}", documents.size());
        
        List<AgentWorkflow> workflows = new ArrayList<>();
        
        for (Document document : documents) {
            try {
                AgentWorkflow workflow = executeWorkflow(document);
                workflows.add(workflow);
            } catch (Exception e) {
                log.error("处理文档失败，文档ID: {}", document.getDocId(), e);
                
                // 创建失败的工作流记录
                AgentWorkflow failedWorkflow = createWorkflow(document);
                failedWorkflow.setStatus(AgentWorkflow.WorkflowStatus.FAILED);
                failedWorkflow.setCompleteTime(new Date());
                workflows.add(failedWorkflow);
            }
        }
        
        log.info("批量文档处理工作流完成，成功: {}, 失败: {}",
            workflows.stream().filter(w -> w.getStatus() == AgentWorkflow.WorkflowStatus.COMPLETED).count(),
            workflows.stream().filter(w -> w.getStatus() == AgentWorkflow.WorkflowStatus.FAILED).count());
        
        return workflows;
    }
    
    /**
     * 创建工作流对象
     */
    private AgentWorkflow createWorkflow(Document document) {
        String workflowId = UUID.randomUUID().toString().replace("-", "");
        
        List<AgentWorkflow.WorkflowStep> steps = new ArrayList<>();
        steps.add(createStep("understanding", "文档理解", AgentWorkflow.StepType.UNDERSTANDING));
        steps.add(createStep("indexing", "文档索引", AgentWorkflow.StepType.RETRIEVAL));
        steps.add(createStep("extraction", "信息抽取", AgentWorkflow.StepType.EXTRACTION));
        steps.add(createStep("analysis", "综合分析", AgentWorkflow.StepType.ANALYSIS));
        
        return AgentWorkflow.builder()
            .workflowId(workflowId)
            .workflowName("文档智能处理工作流")
            .description("对文档进行理解、检索、抽取与综合分析")
            .steps(steps)
            .status(AgentWorkflow.WorkflowStatus.RUNNING)
            .createTime(new Date())
            .build();
    }
    
    /**
     * 创建工作流步骤
     */
    private AgentWorkflow.WorkflowStep createStep(String stepId, String stepName, 
                                                  AgentWorkflow.StepType stepType) {
        return AgentWorkflow.WorkflowStep.builder()
            .stepId(stepId)
            .stepName(stepName)
            .stepType(stepType)
            .status(AgentWorkflow.StepStatus.PENDING)
            .build();
    }
    
    /**
     * 执行文档理解步骤
     */
    private void executeUnderstandingStep(AgentWorkflow workflow, Document document) {
        log.info("执行文档理解步骤");
        
        AgentWorkflow.WorkflowStep step = findStep(workflow, AgentWorkflow.StepType.UNDERSTANDING);
        step.setStatus(AgentWorkflow.StepStatus.RUNNING);
        
        long startTime = System.currentTimeMillis();
        
        try {
            UnderstandingResult result = understandingEngine.understand(document);
            
            step.setStatus(AgentWorkflow.StepStatus.SUCCESS);
            step.setOutput("主题: " + result.getTopic());
            
            // 保存理解结果到工作流
            if (workflow.getResult() == null) {
                workflow.setResult(AgentWorkflow.WorkflowResult.builder().build());
            }
            workflow.getResult().setUnderstandingResult(result);
            
        } catch (Exception e) {
            step.setStatus(AgentWorkflow.StepStatus.FAILED);
            step.setErrorMessage(e.getMessage());
            throw e;
        } finally {
            step.setExecutionTime(System.currentTimeMillis() - startTime);
        }
        
        log.info("文档理解步骤完成，耗时: {}ms", step.getExecutionTime());
    }
    
    /**
     * 执行文档索引步骤
     */
    private void executeIndexingStep(AgentWorkflow workflow, Document document) {
        log.info("执行文档索引步骤");
        
        AgentWorkflow.WorkflowStep step = findStep(workflow, AgentWorkflow.StepType.RETRIEVAL);
        step.setStatus(AgentWorkflow.StepStatus.RUNNING);
        
        long startTime = System.currentTimeMillis();
        
        try {
            retrievalEngine.indexDocument(document);
            
            step.setStatus(AgentWorkflow.StepStatus.SUCCESS);
            step.setOutput("文档已索引");
            
        } catch (Exception e) {
            step.setStatus(AgentWorkflow.StepStatus.FAILED);
            step.setErrorMessage(e.getMessage());
            throw e;
        } finally {
            step.setExecutionTime(System.currentTimeMillis() - startTime);
        }
        
        log.info("文档索引步骤完成，耗时: {}ms", step.getExecutionTime());
    }
    
    /**
     * 执行信息抽取步骤
     */
    private void executeExtractionStep(AgentWorkflow workflow, Document document) {
        log.info("执行信息抽取步骤");
        
        AgentWorkflow.WorkflowStep step = findStep(workflow, AgentWorkflow.StepType.EXTRACTION);
        step.setStatus(AgentWorkflow.StepStatus.RUNNING);
        
        long startTime = System.currentTimeMillis();
        
        try {
            ExtractionResult result = extractionEngine.extract(document);
            
            step.setStatus(AgentWorkflow.StepStatus.SUCCESS);
            step.setOutput("抽取实体数: " + 
                (result.getEntities() != null ? result.getEntities().size() : 0));
            
            // 保存抽取结果到工作流
            if (workflow.getResult() == null) {
                workflow.setResult(AgentWorkflow.WorkflowResult.builder().build());
            }
            workflow.getResult().setExtractionResult(result);
            
        } catch (Exception e) {
            step.setStatus(AgentWorkflow.StepStatus.FAILED);
            step.setErrorMessage(e.getMessage());
            throw e;
        } finally {
            step.setExecutionTime(System.currentTimeMillis() - startTime);
        }
        
        log.info("信息抽取步骤完成，耗时: {}ms", step.getExecutionTime());
    }
    
    /**
     * 执行综合分析步骤
     */
    private void executeAnalysisStep(AgentWorkflow workflow, Document document) {
        log.info("执行综合分析步骤");
        
        AgentWorkflow.WorkflowStep step = findStep(workflow, AgentWorkflow.StepType.ANALYSIS);
        step.setStatus(AgentWorkflow.StepStatus.RUNNING);
        
        long startTime = System.currentTimeMillis();
        
        try {
            UnderstandingResult understandingResult = workflow.getResult().getUnderstandingResult();
            ExtractionResult extractionResult = workflow.getResult().getExtractionResult();
            
            AnalysisResult result = analysisEngine.analyze(document, understandingResult, extractionResult);
            
            step.setStatus(AgentWorkflow.StepStatus.SUCCESS);
            step.setOutput("分析完成");
            
            // 保存分析结果到工作流
            workflow.getResult().setAnalysisResult(result);
            
            // 计算综合评分
            double overallScore = calculateOverallScore(understandingResult, extractionResult, result);
            workflow.getResult().setOverallScore(overallScore);
            
            // 生成总结报告
            String summaryReport = generateSummaryReport(document, understandingResult, extractionResult, result);
            workflow.getResult().setSummaryReport(summaryReport);
            
        } catch (Exception e) {
            step.setStatus(AgentWorkflow.StepStatus.FAILED);
            step.setErrorMessage(e.getMessage());
            throw e;
        } finally {
            step.setExecutionTime(System.currentTimeMillis() - startTime);
        }
        
        log.info("综合分析步骤完成，耗时: {}ms", step.getExecutionTime());
    }
    
    /**
     * 查找步骤
     */
    private AgentWorkflow.WorkflowStep findStep(AgentWorkflow workflow, AgentWorkflow.StepType stepType) {
        return workflow.getSteps().stream()
            .filter(step -> step.getStepType() == stepType)
            .findFirst()
            .orElseThrow(() -> new IllegalStateException("找不到步骤类型: " + stepType));
    }
    
    /**
     * 计算综合评分
     */
    private double calculateOverallScore(UnderstandingResult understandingResult,
                                        ExtractionResult extractionResult,
                                        AnalysisResult analysisResult) {
        double score = 0.0;
        int factorCount = 0;
        
        // 基于理解置信度
        if (understandingResult != null && understandingResult.getConfidence() != null) {
            score += understandingResult.getConfidence();
            factorCount++;
        }
        
        // 基于抽取的实体数量
        if (extractionResult != null && extractionResult.getEntities() != null) {
            double entityScore = Math.min(1.0, extractionResult.getEntities().size() / 10.0);
            score += entityScore;
            factorCount++;
        }
        
        // 基于质量评分
        if (analysisResult != null && analysisResult.getQualityScore() != null) {
            score += analysisResult.getQualityScore().getOverall();
            factorCount++;
        }
        
        return factorCount > 0 ? score / factorCount : 0.5;
    }
    
    /**
     * 生成总结报告
     */
    private String generateSummaryReport(Document document,
                                        UnderstandingResult understandingResult,
                                        ExtractionResult extractionResult,
                                        AnalysisResult analysisResult) {
        StringBuilder report = new StringBuilder();
        
        report.append("=== 文档智能分析报告 ===\n\n");
        
        // 基本信息
        report.append("【文档基本信息】\n");
        report.append("文档ID: ").append(document.getDocId()).append("\n");
        report.append("文档标题: ").append(document.getTitle()).append("\n");
        report.append("文档类型: ").append(document.getDocType()).append("\n\n");
        
        // 理解结果
        if (understandingResult != null) {
            report.append("【文档理解结果】\n");
            report.append("主题: ").append(understandingResult.getTopic()).append("\n");
            report.append("分类: ").append(understandingResult.getCategory()).append("\n");
            report.append("语言: ").append(understandingResult.getLanguage()).append("\n");
            report.append("置信度: ").append(understandingResult.getConfidence()).append("\n\n");
        }
        
        // 抽取结果
        if (extractionResult != null) {
            report.append("【信息抽取结果】\n");
            report.append("实体数量: ").append(
                extractionResult.getEntities() != null ? extractionResult.getEntities().size() : 0).append("\n");
            report.append("关系数量: ").append(
                extractionResult.getRelations() != null ? extractionResult.getRelations().size() : 0).append("\n");
            report.append("事件数量: ").append(
                extractionResult.getEvents() != null ? extractionResult.getEvents().size() : 0).append("\n\n");
        }
        
        // 分析结果
        if (analysisResult != null) {
            report.append("【综合分析结果】\n");
            report.append(analysisResult.getSummary()).append("\n\n");
            
            if (analysisResult.getQualityScore() != null) {
                report.append("【质量评估】\n");
                report.append("完整性: ").append(analysisResult.getQualityScore().getCompleteness()).append("\n");
                report.append("准确性: ").append(analysisResult.getQualityScore().getAccuracy()).append("\n");
                report.append("一致性: ").append(analysisResult.getQualityScore().getConsistency()).append("\n");
                report.append("可读性: ").append(analysisResult.getQualityScore().getReadability()).append("\n");
                report.append("综合评分: ").append(analysisResult.getQualityScore().getOverall()).append("\n\n");
            }
        }
        
        report.append("=== 报告结束 ===\n");
        
        return report.toString();
    }
}
