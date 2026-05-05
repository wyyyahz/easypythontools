package com.hiforce.order.center.ai.agent.service;

import com.hiforce.order.center.ai.agent.model.VectorDocument;
import io.milvus.client.MilvusServiceClient;
import io.milvus.grpc.DataType;
import io.milvus.param.ConnectParam;
import io.milvus.param.IndexType;
import io.milvus.param.MetricType;
import io.milvus.param.R;
import io.milvus.param.collection.*;
import io.milvus.param.dml.InsertParam;
import io.milvus.param.dml.SearchParam;
import io.milvus.response.SearchResultsWrapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 向量数据库服务
 * 基于Milvus实现向量存储和检索
 */
@Slf4j
@Service
public class VectorDatabaseService {
    
    @Value("${vector-database.host:localhost}")
    private String host;
    
    @Value("${vector-database.port:19530}")
    private int port;
    
    @Value("${vector-database.collection-name:document_vectors}")
    private String collectionName;
    
    @Value("${vector-database.dimension:768}")
    private int dimension;
    
    @Value("${vector-database.enabled:true}")
    private boolean enabled;
    
    @Autowired
    private TextEmbeddingService embeddingService;
    
    private MilvusServiceClient milvusClient;
    
    /**
     * 初始化Milvus客户端和集合
     */
    @PostConstruct
    public void init() {
        if (!enabled) {
            log.info("向量数据库功能已禁用");
            return;
        }
        
        try {
            // 连接Milvus
            ConnectParam connectParam = ConnectParam.newBuilder()
                .withHost(host)
                .withPort(port)
                .build();
            
            milvusClient = new MilvusServiceClient(connectParam);
            
            // 测试连接
            R<Boolean> healthCheck = milvusClient.hasCollection(
                HasCollectionParam.newBuilder()
                    .withCollectionName(collectionName)
                    .build()
            );
            
            if (healthCheck.getStatus() != 0 || !healthCheck.getData()) {
                // 创建集合
                createCollection();
            }
            
            // 创建索引
            createIndex();
            
            // 加载集合到内存
            loadCollection();
            
            log.info("向量数据库初始化成功，集合: {}, 维度: {}", collectionName, dimension);
            
        } catch (Exception e) {
            log.error("向量数据库初始化失败，将使用内存模式", e);
            milvusClient = null;
        }
    }
    
    /**
     * 创建集合
     */
    private void createCollection() {
        FieldType docIdField = FieldType.newBuilder()
            .withName("doc_id")
            .withDataType(DataType.VarChar)
            .withMaxLength(128)
            .withPrimaryKey(true)
            .build();
        
        FieldType vectorField = FieldType.newBuilder()
            .withName("vector")
            .withDataType(DataType.FloatVector)
            .withDimension(dimension)
            .build();
        
        FieldType contentTypeField = FieldType.newBuilder()
            .withName("content_type")
            .withDataType(DataType.VarChar)
            .withMaxLength(32)
            .build();
        
        FieldType titleField = FieldType.newBuilder()
            .withName("title")
            .withDataType(DataType.VarChar)
            .withMaxLength(512)
            .build();
        
        FieldType contentField = FieldType.newBuilder()
            .withName("content")
            .withDataType(DataType.VarChar)
            .withMaxLength(65535)
            .build();
        
        FieldType metadataField = FieldType.newBuilder()
            .withName("metadata")
            .withDataType(DataType.JSON)
            .build();
        
        FieldType createTimeField = FieldType.newBuilder()
            .withName("create_time")
            .withDataType(DataType.Int64)
            .build();
        
        CreateCollectionParam createCollectionParam = CreateCollectionParam.newBuilder()
            .withCollectionName(collectionName)
            .withShardsNum(2)
            .addFieldType(docIdField)
            .addFieldType(vectorField)
            .addFieldType(contentTypeField)
            .addFieldType(titleField)
            .addFieldType(contentField)
            .addFieldType(metadataField)
            .addFieldType(createTimeField)
            .build();
        
        R<RpcStatus> response = milvusClient.createCollection(createCollectionParam);
        
        if (response.getStatus() != 0) {
            throw new RuntimeException("创建集合失败: " + response.getMessage());
        }
        
        log.info("创建集合成功: {}", collectionName);
    }
    
    /**
     * 创建索引
     */
    private void createIndex() {
        CreateIndexParam indexParam = CreateIndexParam.newBuilder()
            .withCollectionName(collectionName)
            .withFieldName("vector")
            .withIndexType(IndexType.IVF_FLAT)
            .withMetricType(MetricType.COSINE)
            .withExtraParam("{\"nlist\":1024}")
            .build();
        
        R<RpcStatus> response = milvusClient.createIndex(indexParam);
        
        if (response.getStatus() != 0) {
            log.warn("创建索引失败: {}", response.getMessage());
        } else {
            log.info("创建索引成功");
        }
    }
    
    /**
     * 加载集合到内存
     */
    private void loadCollection() {
        LoadCollectionParam loadParam = LoadCollectionParam.newBuilder()
            .withCollectionName(collectionName)
            .build();
        
        R<RpcStatus> response = milvusClient.loadCollection(loadParam);
        
        if (response.getStatus() != 0) {
            log.warn("加载集合失败: {}", response.getMessage());
        } else {
            log.info("加载集合到内存成功");
        }
    }
    
    /**
     * 插入向量文档
     * 
     * @param vectorDocument 向量文档
     * @return 是否成功
     */
    public boolean insert(VectorDocument vectorDocument) {
        if (!enabled || milvusClient == null) {
            log.debug("向量数据库未启用，跳过插入");
            return false;
        }
        
        try {
            List<String> docIds = Collections.singletonList(vectorDocument.getDocId());
            List<List<Float>> vectors = Collections.singletonList(vectorDocument.getVector());
            List<String> contentTypes = Collections.singletonList(vectorDocument.getContentType());
            List<String> titles = Collections.singletonList(vectorDocument.getTitle() != null ? 
                vectorDocument.getTitle() : "");
            List<String> contents = Collections.singletonList(vectorDocument.getContent() != null ? 
                vectorDocument.getContent() : "");
            
            // 构建元数据JSON
            Map<String, Object> metadata = vectorDocument.getMetadata() != null ? 
                vectorDocument.getMetadata() : new HashMap<>();
            List<String> metadataJson = Collections.singletonList(
                com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(metadata)
            );
            
            List<Long> createTimes = Collections.singletonList(
                vectorDocument.getCreateTime() != null ? 
                vectorDocument.getCreateTime().getTime() : System.currentTimeMillis()
            );
            
            InsertParam insertParam = InsertParam.newBuilder()
                .withCollectionName(collectionName)
                .withFields(Arrays.asList(
                    new InsertParam.Field("doc_id", docIds),
                    new InsertParam.Field("vector", vectors),
                    new InsertParam.Field("content_type", contentTypes),
                    new InsertParam.Field("title", titles),
                    new InsertParam.Field("content", contents),
                    new InsertParam.Field("metadata", metadataJson),
                    new InsertParam.Field("create_time", createTimes)
                ))
                .build();
            
            R<MutationResult> response = milvusClient.insert(insertParam);
            
            if (response.getStatus() == 0) {
                log.debug("向量文档插入成功，docId: {}", vectorDocument.getDocId());
                return true;
            } else {
                log.error("向量文档插入失败: {}", response.getMessage());
                return false;
            }
            
        } catch (Exception e) {
            log.error("向量文档插入异常", e);
            return false;
        }
    }
    
    /**
     * 批量插入向量文档
     * 
     * @param vectorDocuments 向量文档列表
     * @return 成功插入的数量
     */
    public int batchInsert(List<VectorDocument> vectorDocuments) {
        if (!enabled || milvusClient == null || vectorDocuments == null || vectorDocuments.isEmpty()) {
            return 0;
        }
        
        int successCount = 0;
        for (VectorDocument doc : vectorDocuments) {
            if (insert(doc)) {
                successCount++;
            }
        }
        
        log.info("批量插入完成，总数: {}, 成功: {}", vectorDocuments.size(), successCount);
        return successCount;
    }
    
    /**
     * 相似度搜索
     * 
     * @param queryVector 查询向量
     * @param topK 返回结果数量
     * @return 搜索结果
     */
    public List<Map<String, Object>> similaritySearch(List<Float> queryVector, int topK) {
        if (!enabled || milvusClient == null) {
            log.debug("向量数据库未启用，返回空结果");
            return Collections.emptyList();
        }
        
        try {
            SearchParam searchParam = SearchParam.newBuilder()
                .withCollectionName(collectionName)
                .withMetricType(MetricType.COSINE)
                .withOutFields(Arrays.asList("doc_id", "content_type", "title", "content", "metadata"))
                .withTopK(topK)
                .withVectors(Collections.singletonList(queryVector))
                .withVectorFieldName("vector")
                .withParams("{\"nprobe\":16}")
                .build();
            
            R<SearchResults> response = milvusClient.search(searchParam);
            
            if (response.getStatus() != 0) {
                log.error("搜索失败: {}", response.getMessage());
                return Collections.emptyList();
            }
            
            // 解析搜索结果
            SearchResultsWrapper wrapper = new SearchResultsWrapper(response.getData().getResults());
            List<Map<String, Object>> results = new ArrayList<>();
            
            for (int i = 0; i < wrapper.getRowRecords().size(); i++) {
                Map<String, Object> result = new HashMap<>();
                result.put("score", wrapper.getIDScore(i).getScore());
                result.put("docId", wrapper.getFieldData("doc_id", i));
                result.put("contentType", wrapper.getFieldData("content_type", i));
                result.put("title", wrapper.getFieldData("title", i));
                result.put("content", wrapper.getFieldData("content", i));
                result.put("metadata", wrapper.getFieldData("metadata", i));
                results.add(result);
            }
            
            log.debug("相似度搜索完成，返回 {} 个结果", results.size());
            return results;
            
        } catch (Exception e) {
            log.error("相似度搜索异常", e);
            return Collections.emptyList();
        }
    }
    
    /**
     * 根据文本进行相似度搜索
     * 
     * @param queryText 查询文本
     * @param topK 返回结果数量
     * @return 搜索结果
     */
    public List<Map<String, Object>> searchByText(String queryText, int topK) {
        List<Float> queryVector = embeddingService.embed(queryText);
        return similaritySearch(queryVector, topK);
    }
    
    /**
     * 删除向量文档
     * 
     * @param docId 文档ID
     * @return 是否成功
     */
    public boolean delete(String docId) {
        if (!enabled || milvusClient == null) {
            return false;
        }
        
        try {
            String expr = String.format("doc_id == \"%s\"", docId);
            
            DeleteParam deleteParam = DeleteParam.newBuilder()
                .withCollectionName(collectionName)
                .withExpr(expr)
                .build();
            
            R<MutationResult> response = milvusClient.delete(deleteParam);
            
            if (response.getStatus() == 0) {
                log.debug("删除向量文档成功，docId: {}", docId);
                return true;
            } else {
                log.error("删除向量文档失败: {}", response.getMessage());
                return false;
            }
            
        } catch (Exception e) {
            log.error("删除向量文档异常", e);
            return false;
        }
    }
    
    /**
     * 清空集合
     */
    public void clear() {
        if (!enabled || milvusClient == null) {
            return;
        }
        
        try {
            DropCollectionParam dropParam = DropCollectionParam.newBuilder()
                .withCollectionName(collectionName)
                .build();
            
            R<RpcStatus> response = milvusClient.dropCollection(dropParam);
            
            if (response.getStatus() == 0) {
                log.info("清空集合成功");
                // 重新创建集合
                createCollection();
                createIndex();
                loadCollection();
            }
            
        } catch (Exception e) {
            log.error("清空集合异常", e);
        }
    }
}
