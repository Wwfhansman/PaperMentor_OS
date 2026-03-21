# PaperMentor OS 架构设计文档

![Agent 协作流程图](/Users/goucaicai/Desktop/PaperMentor_OS/docs/assets/agent-collaboration-flow.svg)

## 1. 产品定位

PaperMentor OS 是一个面向大学生的多智能体论文评审与指导系统。

它的目标不是替学生写论文，而是像导师初审一样，诊断论文或研究草稿中的薄弱点，解释这些问题为什么重要，并给出结构化的下一步指导，从而在帮助学生深化思考的同时，减轻导师一部分前期审查工作量。

## 2. 架构目标

本架构刻意选择保守且稳定的设计，除非产品核心假设发生变化，否则不应频繁调整。

稳定目标：

- 以多维评审替代一次性答案生成
- 以指导型输出替代代写型输出
- 以显式 rubric 驱动评估，而不是把规则藏在 prompt 里
- 只在主观性模块上使用选择性多智能体 debate
- 通过 skill 机制扩展能力，而不改动核心编排
- 以 evidence-backed reporting 保证每条结论可追溯

V1 非目标：

- 全流程自动写论文
- 对所有学科进行深层专业正确性核验
- 代替学生进行开放式自主研究
- 全流程启用持续论坛式多 agent 讨论

## 3. 核心设计决策

系统采用以下架构原则：

- 一个顶层 supervisor 负责任务拆解和最终汇总
- 多个专项 review worker 分别负责不同维度
- 只有在主观判断分歧较大时才触发 debate
- skill registry 作为 rubric、policy、schema 和领域规则的维护层
- evidence ledger 作为共享记忆和审计层

它不是 peer-to-peer 的 swarm。
它是一个受控的层级系统，并在局部使用竞争协同。

## 4. 系统分层

### 4.1 输入层

职责：

- 接收论文文本、摘要、目录、元数据和可选学科信息
- 将输入标准化为章节、段落、引用和表格等结构
- 生成供 supervisor 使用的 review task package

输出：

- `PaperPackage`
- `ReviewRequest`

### 4.2 编排层

核心组件：

- `ChiefReviewer`

职责：

- 识别当前评审场景
- 选择适用 workflow
- 选择需要调用的 worker agents
- 从 registry 中选择适用 skills
- 发起并行评审
- 检测结论分歧阈值
- 在需要时触发 debate
- 合并结果并生成最终报告

`ChiefReviewer` 不直接负责深入领域评审，它只负责调度与综合。

### 4.3 专项评审层

V1 固定 worker 集合：

- `TopicScopeAgent`
- `LogicChainAgent`
- `LiteratureSupportAgent`
- `NoveltyDepthAgent`
- `WritingFormatAgent`

各 worker 职责如下：

- `TopicScopeAgent`：评估选题价值、研究问题清晰度、选题范围合理性，以及标题、摘要、正文之间是否一致
- `LogicChainAgent`：评估 claim 与 evidence 的匹配情况、论证断裂点、结构连贯性，以及结论是否得到足够支撑
- `LiteratureSupportAgent`：评估相关工作覆盖度、引用支撑是否充分、是否缺少对比基线和必要文献
- `NoveltyDepthAgent`：评估创新程度、研究深度、工作量是否足够，以及论文是否超出了简单总结层面
- `WritingFormatAgent`：评估结构规范、语言表达、引用格式和表层规范性问题

### 4.4 Debate 层

核心组件：

- `DebateJudgeAgent`

只有在以下情况才触发 debate：

- 同一主观维度上两个或更多 reviewer 的严重度判断明显冲突
- 模块 confidence 低于阈值
- 某个 worker 明确将结果标记为 ambiguous

V1 中 debate 只建议用于：

- 创新性评估
- 研究深度评估
- 少量边界型逻辑充分性问题

Debate 流程：

1. 先比较独立 worker 的输出
2. 只提取真正的分歧点
3. `DebateJudgeAgent` 要求各方给出基于证据的简短重述
4. 输出模块级裁决结论
5. 将裁决与理由写回 ledger

这样做是为了避免无边界讨论，控制成本与时延。

### 4.5 共享证据层

核心组件：

- `EvidenceLedger`

职责：

- 用统一 schema 存储所有 findings
- 为每条 finding 记录文本 anchor
- 记录 confidence、severity 和来源 worker
- 记录 debate 过程和最终裁决
- 为 report composer 提供可追溯数据

最终报告中的每条核心结论都必须可追溯到：

- 论文中的某个位置
- 某条 rubric 标准
- 某个 worker 的判断

### 4.6 输出层

核心组件：

- `GuidanceComposer`

职责：

- 将 findings 转化为结构化导师式评审报告
- 区分高优先级问题和低优先级问题
- 将诊断结果转化为可执行的下一步建议
- 强制执行 no-ghostwriting policy

系统输出内容包括：

- 总体评审总结
- 各维度评分
- 高风险问题
- 基于证据的诊断解释
- 修改优先级列表
- 面向学生的下一步行动建议

默认情况下，系统不输出已经改写好的论文章节。

## 5. 固定评审维度

V1 的评审维度固定为：

1. 选题价值与问题清晰度
2. 逻辑与论证链路
3. 文献支撑
4. 创新性与研究深度
5. 写作与格式规范

这五个维度足以支撑一个稳定 MVP，也足以支撑比赛展示。

## 6. 数据契约

### 6.1 PaperPackage

必需字段：

- `paper_id`
- `title`
- `discipline`
- `stage`
- `abstract`
- `sections`
- `references`

可选字段：

- `advisor_requirements`
- `school_format_rules`
- `language`

### 6.2 ReviewFinding

必需字段：

- `dimension`
- `issue_title`
- `severity`，枚举值为 `high | medium | low`
- `confidence`
- `evidence_anchor`
- `diagnosis`
- `why_it_matters`
- `next_action`
- `source_agent`
- `source_skill_version`

### 6.3 DimensionReport

必需字段：

- `dimension`
- `score`
- `summary`
- `findings`
- `debate_used`

### 6.4 FinalReport

必需字段：

- `overall_summary`
- `dimension_reports`
- `priority_actions`
- `student_guidance`
- `advisor_view`
- `safety_notice`

## 7. 路由逻辑

路由逻辑固定如下：

1. `ChiefReviewer` 读取 `PaperPackage`
2. 系统根据论文阶段和论文类型选择 workflow
3. 系统为五个维度加载核心 skills
4. 客观模块执行单次评审
5. 主观模块可执行多 reviewer 评审
6. 运行 disagreement check
7. 分歧超过阈值时触发 debate
8. `GuidanceComposer` 生成最终报告

V1 中，worker 不允许直接互相调用。
所有跨 agent 协调必须经过 supervisor 或 debate 层。

## 8. Skill 交互模型

Workers 是稳定角色。
Skills 是可替换能力包。

每个 worker 会消费：

- 一份 base role definition
- 一份或多份 rubric skills
- 一份 policy skill
- 一份 output schema skill

这意味着领域适配主要通过 skills 完成，而不是靠重写 agents。

## 9. 教育边界与安全策略

PaperMentor OS 的目标是提升思考质量，而不是绕开思考成本。

硬约束：

- finding 必须指出问题，不能静默替学生改写内容
- next action 可以说明要补什么，但默认不能输出大段代写内容
- 如果用户强行要求直接生成，应切换到受限辅助模式并明确提示，而不能与 review mode 混用

review mode 与 writing-assistance mode 必须是两个清晰区分的产品模式。

## 10. 为什么这套架构应保持稳定

这套架构之所以应尽量稳定，是因为它的核心抽象与真实论文评审过程相匹配：

- 导师本来就是按维度看论文
- 不同评审者本来就会在主观维度上产生分歧
- 评审标准本来就会随时间演化
- 严肃任务里，证据比自由意见更重要

未来可以频繁变化的部分应该是：

- skills
- evaluation datasets
- prompts
- discipline-specific policies

未来不应轻易变化的部分是：

- 顶层 orchestration model
- 固定 worker 职责
- evidence ledger schema
- review report contract

## 11. V1 评估目标

架构应通过以下维度进行验证：

- 问题发现的完整性
- 建议的可操作性
- 多次运行的一致性
- 对高严重度问题与人工评审的一致程度
- 用户是否感知到系统是在“指导”而不是“代写”

## 12. 比赛表达

PaperMentor OS 不是一个泛化的 agent playground。

它是一个论文评审操作系统，核心特征包括：

- 受控的多智能体编排
- 以 rubric 为中心的评估机制
- 选择性竞争协同
- 可维护的 skill 演进能力
- 基于证据的教育型指导输出
