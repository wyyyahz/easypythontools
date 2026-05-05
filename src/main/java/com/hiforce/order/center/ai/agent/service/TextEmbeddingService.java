package com.hiforce.order.center.ai.agent.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * 文本嵌入服务
 * 用于将文本转换为向量表示
 */
@Slf4j
@Service
public class TextEmbeddingService {
    
    // 默认向量维度
    private static final int DEFAULT_DIMENSION = 768;
    
    /**
     * 将文本转换为向量
     * 
     * @param text 输入文本
     * @return 向量表示
     */
    public List<Float> embed(String text) {
        if (text == null || text.isEmpty()) {
            log.warn("输入文本为空，返回零向量");
            return generateZeroVector(DEFAULT_DIMENSION);
        }
        
        try {
            // TODO: 这里可以接入真实的embedding模型
            // 例如：OpenAI Embeddings、HuggingFace Transformers、文心一言等
            // 目前使用基于哈希的简单模拟实现
            
            log.debug("生成文本向量，文本长度: {}", text.length());
            
            // 使用改进的TF-IDF模拟向量生成
            return generateSimulatedEmbedding(text, DEFAULT_DIMENSION);
            
        } catch (Exception e) {
            log.error("文本向量化失败", e);
            return generateZeroVector(DEFAULT_DIMENSION);
        }
    }
    
    /**
     * 批量文本向量化
     * 
     * @param texts 文本列表
     * @return 向量列表
     */
    public List<List<Float>> batchEmbed(List<String> texts) {
        List<List<Float>> vectors = new ArrayList<>();
        for (String text : texts) {
            vectors.add(embed(text));
        }
        return vectors;
    }
    
    /**
     * 获取向量维度
     * 
     * @return 向量维度
     */
    public int getDimension() {
        return DEFAULT_DIMENSION;
    }
    
    /**
     * 生成模拟的文本嵌入向量
     * 使用改进的字符级特征提取
     * 
     * @param text 输入文本
     * @param dimension 向量维度
     * @return 归一化的向量
     */
    private List<Float> generateSimulatedEmbedding(String text, int dimension) {
        float[] vector = new float[dimension];
        
        // 方法1: 基于字符hash的特征分布
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            int hash = Character.hashCode(c);
            int index = Math.abs(hash) % dimension;
            vector[index] += 1.0f;
        }
        
        // 方法2: 基于n-gram的特征（bigram）
        for (int i = 0; i < text.length() - 1; i++) {
            String bigram = text.substring(i, i + 2);
            int hash = bigram.hashCode();
            int index = Math.abs(hash) % dimension;
            vector[index] += 0.5f;
        }
        
        // 方法3: 添加文本长度特征
        int lengthIndex = Math.min(text.length(), dimension - 1);
        vector[lengthIndex] += 2.0f;
        
        // L2归一化
        float norm = 0.0f;
        for (float v : vector) {
            norm += v * v;
        }
        norm = (float) Math.sqrt(norm);
        
        if (norm > 0) {
            for (int i = 0; i < dimension; i++) {
                vector[i] /= norm;
            }
        }
        
        // 转换为List<Float>
        List<Float> result = new ArrayList<>(dimension);
        for (float v : vector) {
            result.add(v);
        }
        
        return result;
    }
    
    /**
     * 生成零向量
     * 
     * @param dimension 向量维度
     * @return 零向量
     */
    private List<Float> generateZeroVector(int dimension) {
        List<Float> zeroVector = new ArrayList<>(dimension);
        for (int i = 0; i < dimension; i++) {
            zeroVector.add(0.0f);
        }
        return zeroVector;
    }
    
    /**
     * 计算两个向量的余弦相似度
     * 
     * @param vector1 向量1
     * @param vector2 向量2
     * @return 余弦相似度 [-1, 1]
     */
    public double cosineSimilarity(List<Float> vector1, List<Float> vector2) {
        if (vector1 == null || vector2 == null || vector1.size() != vector2.size()) {
            return 0.0;
        }
        
        double dotProduct = 0.0;
        double norm1 = 0.0;
        double norm2 = 0.0;
        
        for (int i = 0; i < vector1.size(); i++) {
            double v1 = vector1.get(i);
            double v2 = vector2.get(i);
            dotProduct += v1 * v2;
            norm1 += v1 * v1;
            norm2 += v2 * v2;
        }
        
        if (norm1 == 0 || norm2 == 0) {
            return 0.0;
        }
        
        return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
    }
}
