# workbuddy.md — WorkBuddy 开发对话上下文

> 本项目（McNow 麦上吃）全程使用 WorkBuddy 开发。本文档为开发对话的上下文纪要，用于核验 WorkBuddy 联动活动奖励条件。
> 开发时间：2026-10-09 22:35 ~ 23:12（北京时间），单次会话完成。

## 开发环境

- 工具：WorkBuddy（AI Agent 桌面端）
- 连接器：麦当劳官方 `mcd-mcp`（https://mcp.mcd.cn，streamablehttp + Bearer Token）
- 辅助技能：`skill-creator`（WorkBuddy 内置 Skill 创作规范）

## 开发过程实录

### 1. 赛题调研与头脑风暴（22:35）
- 阅读 `M-China/mcd-developer-innovation-challenge` 官方仓库，明确参赛规则（Star 排名、必交文件、Issue 报名格式）
- 与 WorkBuddy 头脑风暴创意方向，否决了同质化严重的"省钱助手"，从真实痛点出发：**不知道吃什么**

### 2. 需求定型（22:37-22:45）
- 创始人原话："就是不知道吃什么其实，去看半天但是我不知道吃什么" + "有套餐尽量是套餐"
- 产品定位从"组餐工具"升级为**点餐决策引擎**，确立拍板模式铁律（最多问 2 个问题、只给 1 个方案、禁止多选项）与 Combo-First 套餐优先算法

### 3. 真实链路验证（22:38-22:55）
在 WorkBuddy 对话中直接调用 mcd-mcp 完成端到端验证：
- `query-nearby-stores`：定位真实门店（含营业时段、24h 门店发现）
- `query-meals`：拉取全菜单，确认 tags 支持新品识别、套餐识别、麦金卡优惠识别
- `calculate-price`：组餐实价试算（蘸酱炸鸡 ¥11.9 + 茉莉奶绿雪冰 ¥9.9 = ¥21.8，促销自动生效）
- `create-order`：真实下单（订单含优惠券自动叠加），验证支付链接形态与 15 分钟订单时效
- 支付二维码化：WorkBuddy 现场编写 Python 脚本，将 payH5Url 生成内联 SVG 二维码直接嵌入对话

### 4. Skill 构建（22:46-23:00）
- 按官方 `skill-creator` 规范构建 `skill/`：YAML frontmatter、渐进式披露（references/ + scripts/）、祈使句风格
- `scripts/pay_qr.py`：支付二维码生成器（确定性代码沉淀为脚本）
- 使用官方 `package_skill.py` 校验通过并打包

### 5. 迭代打磨（23:00-23:12）
- 砍掉"麦麦转盘网页版"方案——产品即 Skill 本身，拒绝为 README 装饰写前端
- 应创始人要求移除全部门店实名信息（隐私脱敏）
- 两轮更名后定稿：**麦上吃 · McNow**，slogan「不想选？麦上吃。」

## WorkBuddy 关键贡献

1. **需求挖掘**：通过追问真实使用场景，把"找不到想吃的"修正为"选择困难"这一核心痛点
2. **实时验证**：直接调用 MCP 工具跑通全链路，所有文档中的价格与流程均为真实数据
3. **工程规范**：按 skill-creator 最佳实践构建，避免手工打包的元数据错误（实测发现 description 多行 YAML 与官方校验器的兼容性问题）
4. **产品纪律**：协助砍掉过度设计（网页转盘），保持 MVP 纯度

## 声明

本项目为参赛者使用 WorkBuddy 独立开发，开发过程不含任何 McDonald's 官方内部信息；本文档不含 Token、密钥等敏感凭证。
