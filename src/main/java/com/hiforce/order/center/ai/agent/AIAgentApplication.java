package com.hiforce.order.center.ai.agent;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * AI智能体工作流应用启动类
 */
@SpringBootApplication
public class AIAgentApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(AIAgentApplication.class, args);
        System.out.println("========================================");
        System.out.println("AI智能体工作流服务启动成功！");
        System.out.println("API文档地址: http://localhost:8080/api/ai-agent/health");
        System.out.println("========================================");
    }
}
