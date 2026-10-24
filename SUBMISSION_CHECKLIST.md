# 参赛提交清单

规则来源：[官方完整活动规则](https://github.com/M-China/mcd-developer-innovation-challenge/blob/main/activityGuidelines.md)。报名截止为北京时间 **2026-10-25 23:59**，最终榜单采集时间为 **2026-10-26 00:00**；按公开 Star 排名，Star > 0 的项目前 100 名及边界并列项目进入获奖范围，仍需通过资格审核。规则变更以官方公告为准。

2026-10-24 公开查询：本仓库为 Public、Star 为 1；[已有报名 Issue #149](https://github.com/M-China/mcd-developer-innovation-challenge/issues/149)，本次尚未核实官方报名成功回执。不要因此直接重复报名；先检查现有 Issue 的官方回复和资格状态。

## 仓库资格

- [ ] GitHub 仓库为 **Public**，项目地址可匿名打开。
- [ ] 仓库创建时间落在官方规则允许区间内。
- [ ] 项目主体确实使用麦当劳官方 MCP；README、MCP_INTEGRATION 和 WorkBuddy 记录相互一致。
- [ ] 没有真实 Token、密码、Cookie、订单支付链接、个人地址或其他凭证。
- [ ] 没有将测试支付链接、真实门店隐私信息写入公开文件。
- [ ] `CONTEST_DECLARATION.md` 保持官方原文，不改名、不改内容。

## 必交文件

- [ ] `README.md`：定位、安装、用法、目标用户、边界和可验证示例。
- [ ] `CONTEST_DECLARATION.md`：官方参赛声明。
- [ ] `MCP_INTEGRATION.md`：服务、工具、调用流程和业务价值。
- [ ] `mcp-config.example.json`：仅使用 `${MCD_MCP_TOKEN}` 占位符。
- [ ] `workbuddy.md`：参加 WorkBuddy 专项奖励时提交，并确认不含 Token。
- [ ] 可运行主体：`skill/` 与本地脚本。

## 本地验收

```bash
python -m pip install -r "skill/requirements.txt"
python -X utf8 "scripts/verify.py"
```

通过后可选打包：

```bash
python -X utf8 "scripts/verify.py" --package
```

不要把含真实配置的备份文件或测试产物加入 Git；提交前运行 `git status --short` 并人工检查 `dist/`、日志和压缩包内容。

## 报名 Issue 文案

Issue 标题建议：

```text
麦上吃 McNow——麦当劳点餐决策引擎 Skill
```

Issue 正文按官方格式保持字段连续，不使用 Markdown 链接：

```text
【参赛申请】
项目名称：麦上吃 McNow
项目地址：https://github.com/Health-525/mcnow
项目简介：基于麦当劳官方 MCP 的点餐决策引擎 Skill。用户一句话表达“不知道吃什么”、预算或口味，Skill 自动确认门店、按套餐优先策略从当前菜单组餐，并用官方价格接口验价；用户明确确认后才创建订单，返回官方支付入口并可在本地生成二维码。支持新品浏览、优惠资格核验、订单状态查询和重复下单保护。仓库含完整 Skill、配置示例、脚本、离线验收用例及 WorkBuddy 开发上下文。
```

## 公开运营建议

- [ ] 在个人可触达的真实社群分享仓库，邀请愿意试用的人自行 Star；不刷 Star、不多账号、不使用自动化刷榜。
- [ ] 报名后检查 Issue 是否收到官方成功回执；若失败按回执修复后重新提交。
- [ ] 记录截止前后仓库地址、报名 Issue 和公开 Star 截图，便于资格核验。
- [ ] 不在 README 承诺“保证得奖”；公开说明 Star 是官方排名依据，作品质量优化用于提升可信度和转化。
