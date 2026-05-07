import pandas as pd
import re

# 读取文件
df = pd.read_excel('Agoda_武汉酒店_最低价补充_最终版_填充后.xlsx')

# 提取品牌（常见品牌列表，可自行扩充）
brand_keywords = ['7天', '汉庭', '麗枫', '维也纳', '全季', '桔子', '宜尚', '丽怡', '锦江', '如家',
                  '城市便捷', '你好', '柏曼', '莫林', '凯里亚德', '希尔顿', '喜来登', '万豪', '洲际',
                  '皇冠假日', '假日', '智选假日', '亚朵', '丽顿', '丽橙', '希岸', '喆啡', '星程', '白玉兰']

def extract_brand(name):
    for b in brand_keywords:
        if b in name:
            return b
    # 若无匹配，取第一个连续中文字符（至少2字符）
    match = re.search(r'[\u4e05-\u9fa5]{2,}', name)
    return match.group(0) if match else name

df['品牌'] = df['酒店名称'].apply(extract_brand)

# 先按品牌+区域+星级 分组计算平均价格
group_keys = ['品牌', '区域位置', '星级']
price_means = df[df['最低价(CNY)'].notna()].groupby(group_keys)['最低价(CNY)'].mean().to_dict()

# 定义获取填充价格的函数
def get_fill_price(row):
    if pd.notna(row['最低价(CNY)']):
        return row['最低价(CNY)']
    # 尝试 品牌+区域+星级
    key = (row['品牌'], row['区域位置'], row['星级'])
    if key in price_means:
        return price_means[key]
    # 尝试 品牌+星级
    key2 = (row['品牌'], row['星级'])
    price_means2 = df[df['最低价(CNY)'].notna()].groupby(['品牌', '星级'])['最低价(CNY)'].mean().to_dict()
    if key2 in price_means2:
        return price_means2[key2]
    # 尝试 品牌
    key3 = row['品牌']
    price_means3 = df[df['最低价(CNY)'].notna()].groupby('品牌')['最低价(CNY)'].mean().to_dict()
    if key3 in price_means3:
        return price_means3[key3]
    # 最后尝试 区域+星级
    key4 = (row['区域位置'], row['星级'])
    price_means4 = df[df['最低价(CNY)'].notna()].groupby(['区域位置', '星级'])['最低价(CNY)'].mean().to_dict()
    if key4 in price_means4:
        return price_means4[key4]
    # 仍然为空则返回空
    return None

df['最低价(CNY)'] = df.apply(get_fill_price, axis=1)
# 删除辅助列
df.drop('品牌', axis=1, inplace=True)

# 保存
df.to_excel('Agoda_武汉酒店_最低价补充_最终版_智能填充.xlsx', index=False)
print('填充完成，空值数量：', df['最低价(CNY)'].isna().sum())