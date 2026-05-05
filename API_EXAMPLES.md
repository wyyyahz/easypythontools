# API使用示例

## 1. 健康检查

```bash
curl -X GET http://localhost:8080/api/ai-agent/health
```

**响应**:
```json
{
  "status": "UP",
  "service": "AI Agent Document Intelligence"
}
```

## 2. 处理单个文档

```bash
curl -X POST http://localhost:8080/api/ai-agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "title": "人工智能技术发展报告",
    "content": "人工智能技术在近年来取得了快速发展。2024年，各大科技公司纷纷加大了对AI技术的投入。深度学习、自然语言处理、计算机视觉等领域都取得了重要突破。预计未来几年，AI技术将在医疗、金融、教育等行业得到更广泛的应用。然而，AI技术的发展也带来了一些挑战，如数据隐私、算法偏见等问题需要解决。",
    "docType": "TXT",
    "source": "技术报告"
  }'
```

**响应**:
```json
{
  "success": true,
  "workflow": {
    "workflowId": "a1b2c3d4e5f6...",
    "workflowName": "文档智能处理工作流",
    "status": "COMPLETED",
    "steps": [...],
    "result": {
      "understandingResult": {
        "topic": "人工智能技术发展报告",
        "summary": "人工智能技术在近年来取得了快速发展。",
        "keywords": ["人工智能", "技术", "发展", "应用"],
        "category": "TECHNOLOGY",
        "confidence": 0.8
      },
      "extractionResult": {
        "entities": [...],
        "relations": [...],
        "events": [...]
      },
      "analysisResult": {
        "summary": "本文档主题为：人工智能技术发展报告...",
        "qualityScore": {
          "overall": 0.75
        }
      },
      "summaryReport": "=== 文档智能分析报告 ===\n..."
    }
  }
}
```

## 3. 批量处理文档

```bash
curl -X POST http://localhost:8080/api/ai-agent/process/batch \
  -H "Content-Type: application/json" \
  -d '[
    {
      "title": "文档1",
      "content": "这是第一个文档的内容，关于机器学习的基础知识。",
      "docType": "TXT"
    },
    {
      "title": "文档2",
      "content": "这是第二个文档的内容，关于深度学习的应用场景。",
      "docType": "TXT"
    }
  ]'
```

## 4. 检索文档

```bash
curl -X GET "http://localhost:8080/api/ai-agent/search?query=机器学习&maxResults=10"
```

**响应**:
```json
{
  "success": true,
  "result": {
    "query": "机器学习",
    "documents": [
      {
        "docId": "doc1",
        "title": "文档1",
        "snippet": "...机器学习的基础知识...",
        "relevanceScore": 2.0,
        "source": null
      }
    ],
    "totalCount": 1,
    "retrievalTime": 15
  }
}
```

## 5. 仅理解文档

```bash
curl -X POST http://localhost:8080/api/ai-agent/understand \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文档",
    "content": "这是一段测试内容，用于验证文档理解功能。",
    "docType": "TXT"
  }'
```

**响应**:
```json
{
  "success": true,
  "result": {
    "topic": "测试文档",
    "summary": "这是一段测试内容，用于验证文档理解功能。",
    "keywords": ["测试", "内容", "验证", "理解"],
    "entities": [],
    "category": "GENERAL",
    "sentiment": {
      "polarity": "NEUTRAL",
      "score": 0.0,
      "labels": ["中性"]
    },
    "language": "ZH",
    "confidence": 0.6
  }
}
```

## 6. 仅抽取信息

```bash
curl -X POST http://localhost:8080/api/ai-agent/extract \
  -H "Content-Type: application/json" \
  -d '{
    "title": "会议通知",
    "content": "2024年3月15日，科技公司在北京召开了年度技术大会。张三先生和李四女士参加了此次会议。",
    "docType": "TXT"
  }'
```

**响应**:
```json
{
  "success": true,
  "result": {
    "entities": [
      {
        "text": "2024年3月15日",
        "type": "DATE",
        "confidence": 0.75
      },
      {
        "text": "北京",
        "type": "LOCATION",
        "confidence": 0.75
      },
      {
        "text": "张三先生",
        "type": "PERSON",
        "confidence": 0.75
      }
    ],
    "relations": [],
    "events": [
      {
        "eventType": "MEETING",
        "description": "年度技术大会",
        "time": "2024年3月15日",
        "confidence": 0.65
      }
    ],
    "keyFacts": [...],
    "structuredData": {
      "entities": {
        "DATE": ["2024年3月15日"],
        "LOCATION": ["北京"],
        "PERSON": ["张三先生"]
      }
    }
  }
}
```

## 7. 完整分析文档

```bash
curl -X POST http://localhost:8080/api/ai-agent/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "title": "产品评测",
    "content": "这款新产品的性能优秀，用户体验良好。但是在价格方面偏高，可能影响市场接受度。总体而言，这是一款值得推荐的产品。",
    "docType": "TXT"
  }'
```

**响应**:
```json
{
  "success": true,
  "result": {
    "summary": "本文档主题为：产品评测。文档类别为：BUSINESS。主要关键词包括：产品、性能、用户、体验、价格。整体情感倾向为：POSITIVE。",
    "findings": [...],
    "insights": [...],
    "trendAnalysis": {
      "description": "基于当前文档内容的趋势分析",
      "direction": "STABLE",
      "strength": 0.5
    },
    "riskAssessment": {
      "risks": [],
      "overallRiskLevel": "LOW"
    },
    "qualityScore": {
      "completeness": 0.6,
      "accuracy": 0.75,
      "consistency": 0.7,
      "readability": 0.9,
      "overall": 0.7375
    }
  }
}
```

## Python调用示例

```python
import requests
import json

# 服务地址
BASE_URL = "http://localhost:8080/api/ai-agent"

def process_document(title, content, doc_type="TXT"):
    """处理单个文档"""
    url = f"{BASE_URL}/process"
    payload = {
        "title": title,
        "content": content,
        "docType": doc_type
    }
    
    response = requests.post(url, json=payload)
    return response.json()

def search_documents(query, max_results=10):
    """检索文档"""
    url = f"{BASE_URL}/search"
    params = {
        "query": query,
        "maxResults": max_results
    }
    
    response = requests.get(url, params=params)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 处理文档
    result = process_document(
        "测试文档",
        "这是一个关于人工智能的测试文档。AI技术正在快速发展。"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 检索文档
    search_result = search_documents("人工智能", 5)
    print(json.dumps(search_result, indent=2, ensure_ascii=False))
```

## JavaScript调用示例

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8080/api/ai-agent';

// 处理文档
async function processDocument(title, content, docType = 'TXT') {
    try {
        const response = await axios.post(`${BASE_URL}/process`, {
            title: title,
            content: content,
            docType: docType
        });
        return response.data;
    } catch (error) {
        console.error('Error:', error.message);
        throw error;
    }
}

// 检索文档
async function searchDocuments(query, maxResults = 10) {
    try {
        const response = await axios.get(`${BASE_URL}/search`, {
            params: {
                query: query,
                maxResults: maxResults
            }
        });
        return response.data;
    } catch (error) {
        console.error('Error:', error.message);
        throw error;
    }
}

// 使用示例
(async () => {
    // 处理文档
    const result = await processDocument(
        '测试文档',
        '这是一个关于机器学习的测试文档。'
    );
    console.log(JSON.stringify(result, null, 2));
    
    // 检索文档
    const searchResult = await searchDocuments('机器学习', 5);
    console.log(JSON.stringify(searchResult, null, 2));
})();
```

## 注意事项

1. **文档大小限制**: 建议单个文档内容不超过10MB
2. **并发控制**: 默认最大并发工作流数为10，可根据需要调整配置
3. **超时设置**: 工作流默认超时时间为5分钟
4. **索引持久化**: 当前实现使用内存索引，重启后索引会丢失。生产环境建议集成Elasticsearch

## 错误处理

所有API在发生错误时都会返回统一格式：

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

HTTP状态码说明：
- `200`: 成功
- `400`: 请求参数错误
- `500`: 服务器内部错误
