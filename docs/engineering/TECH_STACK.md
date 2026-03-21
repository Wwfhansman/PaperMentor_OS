# PaperMentor OS 技术选型文档

## 1. 文档目的

本文件用于明确 PaperMentor OS 当前阶段的技术路线，避免团队在开发初期反复切换语言、框架和模型接入方案。

## 2. 当前推荐技术路线

当前最推荐的技术方案为：

- 服务端语言：`Python 3.11`
- Web 服务框架：`FastAPI`
- Agent 编排层：`LangGraph`
- 模型调用层：OpenAI 官方 SDK 兼容接口封装
- 数据校验：`Pydantic`
- Skill 存储：文件系统 + `YAML / Markdown / JSON`
- 本地状态存储：`JSON` 或 `SQLite`
- 评测脚本：Python 自定义脚本

## 3. 为什么选择 Python

选择 Python 的原因：

- AI 和 agent 生态最成熟
- 文本处理、数据结构化、接口封装都比较顺手
- 主流大模型供应商优先提供 Python SDK 或兼容接口
- 后续做评测、脚本、服务端整合成本更低

## 4. Python 版本建议

推荐版本：

- `Python 3.11`

不推荐版本：

- macOS 自带 `Python 3.9`

原因：

- 当前主流 agent 框架普遍要求 `Python 3.10+`
- `Python 3.11` 在兼容性、性能、生态支持之间更平衡
- `Python 3.9` 会限制后续框架选择，并增加环境问题

结论：

- 如果准备正式开始开发，应先安装新的 Python 版本
- 不建议直接基于系统自带的 `Python 3.9` 启动项目

## 5. Agent 框架对比

### 5.1 CrewAI

特点：

- 上手快
- 适合快速做多角色协作 demo
- `Agent / Task / Crew` 抽象直观

优点：

- 早期出效果快
- 适合概念验证

缺点：

- 对复杂状态流、证据追踪、局部 debate 的控制不够细
- 后期容易和固定架构打架
- 不适合作为本项目最终主架构

适用判断：

- 适合快速验证概念
- 不建议作为正式版主架构

### 5.2 AutoGen / AG2

特点：

- 强调 agent 间对话与协作
- 比较适合讨论式、多角色式流程

优点：

- 做 debate 类子模块比较自然
- 多角色交互表达强

缺点：

- 容易把系统做成“会聊天的一群 agent”
- 对你们这种固定流程型评审系统不够稳
- 调试和结果约束成本较高

适用判断：

- 可以用于实验 debate 模块
- 不建议作为整套系统的主骨架

### 5.3 LangChain / LangGraph

特点：

- `LangChain` 更偏组件层
- `LangGraph` 更偏有状态工作流和 agent 编排

优点：

- 适合固定流程 + 条件分支 + 状态传递
- 非常适合多 worker 并行、局部 debate、最终汇总这种结构
- 比较符合 PaperMentor OS 的架构形态

缺点：

- 比 CrewAI 更底层
- 需要自己想清楚状态流和节点职责

适用判断：

- 最适合做本项目主架构

## 6. 是否从零开始写

建议：

- 不要一开始完全从零写
- 也不要完全依赖高层封装框架

推荐方式：

- 用 `LangGraph` 处理主流程编排
- 核心业务能力自己实现

自己实现的部分包括：

- `Skill Registry`
- `EvidenceLedger`
- `ReviewFinding / Report Schema`
- debate 触发逻辑
- 报告生成逻辑

原因：

- 项目真正的差异化不在“自己造 agent runtime”
- 项目真正的差异化在评审流程、技能体系和证据逻辑

## 7. 大模型使用策略

### 7.1 是否必须给每个 agent 配不同模型

不必须。

项目初期完全可以让所有 agents 共用同一个大模型。

多 agent 的核心不在于“模型不同”，而在于：

- 角色不同
- rubric 不同
- skill 不同
- 输出 schema 不同
- 汇总和裁决逻辑不同

### 7.2 当前推荐模型策略

最推荐的起步方案：

- 所有 agents 共用同一个模型

这样做的好处：

- 成本最低
- 调试最简单
- 结果更容易对齐

后续增强方案：

- 普通 workers 用便宜模型
- `ChiefReviewer` 和 `DebateJudgeAgent` 用更强模型

## 8. 模型供应商切换策略

系统应设计为支持可配置模型接入。

建议统一抽象：

- `provider`
- `base_url`
- `api_key`
- `model_name`
- `temperature`
- `max_tokens`

这样只要供应商兼容 OpenAI 风格接口，系统就能快速切换。

## 9. 推荐的模型接入抽象

建议定义两个核心抽象：

### 9.1 ProviderConfig

建议字段：

- `provider_id`
- `base_url`
- `api_key`
- `model_name`
- `temperature`
- `max_tokens`
- `timeout`

### 9.2 LLMClient

建议能力：

- `generate(messages, config)`
- `generate_structured(messages, schema, config)`
- `supports_json_schema()`
- `supports_tool_calling()`

这样 agent 层不需要感知底层具体是哪家模型。

## 10. BYOK 与平台托管模式

### 10.1 BYOK

BYOK 即 `Bring Your Own Key`，也就是让用户自己填：

- provider
- base_url
- model_name
- api_key

适合：

- 开发者用户
- 自部署用户
- 高级用户

### 10.2 平台托管模式

平台托管模式即：

- 由系统提供默认 API
- 用户按次数、额度或订阅使用

适合：

- 普通学生用户
- 比赛演示版
- 低门槛产品体验

### 10.3 最终建议

正式方案建议采用双模式：

- 默认托管模式
- 高级用户支持 BYOK

不建议把“用户自己填 API Key”作为唯一正式方案。

## 11. 成本策略建议

如果由平台统一提供 API，则必须有成本控制机制。

原因：

- 多 agent 任务 token 消耗高
- 论文输入长度本身就大
- debate 和汇总会增加额外调用

建议方式：

- 免费额度限制
- 次数限制
- 订阅制
- 高级功能单独计费

## 12. 当前阶段推荐落地方案

结合单人开发、预算有限的现实，当前阶段建议如下：

### 比赛版

- 固定一个主模型
- 由你自己提供 API
- 不开放复杂的 provider 配置界面
- 重点保证演示稳定
- 输入优先支持 `docx`
- 主演示样例固定为“计算机专业本科毕业论文草稿”

### 内测版

- 支持 `model_name + base_url + api_key` 切换
- 支持 BYOK
- 支持少量 OpenAI 兼容供应商

### 正式版

- 默认托管模式
- 高级用户支持 BYOK
- 根据套餐控制调用额度和高级评审能力

## 13. 当前结论

当前阶段最稳的技术方向是：

- `Python 3.11`
- `FastAPI`
- `LangGraph`
- 单模型跑全 agent
- 架构上预留 provider 抽象
- 中长期采用“托管 + BYOK”双模式
- V1 输入优先支持 `docx`
- V1 聚焦“计算机专业本科毕业论文”
