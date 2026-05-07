import pandas as pd
import numpy as np

# 读取原始 Excel
df = pd.read_excel('Agoda_武汉酒店_2026-06-05.xlsx', sheet_name='12-总数居（7073条）')

# 定义星级补充函数
def infer_star(name, existing_star):
    if pd.notna(existing_star) and str(existing_star).strip() != '':
        return existing_star
    name = str(name).lower()
    # 豪华/五星品牌
    luxury = ['丽思卡尔顿', '瑞华', '费尔蒙', '威斯汀', '万豪', '喜来登', '洲际', '君悦', '凯悦', '索菲特', '皇冠假日', '希尔顿', '香格里拉', '卓尔万豪', '马哥孛罗', '万达瑞华', '富力万达', '襄投万豪', '世茂希尔顿', '光明万丽', '锦江国际', '新华voco', '新世界', '江城明珠豪生', '欧亚会展', '金盾舒悦', '巴公邸', '丽笙', '威斯汀', '凯悦', '朗廷', '温德姆', '铂瑞', '碧桂园凤凰', '曲水兰亭']
    if any(k in name for k in luxury):
        return 5
    # 中高端品牌
    midhigh = ['亚朵', '全季', '丽枫', '维也纳', '桔子', '宜尚', '丽怡', '凯里亚德', '漫心', '美居', '美仑', '万枫', '福朋', '智选假日', '希尔顿惠庭', '欢朋', '锦江都城', '丽顿', '丽橙', '潮漫', '莫林', '格菲', '宜必思', '凯瑞', '雅斯特', '白玉兰', '星程', '你好', '城市精选', '缤跃', '希岸', '喆啡', '非繁', '秋果', '柏曼', '康铂', '宜必思尚品', '城际', '美悦', '建国璞隐', '臻程', '枫渡']
    if any(k in name for k in midhigh):
        return 4
    # 经济连锁
    economy = ['7天', '汉庭', '如家', '城市便捷', '锦江之星', '速8', '精途', '贝壳', '海友', '派柏', '莫泰', '99inn', '怡莱', '布丁', '尚客优', '骏怡', '易佰']
    if any(k in name for k in economy):
        return 3
    # 民宿/公寓/青旅/招待所
    budget = ['民宿', '公寓', '青年旅舍', '旅馆', '招待所', '客栈', '青旅', '胶囊', '太空舱', '电竞', '影院', 'loft', 'homestay', 'hostel', 'apartment', '客栈', '山庄', '别墅']
    if any(k in name for k in budget):
        return 2
    # 其他默认
    return 3

# 补充星级
df['星级'] = df.apply(lambda row: infer_star(row['酒店名称'], row['星级']), axis=1)

# 保存为新 Excel
df.to_excel('Agoda_武汉酒店_星级补充.xlsx', index=False)
print("已生成 Agoda_武汉酒店_星级补充.xlsx")