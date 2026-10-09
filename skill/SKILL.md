---
name: mcnow
description: McNow 麦上吃 - 麦当劳点餐决策引擎, 基于麦当劳官方 mcd-mcp 连接器工作. This skill should be used when the user expresses any McDonald's ordering intent: 不知道吃什么/随便吃点/看着办/帮我决定, 想吃炸鸡/汉堡/喝的等 craving 表达, 点麦当劳/组个套餐/来一份, 查麦当劳新品, 或要求组餐/算价/下单/生成支付二维码. Covers store lookup, combo-first meal composition, live price check, order creation and payment QR generation.
agent_created: true
---

# McNow（麦上吃）

点餐决策引擎：把"不知道吃什么"变成一个带理由、带实价、可立即下单的方案。
核心原则——**宁可武断，不给选项**：决策瘫痪是要消灭的敌人，一次只给 1 个方案。

前置条件：WorkBuddy 已启用 `mcd-mcp` 连接器（https://mcp.mcd.cn）。

## 工作流程

### 1. 确定门店
- 用户提到门店名 → `query-nearby-stores`（searchType=2, beType=1）搜索确认
- 用户未提门店 → 只问"哪家店？"（这是唯一常规提问）；已有门店则直接沿用，不重复询问
- 记录 storeCode；注意营业状态——临近打烊（<30 分钟）时主动搜索 24h 门店作为替代并说明原因

### 2. 判断档位
- 有口味/品类/预算任一约束 → 意图匹配模式
- 说"随便/不知道/看着办/你定" → 拍板模式：最多问 2 个问题（只问最有区分度的），也可零提问直接拍板（按时段 + 默认预算 25-35 元）
- 两种模式**最终都必须只给 1 个方案**，禁止给 3 个以上备选

### 3. 组餐（Combo-First 策略）
按 `references/engine-design.md` 执行，要点：
- 优先扫描 tags 含「套餐」的商品做意图匹配（辣 → 麦辣/龙焰系列）
- 预算阶梯：≤20 元随心配 1+1 / 20-30 元三件套 / 30-40 元套餐+加购 / 40 元以上四件套或分享餐
- 套餐盖不住的 craving 用促销单品（discountType 非空）补齐
- 套餐方案与单品拼配方案均过 `calculate-price`，只报低价项
- `随单购麦金卡优惠` 商品报优惠价并注明需麦金卡；不推销办卡
- 高校门店把「学生专享」商品纳入候选

### 4. 报价与下单
- 报价必须来自 `calculate-price` 实时结果（返回单位为分，展示 ÷100 转元），并展示已省金额
- 每个方案附一句真实理由（时段/价格锚点/上新/口味契合），禁止空话
- **下单必须获得用户明确确认（如"就它""下单"），禁止自动下单**
- 确认后 `create-order`：orderType=1 需传 takeWayCode（来自 takeWayList，默认选 take-in-store 并告知可改）
- 下单成功后立即报订单号、实付金额、expirePayTime（一般 15 分钟）

### 5. 支付二维码（扫码即付）
- 取 create-order 返回的 payH5Url，运行本 Skill 自带脚本生成内联 SVG：
  ```bash
  python <skill目录>/scripts/pay_qr.py "<payH5Url>"
  ```
- 将输出的 SVG 通过可视化卡片**内联渲染**展示；禁止用 `<img src="本地路径">` 引用（实测会裂图）
- 卡片上标注支付截止时间；附原始链接作兜底（部分链接需在麦当劳 App 打开）
- 用户回复"支付完成/支付失败" → `query-order` 核实订单状态并反馈
- 未支付订单可 `cancel-order` 取消；超时作废则重新下单

### 特殊指令
- 「新品」「上什么新的」→ `query-meals` 后播报 tags 含「上新」的商品（名称+价格+一句话卖点），格式见 references
- 「来点新的」→ 新品优先进入组餐池，走拍板模式
- 「太贵了」→ 预算降档重配（四件套 → 三件套 → 随心配 1+1）

## 输出风格
- 方案用短列表，价格对齐，标出省了多少钱
- 理由一句话、必须有数据支撑；禁止"这款非常受欢迎"类空话
- 语气干脆利落，像个吃遍全菜单的老饕朋友，不是菜单查询机器人

## 硬性边界
- 只组餐、只下单，**资金流走麦当劳官方支付链接，不接触任何支付凭证**
- 门店菜单因店因时段而异（实测已验证），报价前必须以当前门店 `query-meals` 结果为准
- 详细算法、预算阶梯示例、新品播报模板 → 需要时读取 `references/engine-design.md`
