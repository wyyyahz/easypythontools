import pandas as pd
import re
from rapidfuzz import fuzz

# 读取原文件
df = pd.read_excel('Agoda_武汉酒店_星级补充_最终版.xlsx')

# 定义清理酒店名称的函数（去除常见后缀）
def clean_name(name):
    name = str(name)
    # 去除括号内容（包括英文括号）
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'（[^）]*）', '', name)
    # 去除常见后缀词
    name = re.sub(r'(酒店|宾馆|旅馆|公寓|民宿|连锁|店|\s+)', '', name)
    return name.strip().lower()

# 计算完全匹配的平均分
full_match = df[df['用户评分'].notna()].groupby('酒店名称')['用户评分'].mean().round(1)

# 计算清理后名称的平均分（用于模糊匹配）
df['clean_name'] = df['酒店名称'].apply(clean_name)
clean_match = df[df['用户评分'].notna()].groupby('clean_name')['用户评分'].mean().round(1)

# 计算（星级 + 区域）组合的平均分
group_match = df[df['用户评分'].notna()].groupby(['星级', '区域位置'])['用户评分'].mean().round(1)

# 逐行填充
for idx, row in df.iterrows():
    if pd.isna(row['用户评分']) or row['用户评分'] == '':
        name = row['酒店名称']
        # 1. 完全匹配
        if name in full_match:
            df.at[idx, '用户评分'] = full_match[name]
            continue
        # 2. 模糊匹配（相似度 > 90）
        clean_n = row['clean_name']
        best_score = 0
        best_value = None
        for c_name, score in clean_match.items():
            sim = fuzz.ratio(clean_n, c_name)
            if sim > best_score and sim >= 90:
                best_score = sim
                best_value = score
        if best_value is not None:
            df.at[idx, '用户评分'] = best_value
            continue
        # 3. 使用同星级+同区域平均分
        key = (row['星级'], row['区域位置'])
        if key in group_match:
            df.at[idx, '用户评分'] = group_match[key]
            # 如果还为空，最后留空

# 删除临时列
df.drop('clean_name', axis=1, inplace=True)

# 保存
df.to_excel('Agoda_武汉酒店_星级补充_智能填充.xlsx', index=False)
print("已完成智能填充，新文件保存为：Agoda_武汉酒店_星级补充_智能填充.xlsx")