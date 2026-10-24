# 麦当劳 MCP 集成说明

McNow 以官方麦当劳 MCP 提供的门店、菜单、价格和订单能力完成点餐决策。本文区分历史使用记录与本次新增的按需规则，避免把设计能力当成实测结果。

## 服务与配置

| 项目 | 内容 |
|---|---|
| 服务 | 麦当劳中国官方 `mcd-mcp` |
| 地址 | `https://mcp.mcd.cn` |
| 协议 | Streamable HTTP，Bearer Token 认证 |
| 文档 | [官方 MCP 使用指南](https://github.com/M-China/mcd-mcp-server) |
| 脱敏配置 | [mcp-config.example.json](mcp-config.example.json) |

示例只使用 `${MCD_MCP_TOKEN}` 占位符；宿主是否自动展开环境变量须核实。真实凭证只进入本地配置。脚本默认路径为 `~/.workbuddy/mcp.json`，应先从 WorkBuddy 配置入口核实，不同版本可用 `--config` 指定。

## 工具与业务价值

参数、必填字段、单位和可选值以当前连接器 schema 为准。以下是工作流摘要，不是可直接复制的完整请求体。

| 工具 | 调用时机 | 用途与边界 | 验证状态 |
|---|---|---|---|
| `query-nearby-stores` | 缺门店或核实营业信息 | 获取门店编码、营业状态／时段；同名门店须确认 | 历史实测 |
| `query-meals` | 每次门店／时段变化后的组餐 | 只从当前门店可售菜单选择，识别套餐、新品、促销 | 历史实测 |
| `query-meal-detail` | 套餐或商品有必选规格／替换项 | 获取真实组成和配置，再提交试算 | 新增按需规则，未重跑 |
| `query-store-coupons` | 用户要求用已有券／省钱 | 核实当前门店与用户资格，不自动领券、购卡 | 新增按需规则，未重跑 |
| `calculate-price` | 输出确定报价前、确认后复验 | 计算含优惠的总价，读取取餐方式；只比较同等满足需求的候选 | 基础试算历史实测；新增复验未重跑 |
| `create-order` | 当前完整方案被明确确认且复验一致 | 沿用相同商品配置、门店、券及取餐方式，创建一次 | 基础创建历史实测；新增规则未重跑 |
| `query-order` | 支付完成／失败、重复请求或状态不明 | 以工具结果确认状态，不凭用户描述声称已支付 | 状态处理规则，未重跑 |
| `order-list` | 创建超时、无法确定是否已创建 | 核对近期同配置订单，不能排除已创建就停止重试 | 新增异常分支，未实测 |
| `cancel-order` | 用户明确取消具体订单 | 根据实际状态决定是否可取消，按返回值反馈 | 取消规则，未实测 |
| `list-nutrition-foods` | 明确要求热量／蛋白等目标 | 匹配规格和数量；缺数据时不精算、不保证过敏安全 | 可选能力，未实测 |
| `campaign-calendar` | 用户主动问活动 | 区分活动日期和实际可售菜单，宣传价不能代替实付 | 可选能力，未实测 |

外送需要 `delivery-query-addresses`、`delivery-query-stores` 等实际可用工具及配送费试算。本版本以到店取餐为主，外送未完成实测，不自动新增地址。

## 调用流程

```text
query-nearby-stores → storeCode 与已确认地点
          ↓
query-meals → 必要的 query-meal-detail / query-store-coupons
          ↓
套餐优先搜索 → 套餐候选与同需求单品候选
          ↓
calculate-price → 唯一方案、真实实付与一句理由
          ↓
用户确认 → 同配置复验（有变化则重新确认）
          ↓
create-order（一次）→ 订单号、expirePayTime、payH5Url
          ↓
本地二维码或原始官方链接 → 用户自行支付 → query-order
```

组餐策略见 [engine-design.md](skill/references/engine-design.md)。创建超时后先核实状态，不能盲目再下；二维码失败保留原订单。完整异常规则见 [order-lifecycle.md](skill/references/order-lifecycle.md)。

## 历史真实使用记录

原仓库的 [WorkBuddy 开发纪要](workbuddy.md) 记录了 2026-10-09 的门店查询、菜单、试算、创建订单及支付链接／二维码验证：

- 炸鸡与饮料需求 → 蘸酱炸鸡 ¥11.9 + 茉莉奶绿雪冰 ¥9.9 = **¥21.8**，当次记录原价 ¥34.9，优惠 ¥13.1。
- 当次菜单与试算结果一致，促销生效；这不能推导出所有优惠券都能自动叠加。
- 当次创建返回支付链接，二维码由本地脚本生成。不能据此声称已支付成功或永远有固定的 15 分钟支付期限。

这些是历史纪要，本次未连接真实账户复核，也未重新创建订单。今日库存、资格、价格、时效与状态全部以当前官方返回为准。

## 本次离线验证范围

[`scripts/verify.py`](scripts/verify.py) 不联网，不读取真实配置或凭证，使用临时目录和合成数据验证：

- 必交材料、Skill 元数据与本地文档链接；有限模式的疑似凭证扫描。
- 配置合并、备份、幂等、非法结构拒绝、原子替换失败保护和 dry-run。
- HTTPS 链接格式拒绝、SVG XML、二维码矩阵完整性、四模块留白、长链接布局和 stdin 输出。

自动检查不能证明宿主模型会正确遵循 Skill，也不是完整安全审计。真实交互回放清单见 [acceptance-cases.md](skill/references/acceptance-cases.md)。
