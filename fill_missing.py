import pandas as pd
import numpy as np

# 读取原Excel文件
df = pd.read_excel('Agoda_武汉酒店_星级补充_最终版.xlsx')

# 找出用户评分为空的行
mask_missing = df['用户评分'].isna() | (df['用户评分'] == '')

# 对于每个缺失的评分，根据酒店名称从已有评分中查找匹配值
# 先计算每个酒店名称的非空评分的平均值（保留一位小数）
name_to_avg_score = df[df['用户评分'].notna() & (df['用户评分'] != '')].groupby('酒店名称')['用户评分'].mean().round(1)

# 填充缺失值
df.loc[mask_missing, '用户评分'] = df.loc[mask_missing, '酒店名称'].map(name_to_avg_score)

# 如果仍然有缺失（即酒店名称从未出现过评分），则保留NaN
# 保存为新文件
df.to_excel('Agoda_武汉酒店_星级补充_填充后.xlsx', index=False)

print("处理完成！新文件已保存为 'Agoda_武汉酒店_星级补充_填充后.xlsx'")