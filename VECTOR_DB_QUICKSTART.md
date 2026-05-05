# 向量数据库功能快速开始

## 📋 功能概述

本系统现已支持将抽取的文档信息自动存储到向量数据库中，并提供基于语义的相似度检索功能。

### 核心特性

✅ **自动向量存储** - 文档处理完成后自动存储到Milvus  
✅ **多维度向量化** - 分别对文本、实体、关系、事件、事实进行向量化  
✅ **语义搜索** - 支持基于自然语言的相似度检索  
✅ **优雅降级** - Milvus未启动时不影响主流程  

---

## 🚀 快速开始（3步）

### 步骤1：启动Milvus服务

使用Docker Compose快速启动（推荐）：

创建 `docker-compose.yml` 文件：

```yaml
version: '3.5'

services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - ./volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ./volumes/minio:/minio_data
    command: minio server /minio_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  standalone:
    image: milvusdb/milvus:v2.3.5
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ./volumes/milvus:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"
```

启动命令：

```bash
docker-compose up -d
```

验证Milvus是否启动成功：

```bash
docker ps | grep milvus
```

### 步骤2：配置应用

编辑 `src/main/resources/application.yml`：

```yaml
vector-database:
  host: localhost        # Milvus地址
  port: 19530           # Milvus端口
  collection-name: document_vectors
  dimension: 768
  enabled: true         # 设为true启用
```

### 步骤3：启动应用并测试

```bash
# 编译项目
mvn clean package

# 启动应用
java -jar target/ai-agent-1.0.0.jar
```

---

## 📝 使用示例

### 1️⃣ 处理文档（自动存储向量）

```bash
curl -X POST http://localhost:8080/api/ai-agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "docId": "doc001",
    "title": "人工智能发展报告",
    "content": "2024年人工智能技术取得了重大突破。深度学习模型在自然语言处理领域表现出色，准确率提升了30%。多家科技公司发布了新一代AI产品。",
    "docType": "TXT",
    "source": "技术期刊"
  }'
```

**执行后会自动存储：**
- ✅ 完整文本向量
- ✅ 实体向量（日期、金额等）
- ✅ 关系向量
- ✅ 事件向量
- ✅ 关键事实向量

### 2️⃣ 向量相似度搜索

```bash
curl -X POST http://localhost:8080/api/ai-agent/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "queryText": "AI技术的最新进展",
    "topK": 5
  }'
```

返回结果包含相似度评分和相关文档片段。

### 3️⃣ 删除向量数据

```bash
curl -X DELETE http://localhost:8080/api/ai-agent/vector/doc001
```

### 4️⃣ 清空向量数据库

```bash
curl -X POST http://localhost:8080/api/ai-agent/vector/clear
```

---

## 🧪 运行测试

```bash
# 运行向量数据库测试
mvn test -Dtest=VectorDatabaseTest
```

测试包括：
- ✅ 文本向量化测试
- ✅ 批量向量化测试
- ✅ 相似度计算测试
- ✅ 向量数据库连接测试

---

## 📊 API接口总览

| 功能 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 处理文档 | POST | `/api/ai-agent/process` | 自动存储向量 |
| 批量处理 | POST | `/api/ai-agent/process/batch` | 批量存储向量 |
| 向量搜索 | POST | `/api/ai-agent/vector/search` | 语义搜索 |
| 删除向量 | DELETE | `/api/ai-agent/vector/{docId}` | 删除指定文档 |
| 清空数据库 | POST | `/api/ai-agent/vector/clear` | 清空所有数据 |

---

## 🔧 高级配置

### 接入真实Embedding模型

当前使用的是模拟算法，生产环境建议替换为真实模型：

**OpenAI Embeddings示例：**

```java
@Service
public class TextEmbeddingService {
    
    public List<Float> embed(String text) {
        // 调用OpenAI API
        OpenAIClient client = OpenAIClient.builder()
            .apiKey("your-api-key")
            .build();
        
        EmbeddingRequest request = EmbeddingRequest.builder()
            .model("text-embedding-ada-002")
            .input(text)
            .build();
        
        EmbeddingResult result = client.createEmbedding(request);
        return result.getData().get(0).getEmbedding();
    }
}
```

### 性能优化

**1. 异步存储**

```java
@Async
public void saveToVectorDatabase(...) {
    // 异步执行，不阻塞主流程
}
```

**2. 批量插入优化**

```java
// 一次性插入多个向量，减少网络开销
vectorDatabaseService.batchInsert(vectorDocs);
```

**3. 索引类型选择**

- 小数据量（<100万）：`IVF_FLAT`
- 大数据量（>100万）：`HNSW`

---

## ❓ 常见问题

### Q1: Milvus未启动会影响文档处理吗？

**A:** 不会。系统会优雅降级，跳过向量存储步骤，继续完成文档处理。

### Q2: 如何查看已存储的向量数据？

**A:** 可以使用Milvus可视化工具 Attu：

```bash
docker run -p 8000:3000 -e MILVUS_URL=localhost:19530 zilliz/attu:v2.3
```

然后访问 http://localhost:8000

### Q3: 向量维度可以修改吗？

**A:** 可以，但需要：
1. 修改 `application.yml` 中的 `dimension`
2. 确保embedding模型输出相同维度
3. 清空现有数据后重新创建集合

### Q4: 存储空间占用多大？

**A:** 估算公式：
```
存储空间 ≈ 文档数 × 平均向量数 × 维度 × 4字节
例如：1000文档 × 20向量 × 768维 × 4字节 ≈ 60MB
```

---

## 📚 相关文档

- [详细使用说明](VECTOR_DB_USAGE.md)
- [Milvus官方文档](https://milvus.io/docs)
- [API测试用例](src/test/java/com/hiforce/order/center/ai/agent/VectorDatabaseTest.java)

---

## 🎯 下一步

1. ✅ 启动Milvus服务
2. ✅ 配置应用
3. ✅ 处理测试文档
4. ✅ 尝试向量搜索
5. 🔄 接入真实Embedding模型（可选）
6. 🔄 优化性能和索引（可选）

祝你使用愉快！🎉
