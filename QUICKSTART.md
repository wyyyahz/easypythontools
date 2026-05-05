# 快速开始指南

## 前置要求

- Java 1.8 或更高版本
- Maven 3.x
- Git（可选）

## 安装步骤

### 方法一：使用启动脚本（推荐）

Windows系统直接双击运行：
```
start.bat
```

### 方法二：手动编译运行

```bash
# 1. 进入项目目录
cd ai-agent

# 2. 编译项目
mvn clean package -DskipTests

# 3. 运行应用
java -jar target/ai-agent.jar
```

## 验证安装

服务启动后，在浏览器中访问：
```
http://localhost:8080/api/ai-agent/health
```

如果看到以下响应，说明安装成功：
```json
{
  "status": "UP",
  "service": "AI Agent Document Intelligence"
}
```

## 第一次使用

### 1. 处理一个文档

使用curl命令：
```bash
curl -X POST http://localhost:8080/api/ai-agent/process \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"测试\",\"content\":\"这是一个测试文档\",\"docType\":\"TXT\"}"
```

或使用Postman等API测试工具发送POST请求到：
- URL: `http://localhost:8080/api/ai-agent/process`
- Body (JSON):
```json
{
  "title": "人工智能简介",
  "content": "人工智能是计算机科学的一个重要分支。它致力于创造能够模拟人类智能的系统。机器学习、深度学习是AI的核心技术。",
  "docType": "TXT",
  "source": "测试"
}
```

### 2. 查看结果

响应将包含完整的工作流执行结果，包括：
- 文档理解结果（主题、摘要、关键词等）
- 信息抽取结果（实体、关系、事件等）
- 综合分析结果（质量评分、风险评估等）
- 总结报告

### 3. 检索文档

先处理几个文档建立索引，然后进行检索：
```bash
curl "http://localhost:8080/api/ai-agent/search?query=人工智能&maxResults=5"
```

## 常用操作

### 批量处理文档

```bash
curl -X POST http://localhost:8080/api/ai-agent/process/batch \
  -H "Content-Type: application/json" \
  -d "[{\"title\":\"文档1\",\"content\":\"内容1\",\"docType\":\"TXT\"},{\"title\":\"文档2\",\"content\":\"内容2\",\"docType\":\"TXT\"}]"
```

### 仅理解文档

```bash
curl -X POST http://localhost:8080/api/ai-agent/understand \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"测试\",\"content\":\"测试内容\",\"docType\":\"TXT\"}"
```

### 仅抽取信息

```bash
curl -X POST http://localhost:8080/api/ai-agent/extract \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"会议\",\"content\":\"2024年3月15日在北京召开会议\",\"docType\":\"TXT\"}"
```

## 查看日志

日志文件位于：
```
ai-agent/logs/ai-agent.log
ai-agent/logs/ai-agent-error.log
```

## 停止服务

在运行窗口按 `Ctrl+C` 即可停止服务。

## 常见问题

### Q1: 端口8080被占用怎么办？

修改 `src/main/resources/application.yml` 中的端口配置：
```yaml
server:
  port: 8081  # 改为其他可用端口
```

### Q2: 如何调整日志级别？

修改 `src/main/resources/application.yml`：
```yaml
logging:
  level:
    com.hiforce.order.center.ai.agent: DEBUG  # 改为DEBUG查看更详细日志
```

### Q3: 编译失败怎么办？

确保Maven已正确安装并配置环境变量：
```bash
mvn -version  # 检查Maven版本
java -version  # 检查Java版本
```

### Q4: 如何处理中文文档？

系统已针对中文优化，直接传入中文内容即可。确保请求的Content-Type为`application/json; charset=utf-8`。

## 下一步

- 阅读 [README.md](README.md) 了解完整功能
- 查看 [API_EXAMPLES.md](API_EXAMPLES.md) 学习更多API用法
- 阅读 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) 了解项目架构

## 技术支持

如遇到问题，请检查：
1. Java和Maven版本是否符合要求
2. 端口是否被占用
3. 日志文件中的错误信息

---

**祝您使用愉快！** 🎉
