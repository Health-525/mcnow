# MCP_INTEGRATION.md — 麦当劳 MCP 集成说明

本文档说明麦上吃实际使用的麦当劳 MCP Server、Tool、调用流程和业务价值。

## MCP Server

| 项 | 值 |
|---|---|
| Server | mcd-mcp（麦当劳中国官方） |
| URL | `https://mcp.mcd.cn` |
| 协议 | streamablehttp，Bearer Token 认证 |
| 申请方式 | [MCP Server GitHub 使用指南](https://github.com/M-China/mcd-mcp-server) |

## 工具清单与使用场景

### 1. query-nearby-stores — 门店定位
- **调用时机**：会话开始，确定用户门店
- **入参**：`searchType=2`（按城市+关键词搜索）、`beType=1`（到店自取）
- **产出**：storeCode（后续一切调用的前提）、营业状态、营业时段、预约时段
- **业务价值**：时段感知决策的数据源——"离打烊还有 16 分钟"的临场感来自这里

### 2. query-meals — 全菜单获取
- **调用时机**：组餐、新品播报、价格查询前
- **入参**：storeCode + orderType/beType
- **产出**：分类菜单 + 商品详情（code、名称、现价、原价、tags、discountType、随单购信息）
- **业务价值**：
  - `tags` 含「上新」→ 新品雷达的天然数据源
  - `currentPrice vs originalPrice` → 价格锚点与省钱计算
  - `tags` 含「套餐」→ 套餐优先策略的扫描池
  - `discountType="随单购麦金卡优惠"` → 麦金卡精算提示
- **关键发现**：各门店菜单存在真实差异（同一时刻两家门店 SKU 不同），"App 大菜单≠门店可点"是本 Skill 解决的真实痛点

### 3. calculate-price — 实价试算
- **调用时机**：输出任何方案前，验证真实总价（含促销）
- **入参**：storeCode + items[]（productCode, quantity）
- **产出**：原价/现价/优惠金额/商品明细 + takeWayList（堂食/外带选项）
- **业务价值**：让"省了 ¥13.1"这类承诺有据可依；套餐方案 vs 单品拼配方案的比价依据

### 4. create-order — 下单
- **调用时机**：用户明确确认方案后（强制二次确认）
- **支付机制**：MCP **不代收款**——create-order 成功后返回官方支付链接，用户扫码或打开麦当劳 App 完成支付；支付后回询"支付完成/支付失败"，再用 `query-order` 查询订单状态确认
- **退款/取消**：未支付可 `cancel-order` 取消
- **业务价值**：完成"一句话 → 吃到"的最后一步；资金流走麦当劳官方通道，AI 只组餐不碰钱，安全边界清晰

### 5. list-nutrition-foods — 营养数据（二期）
- 约束组餐（热量/蛋白目标）的数据源

## 调用流程图

```
query-nearby-stores ──→ storeCode
        │
        ▼
   query-meals ──→ 菜单池（套餐/新品/促销标签）
        │
        ▼
  AI 组餐引擎（Combo-First 策略，见 docs/engine-design.md）
        │
        ▼
  calculate-price ──→ 实价 + 已省金额 + 取餐方式
        │
   用户确认
        ▼
   create-order ──→ 下单成功
```

## 验证记录

2026-10-09 于真实门店完成全链路验证：

- 「想吃炸鸡，配点喝的，别太贵」→ 蘸酱炸鸡 ¥11.9 + 茉莉奶绿雪冰 ¥9.9 = **¥21.8**（原价 ¥34.9，省 ¥13.1）
- calculate-price 返回与菜单标价一致，促销自动生效

## 遵循的工具约定

- calculate-price 返回价格单位为"分"，展示时 ÷100 转为"元"
- 到店自取场景（beType=1）不传 beCode
- create-order 前必须获得用户明确确认
