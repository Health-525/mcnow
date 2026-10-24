<div align="center">

<img src="assets/logo.jpg" alt="麦上吃 McNow" width="180"/>

# 麦上吃 · McNow

> **一句话点餐决策引擎：把“我不知道吃什么”变成一个实时验价、确认后可下单的麦当劳方案。**

[![参赛作品](https://img.shields.io/badge/麦当劳%20MCP%20创意开发大赛-参赛作品-red)](https://github.com/M-China/mcd-developer-innovation-challenge)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

## 先看它怎么工作

```text
人：不知道吃什么，25 块以内，想吃炸鸡和喝的

麦上吃：（确认门店并读取菜单后）
        就这套：蘸酱炸鸡 + 茉莉奶绿雪冰
        实付：¥21.8（以当前门店 calculate-price 为准）
        理由：满足炸鸡和饮料，历史试算优惠 ¥13.1。

        确认下单吗？
```

这段是交互示意；仓库中的价格样例来自 2026-10-09 的一次真实链路记录，不能代表今天的库存或价格。Skill 不在用户确认前创建订单，也不接触支付凭证。

## 为什么做它

点餐困难常常不是找不到商品，而是面对门店差异、套餐组合、优惠资格和实时价格时不想做选择。McNow 把这些判断收进一次短对话：先锁定可履约门店，再从当前菜单组餐，用官方价格接口验算，最后把决定权留给用户。

核心产品纪律是“默认替你拍板，但不替你付款”：默认输出一个方案；用户想浏览新品或比较方案时再展开；任何价格、库存、会员或学生资格都以当前工具返回为准。

## 能力

- **拍板模式**：理解“随便、你定、不知道吃什么”，最多问必要问题，默认只给一个方案。
- **套餐优先 + 同需求比价**：读取套餐详情，和覆盖相同需求的单品候选进行实时试算。
- **门店与时段感知**：按门店编码和当前可售菜单工作；临近打烊时提示风险并可切换门店重新核价。
- **新品与优惠**：读取当前菜单标签；优惠券、麦金卡、学生资格均需工具或用户信息证实。
- **安全订单生命周期**：报价、二次确认、同配置复验、创建一次、查询支付状态，避免重复订单。
- **支付二维码**：从当前订单的官方 `payH5Url` 本地生成内联 SVG，不上传第三方。

## 快速开始

目标用户：想快速决定麦当劳吃什么、需要按预算和口味组餐的 WorkBuddy 用户。

前置要求：Python 3.9+、WorkBuddy，以及[麦当劳中国 MCP Token](https://github.com/M-China/mcd-mcp-server)。Token 只在本地配置中使用，不要粘贴到聊天、Issue 或日志。

### 0. 导入 Skill

下载或克隆本仓库，在 WorkBuddy 的技能管理入口导入 `skill/`，或导入离线验收生成的 `dist/mcnow-skill.zip`（压缩包内根目录为 `mcnow/`）。不同版本的导入入口以 WorkBuddy 当前界面为准。启用后再配置连接器；仅添加连接器不会自动安装本 Skill。

### 1. 配置 mcd-mcp

连接器配置格式见 [mcp-config.example.json](mcp-config.example.json)。`${MCD_MCP_TOKEN}` 是脱敏占位符，不能假定宿主会自动展开。推荐运行脚本，在本地隐藏输入 Token：

```bash
python "skill/scripts/setup_mcp.py" --dry-run
python "skill/scripts/setup_mcp.py"
```

脚本默认目标为 `~/.workbuddy/mcp.json`。先从 WorkBuddy 配置入口核实实际路径；路径不同时使用：

```bash
python "skill/scripts/setup_mcp.py" --config "实际配置路径/mcp.json" --dry-run
python "skill/scripts/setup_mcp.py" --config "实际配置路径/mcp.json"
```

脚本保留其他连接器和额外设置，写入前备份；备份也含凭证，请仅在本地保存。也支持读取进程已有的 `MCD_MCP_TOKEN` 环境变量。然后打开 WorkBuddy → 连接器 → 自定义连接器，启用 `mcd-mcp`。若工具已可用，跳过配置。

### 2. 开始对话

```text
不知道吃什么，25 块以内，你定
想吃炸鸡，配饮料，帮我算当前门店实价
最近这家店有什么新品？先别下单
就上一条方案，下单
```

只有完整报价卡被明确确认后才会创建订单。二维码脚本依赖见 [skill/requirements.txt](skill/requirements.txt)：

```bash
python -m pip install -r "skill/requirements.txt"
python "skill/scripts/pay_qr.py" --help
```

真实链接由宿主通过进程 stdin 传给 `--url-stdin`，不在命令行中内嵌；支付截止时间取当前订单返回值。宿主不支持 SVG 时仍可打开同一官方支付链接。

## MCP 链路

```text
query-nearby-stores
       ↓
query-meals → query-meal-detail（套餐需要时）→ query-store-coupons（用户有券时）
       ↓
calculate-price（候选验价）
       ↓
用户确认 → 同配置复验 → create-order
       ↓
payH5Url → 本地 SVG / 官方支付页 → query-order
```

完整工具说明见 [MCP_INTEGRATION.md](MCP_INTEGRATION.md)；订单异常、限流与重复下单处理见 [skill/references/order-lifecycle.md](skill/references/order-lifecycle.md)。

## 离线验收

不需要 Token、不会调用真实订单接口：

```bash
python -m pip install -r "skill/requirements.txt"
python -X utf8 "scripts/verify.py"
```

行为回放案例见 [skill/references/acceptance-cases.md](skill/references/acceptance-cases.md)。本次未连接真实 MCP 重跑，自动检查不能证明模型会遵循指令，也不能替代真实门店链路验证。缺 `qrcode` 时基础检查仍可运行，二维码测试显示跳过；打包要求全部测试通过。

## 项目文件

| 路径 | 用途 |
|---|---|
| `skill/SKILL.md` | Skill 入口、路由、确认边界和输出格式 |
| `skill/references/engine-design.md` | 组餐搜索、预算、优惠资格和理由规则 |
| `skill/references/order-lifecycle.md` | 订单状态机、异常和支付展示规则 |
| `skill/scripts/setup_mcp.py` | 本地安全配置 mcd-mcp |
| `skill/scripts/pay_qr.py` | 本地生成支付二维码 SVG |
| `scripts/verify.py` | 不联网的结构、凭证、配置和二维码验收 |
| `mcp-config.example.json` | 脱敏 MCP 配置示例，只有环境变量占位符 |
| `SUBMISSION_CHECKLIST.md` | 参赛资格、公开仓库和报名 Issue 检查清单 |

## 已验证与边界

- 2026-10-09 曾在真实门店完成“门店查询 → 菜单 → 实价试算 → 下单返回支付链接”的链路验证，样例记录见 [MCP_INTEGRATION.md](MCP_INTEGRATION.md)。
- 当前仓库提供的是 WorkBuddy Skill 和本地脚本，不承诺外送、营养目标、活动预约等未完成实测的能力；相关请求会按工具可用性和用户确认继续。
- 餐品、价格、库存、优惠和订单状态以麦当劳官方实时结果为准；本项目不是麦当劳官方产品。

## 参赛

本项目按官方要求保留 `CONTEST_DECLARATION.md`、`MCP_INTEGRATION.md`、`mcp-config.example.json` 和 WorkBuddy 开发上下文。报名文案和提交前检查见 [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md)。

## 贡献

欢迎通过 Issue 提交脱敏复现步骤：宿主版本、输入、预期行为、实际行为。请移除 Token、个人地址、订单号和支付链接；行为改动请补充对应回放案例并运行离线验收。

## 许可证

[MIT](LICENSE)
