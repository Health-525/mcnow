<div align="center">

# 麦上吃 · McNow

**不想选？麦上吃。**

一个跑在 WorkBuddy 里的麦当劳点餐决策引擎 Skill
基于麦当劳官方 [mcd-mcp](https://github.com/M-China/mcd-mcp-server) ｜ 全程用 [WorkBuddy](https://www.workbuddy.cn) 开发

[![contest](https://img.shields.io/badge/麦当劳MCP创意开发大赛-参赛作品-red)](https://github.com/M-China/mcd-developer-innovation-challenge)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![skill](https://img.shields.io/badge/skill--creator-校验通过-blue)](skill/SKILL.md)

</div>

## 快速开始

**1. 申请 MCP Token** → [麦当劳 MCP Server 指南](https://github.com/M-China/mcd-mcp-server)

**2. 一键配置**（自动写入 WorkBuddy MCP 配置，幂等、自动备份、不动其他连接器）：

```bash
python skill/scripts/setup_mcp.py <你的MCP_TOKEN>
```

**3. 启用并开聊**：WorkBuddy →【连接器】→【自定义连接器】→ 启用 mcd-mcp，然后：

```text
「不知道吃啥，25 块以内，看着办」
「想吃炸鸡，配点喝的」
「最近上什么新品了？」
```

确认方案后自动下单，支付二维码直接出现在对话里，扫码即付。支付走麦当劳官方通道，Skill 不接触任何资金凭证。

## 它是什么样子的

以下是一次**真实点餐**的完整记录（开发当晚 22:51，未删减）：

```text
人：我不知道吃什么

麦上吃：好，拍板模式。先说个要紧的——亚青村店 23:00 打烊，
        只剩 9 分钟，来不及了。旁边地铁站店 24 小时营业，切过去。

        （拉取门店菜单，扫描套餐池）

麦上吃：决定了，就它，不用再想：
        🍗 蘸酱炸鸡（韩式芝士酱·上新）   ¥11.9
        🥤 茉莉奶绿雪冰（促销）           ¥9.9
        🥠 黑洋酥小圆子风味派（本周新品） ¥5.0
        合计 ¥26.8（原价 ¥44.9，省 ¥18.1）

        为什么是它：那家店快打烊了，这家 24 小时；炸鸡是你今晚
        自己点过名的；¥5 的派是塞给你的夜宵彩蛋。套餐池里唯一
        贴 craving 的麦辣鸡翅套餐 ¥36.5，比这套贵 ¥9.7，Pass。

        就它吗？确认就下单。
```

从"我不知道吃什么"到一张能扫的付款码，中间没有一次"请选择您想要的套餐"。

## 解决什么问题

翻菜单十分钟 → 心算套餐划不划算 → 关掉 App → 问朋友"吃什么" → 还是不知道。

问题不是没有好吃的，是**决策成本被转嫁给了饿着肚子的你**。

| 传统点餐 | 麦上吃 |
|---|---|
| 上百个 SKU 自己翻 | 说一句话，甚至不用说 |
| 套餐划不划算自己算 | 套餐优先 + 双向验价，只报低价方案 |
| 推荐列表永远有 5 个选项 | **只给 1 个方案，附一句真实理由** |
| 新品混在菜单第 4 屏 | 「上新」标签直达，一句话播报 |

## 核心设计

- **宁可武断，不给选项** — 最多问 2 个问题，最终只给 1 个方案
- **套餐优先（Combo-First）** — 先扫套餐再补单品；套餐方案与单品拼配都过 `calculate-price` 实时验价，只报便宜的那个；实测促销券自动叠加，报价即实付
- **时段感知** — 打烊前 30 分钟自动换 24 小时门店，并保证方案 15 分钟内取得到
- **新品雷达** — 基于菜单「上新」标签，一句话播报门店新品

## 工作原理

```text
query-nearby-stores ──→ storeCode + 营业时段（时段感知）
        │
        ▼
   query-meals ──→ 菜单池（套餐 / 上新 / 促销 / 麦金卡 标签）
        │
        ▼
  Combo-First 组餐引擎 ──→ 唯一方案 + 一句理由
        │
        ▼
  calculate-price ──→ 实价（含自动叠加优惠）+ 取餐方式
        │
     用户确认
        ▼
   create-order ──→ payH5Url（15 分钟时效）
        │
        ▼
  scripts/pay_qr.py ──→ 内联 SVG 支付二维码，扫码即付
```

## 文档

| 文档 | 内容 |
|---|---|
| [skill/SKILL.md](skill/SKILL.md) | Skill 定义（工作流程 + 硬性边界） |
| [skill/references/engine-design.md](skill/references/engine-design.md) | Combo-First 全策略：预算阶梯、麦金卡精算、新品播报模板 |
| [MCP_INTEGRATION.md](MCP_INTEGRATION.md) | 麦当劳 MCP 工具集成说明与实测记录 |
| [workbuddy.md](workbuddy.md) | WorkBuddy 开发对话上下文 |

## 项目结构

```text
mcnow/
├── CONTEST_DECLARATION.md        # 参赛声明（官方原样）
├── MCP_INTEGRATION.md
├── workbuddy.md
└── skill/
    ├── SKILL.md
    ├── references/
    │   └── engine-design.md
    └── scripts/
        ├── setup_mcp.py          # 一键写入 MCP 配置（只需 Token）
        └── pay_qr.py             # 支付二维码生成（内联 SVG）
```

## Roadmap

- [ ] 约束组餐：热量/蛋白目标求解
- [ ] 多人拆单：忌口分流，各自小票
- [ ] 特调黑话：去冰、免酱、多加酱

## License

MIT

---

*参赛作品，由参赛者独立开发，非麦当劳官方产品。餐品信息、价格及供应状态以麦当劳官方渠道实时结果为准。*
