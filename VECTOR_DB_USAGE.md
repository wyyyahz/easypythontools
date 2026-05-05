# 向量数据库集成说明

## 概述

本系统已将抽取的文档信息自动存储到向量数据库（Milvus）中，支持基于语义的相似度检索。

## 架构设计

### 数据存储策略

系统在信息抽取完成后，会将以下内容分别向量化并存储：

1. **完整文本向量** (FULL_TEXT)
   - 对整个文档内容进行向量化
   - 包含元数据：文档类型、来源、实体数量等

2. **实体向量** (ENTITY)
   - 对每个抽取的实体进行向量化
   - 包含元数据：实体类型、置信度

3. **关系向量** (RELATION)
   - 对每个抽取的关系描述进行向量化
   - 包含元数据：关系类型、头实体、尾实体、置信度

4. **事件向量** (EVENT)
   - 对每个抽取的事件描述进行向量化
   - 包含元数据：事件类型、时间、地点、置信度

5. **关键事实向量** (KEY_FACT)
   - 对每个关键事实进行向量化
   - 包含元数据：事实类型、重要性评分

## 配置说明

在 `application.yml` 中配置向量数据库：

```yaml
vector-database:
  host: localhost          # Milvus服务器地址
  port: 19530             # Milvus服务器端口
  collection-name: document_vectors  # 集合名称
  dimension: 768          # 向量维度
  enabled: true           # 是否启用（设为false可跳过存储）
```

## 使用方式

### 1. 启动Milvus服务

需要先安装并启动Milvus向量数据库：

```bash
# 使用Docker启动Milvus
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:v2.3.5 \
  milvus run standalone
```

或者使用Docker Compose：

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
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/minio:/minio_data
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
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/milvus:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"
```

### 2. 处理文档（自动存储到向量数据库）

```bash
curl -X POST http://localhost:8080/api/ai-agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "docId": "doc001",
    "title": "人工智能技术发展报告",
    "content": "2024年人工智能技术取得了重大突破。深度学习模型在自然语言处理领域表现出色...",
    "docType": "TXT",
    "source": "技术期刊"
  }'
```

处理后，系统会自动将以下数据存储到向量数据库：
- 完整文档内容的向量
- 抽取的实体向量（如日期、金额等）
- 抽取的关系向量
- 抽取的事件向量
- 关键事实向量

### 3. 向量相似度搜索

```bash
curl -X POST http://localhost:8080/api/ai-agent/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "queryText": "人工智能技术的最新进展",
    "topK": 5
  }'
```

返回结果示例：
```json
{
  "success": true,
  "results": [
    {
      "score": 0.95,
      "docId": "doc001",
      "contentType": "FULL_TEXT",
      "title": "人工智能技术发展报告",
      "content": "2024年人工智能技术取得了重大突破...",
      "metadata": "{\"entityCount\":5,\"relationCount\":3,...}"
    },
    {
      "score": 0.87,
      "docId": "doc001",
      "contentType": "ENTITY",
      "title": "人工智能技术发展报告",
      "content": "2024年",
      "metadata": "{\"entityType\":\"DATE\",\"confidence\":0.8}"
    }
  ],
  "count": 2
}
```

### 4. 删除向量文档

```bash
curl -X DELETE http://localhost:8080/api/ai-agent/vector/doc001
```

### 5. 清空向量数据库

```bash
curl -X POST http://localhost:8080/api/ai-agent/vector/clear
```

## API接口列表

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 处理文档 | POST | `/api/ai-agent/process` | 处理文档并自动存储到向量数据库 |
| 批量处理 | POST | `/api/ai-agent/process/batch` | 批量处理文档 |
| 向量搜索 | POST | `/api/ai-agent/vector/search` | 基于文本的向量相似度搜索 |
| 删除向量 | DELETE | `/api/ai-agent/vector/{docId}` | 删除指定文档的向量数据 |
| 清空数据库 | POST | `/api/ai-agent/vector/clear` | 清空所有向量数据 |

## 扩展建议

### 1. 接入真实的Embedding模型

当前使用的是模拟的向量生成算法，建议替换为真实的embedding模型：

- **OpenAI Embeddings**: `text-embedding-ada-002`
- **HuggingFace**: `sentence-transformers/all-MiniLM-L6-v2`
- **百度文心一言**: ERNIE-Bot embedding
- **阿里通义千问**: text-embedding-v1

修改 `TextEmbeddingService.embed()` 方法即可。

### 2. 优化向量索引

根据数据量调整Milvus索引参数：

```java
// IVF_FLAT 适合中小规模数据
.withIndexType(IndexType.IVF_FLAT)
.withExtraParam("{\"nlist\":1024}")

// HNSW 适合大规模数据，查询更快
.withIndexType(IndexType.HNSW)
.withExtraParam("{\"M\":16,\"efConstruction\":200}")
```

### 3. 添加向量缓存

对于频繁查询的向量，可以添加Redis缓存层提升性能。

### 4. 异步存储

如果文档量大，可以将向量存储改为异步执行，避免阻塞主流程：

```java
@Async
public void saveToVectorDatabase(...) {
    // 异步存储逻辑
}
```

## 注意事项

1. **Milvus未启动时的降级处理**：如果Milvus未启动或连接失败，系统会自动降级，不影响文档处理主流程
2. **向量维度一致性**：确保配置的dimension与embedding模型输出的维度一致
3. **存储空间**：向量数据占用空间较大，定期清理无用数据
4. **性能优化**：大批量插入时建议使用batchInsert方法

## 故障排查

### 问题1：连接Milvus失败

检查：
- Milvus服务是否启动
- 端口19530是否开放
- 配置文件中的host和port是否正确

### 问题2：向量搜索无结果

检查：
- 是否有成功存储的向量数据
- 查询文本是否与存储的内容相关
- 向量维度是否匹配

### 问题3：存储失败但不影响主流程

这是预期行为。系统会记录错误日志，但不会中断文档处理流程。查看日志文件了解详细错误信息。
