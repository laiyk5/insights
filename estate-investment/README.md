# 房价地图

分析全国各城市买房 vs 租房的经济性，并用交互式地图可视化。

## 项目做什么

1. **数据采集**: 从 [禧泰数据](https://www.cityre.cn) 抓取全国 322 个城市的租房和二手房挂牌数据
2. **经济性计算**: 比较"全款买房持有 30 年"与"租房 30 年"的净收益
3. **交互可视化**: 在地图上展示各城市的租金水平、房价水平、以及买房/租房哪种更划算

## 核心结论（默认假设）

假设条件：
- 持有/租住周期：30 年
- 资金机会成本：年化 4%（债基收益）
- 房价年增值：**2%**

在此假设下：
- **买房更划算**：21 个城市
- **租房更划算**：299 个城市

买房最划算的城市通常是低房价、租金收益率高的城市（如林芝、阿勒泰、本溪）。
一线及强二线城市（深圳、上海、北京、厦门、杭州）由于租售比极高，租房明显更优。

> 结论对房价增值假设极度敏感：若假设增值 0%，全部 320 个城市租房更优；若假设增值 4%，全部城市买房更优。

## 租金回报率

**租金回报率 = 年租金 / 房价 × 100%**

全国 320 个城市平均租金回报率：**3.25%**

| 类别 | 城市 | 回报率 |
|------|------|--------|
| **最高** | 阿勒泰 | 6.91% |
| | 林芝 | 6.76% |
| | 鹤岗 | 6.30% |
| **最低** | 深圳 | 1.36% |
| | 厦门 | 1.45% |
| | 东莞 | 1.50% |

**规律**：
- 低房价城市（鹤岗、阿勒泰等）租金回报率普遍在 5% 以上，接近理财产品收益
- 一线城市（深圳 1.36%、上海 1.75%、北京 ~2%）回报率极低，说明房价中包含了大量升值预期
- 国际上一般认为 4-6% 是合理租金回报率区间，以此标准中国大部分二三线城市已具备投资价值

## 快速开始

```bash
# 安装依赖
uv sync

# 抓取最新数据
uv run scripts/fetch_city_rent.py
uv run scripts/fetch_city_price.py

# 生成各种分析地图
uv run scripts/calculate_buy_vs_rent.py      # 买房 vs 租房净收益
uv run scripts/calculate_rental_yield.py     # 租金回报率
uv run scripts/visualize_city_rent.py        # 城市租金水平

# 查看结果
open outputs/buy_vs_rent_map.html
open outputs/rental_yield_map.html
```

## 项目结构

```
.
├── data/                          # 原始及中间数据
│   ├── city_rent.json            # 322 城市租房数据
│   ├── city_price.json           # 322 城市二手房价格数据
│   ├── buy_vs_rent.json          # 买/租经济性计算结果
│   ├── rental_yield.json         # 租金回报率计算结果
│   ├── city_coords_cache.json    # 城市坐标缓存（Nominatim）
│   ├── shenzhen.json             # 深圳各区模拟数据
│   └── hongkong.json             # 香港各区模拟数据
│
├── outputs/                       # 生成的可视化 HTML
│   ├── buy_vs_rent_map.html      # 买房 vs 租房净收益地图
│   ├── rental_yield_map.html     # 租金回报率地图
│   ├── city_rent_map.html        # 城市租金水平地图
│   └── estate_price_heatmap.html # 深圳+香港房价热力图
│
├── scripts/                       # 可执行脚本
│   ├── fetch_city_rent.py        # 抓取租房数据
│   ├── fetch_city_price.py       # 抓取房价数据
│   ├── calculate_buy_vs_rent.py  # 计算并生成买/租对比地图
│   ├── calculate_rental_yield.py # 计算并生成租金回报率地图
│   ├── visualize_city_rent.py    # 生成租金地图
│   ├── generate_heatmap.py       # 生成深圳/香港热力图
│   └── visualization.py          # 底层热力图绘制
│
├── insights/estate/               # 核心模型
│   ├── models.py                 # 数据模型（EstatePrice, CityRent 等）
│   └── mock_data.py              # 数据加载器（从 JSON 加载静态数据）
│
├── pyproject.toml                 # 项目配置
└── uv.lock                        # 依赖锁定
```

## 数据来源

### 城市租房数据
- **来源**: [禧泰数据 (cityre.cn)](https://www.cityre.cn/target/houseRentShow)
- **指标**: 各城市租房挂牌数量、单位面积月租金（元/月/平米）
- **API**: `GET https://www.cityre.cn/target/gethousingPriceList?queryType=houseRent`
- **数据文件**: `data/city_rent.json`
- **覆盖范围**: 全国 322 个城市

### 城市二手房价格数据
- **来源**: [禧泰数据 (cityre.cn)](https://www.cityre.cn/target/housingPriceShow)
- **指标**: 各城市二手房挂牌数量、单位面积均价（元/平米）
- **API**: `GET https://www.cityre.cn/target/gethousingPriceList?queryType=housingPrice`
- **数据文件**: `data/city_price.json`
- **覆盖范围**: 全国 322 个城市

### 深圳/香港房产模拟数据
- **来源**: 随机生成的模拟数据
- **用途**: 用于测试 district-level 热力图可视化
- **数据文件**: `data/shenzhen.json`, `data/hongkong.json`
- **说明**: 基于各区域历史成交价格区间估算，非真实数据

## 计算模型

### 买房（全款）
- **成本**: 房价 × (1 + 4%)^30  —— 房价加上 30 年复利机会成本
- **收益**: 房价 × (1 + 增值率)^30  —— 30 年后房产残值
- **净收益**: 残值 - 总成本

### 租房
- **成本**: 月租金 × 12 × 30  —— 30 年累计租金
- **收益**: 0
- **净收益**: -累计租金

### 买房 vs 租房
净收益差 = (买房净收益) - (租房净收益) = 残值 - 总成本 + 累计租金

> 注：当前模型基于全款买房简化计算，未考虑贷款杠杆、首付比例、月供现金流等因素。后续可扩展为更精细的贷款买房模型。
