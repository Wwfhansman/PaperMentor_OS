# PaperMentor OS Skill Registry 设计文档

![Skill 演进流程图](/Users/goucaicai/Desktop/PaperMentor_OS/docs/assets/skill-evolution-flow.svg)

## 1. 为什么需要 Skills

系统不应该把评审标准直接写死在 agent 代码里，也不应该全部堆在一个超长 system prompt 中。

Skills 的作用是让评审能力变得：

- 可维护
- 可版本化
- 可测试
- 可复用
- 可替换，而不需要重写整体架构

Agents 定义角色。
Skills 定义评审能力。

## 2. 稳定 Skill 模型

每个 skill 都应是一个独立能力包，可被一个或多个 agents 复用。

每个 skill 必须声明：

- 它是做什么的
- 在什么情况下应该启用
- 依赖哪些输入
- 必须遵守什么输出契约
- 必须遵守哪些 policy 边界
- 如何评估这个 skill 的质量

V1 原则：

- agents 尽量稳定
- skills 持续演进

## 3. Skill 分类

PaperMentor OS V1 建议使用五类 skills。

### 3.1 Rubric Skills

用途：

- 定义某个评审维度下“什么算好”

示例：

- `topic-clarity-rubric`
- `logic-chain-rubric`
- `literature-support-rubric`
- `novelty-depth-rubric`
- `writing-format-rubric`

### 3.2 Policy Skills

用途：

- 约束产品边界和安全策略

示例：

- `no-ghostwriting-policy`
- `education-guidance-policy`
- `evidence-required-policy`

### 3.3 Output Schema Skills

用途：

- 强制所有 workers 以统一结构输出

示例：

- `review-finding-schema`
- `dimension-report-schema`
- `final-report-schema`

### 3.4 Domain Adaptation Skills

用途：

- 将通用评审逻辑适配到学科、阶段或院校要求

示例：

- `computer-science-thesis-rules`
- `proposal-stage-review-rules`
- `graduation-thesis-format-rules`

### 3.5 Evaluation Skills

用途：

- 定义某个 skill 本身该如何被测试和验收

示例：

- `high-severity-issue-benchmark`
- `report-actionability-benchmark`
- `consistency-check-benchmark`

## 4. 推荐的 Skill 目录结构

```text
skills/
  topic-clarity-rubric/
    skill.yaml
    prompt.md
    rubric.md
    output_schema.json
    examples.json
    eval_cases.json
  logic-chain-rubric/
  novelty-depth-rubric/
  no-ghostwriting-policy/
  review-finding-schema/
```

这套目录结构建议尽量保持稳定。

## 5. 强制 Skill Metadata

每个 `skill.yaml` 建议至少包含：

```yaml
id: novelty-depth-rubric
name: Novelty And Research Depth Rubric
version: 1.0.0
category: rubric
owner_agent:
  - NoveltyDepthAgent
applicable_disciplines:
  - computer_science
applicable_stages:
  - proposal
  - draft
  - final_draft
required_inputs:
  - title
  - abstract
  - sections
optional_inputs:
  - references
  - advisor_requirements
output_schema: review_finding_schema_v1
policies:
  - no-ghostwriting-policy
  - evidence-required-policy
quality_gates:
  - high_severity_recall
  - report_actionability
status: active
```

## 6. Skill 加载规则

Skill 加载建议遵循固定规则：

1. 先加载 worker 的 base role definition
2. 再加载必需 rubric skill
3. 再加载必需 policy skills
4. 再加载 output schema skill
5. 最后根据论文类型和学科加载可选 domain adaptation skill
6. 如果缺失必需 skill 或版本不兼容，则直接拒绝执行

这样能提高执行确定性，也便于调试。

## 7. Skill 选择策略

Skill 选择不应依赖 agent 的自由发挥。
应依赖显式路由条件。

选择输入包括：

- 论文阶段
- 学科
- 作业类型
- 学校规范
- 请求的评审模式

选择优先级建议为：

1. 全局 policy skills
2. 维度必需 rubric
3. domain adaptation skill
4. 格式/风格规则 skill
5. evaluation skill，注意它主要用于离线 QA，不用于在线推理

## 8. 版本策略

所有 skills 建议采用语义化版本控制。

版本规则：

- major：输出契约或 rubric 含义发生变化
- minor：rubric 扩展或指导增强，但契约不变
- patch：措辞、例子、prompt 微调，但行为目标不变

默认情况下，每个 skill 只保留一个 production active version。
旧版本应保留用于评测与回滚。

## 9. Skill 治理流程

每次 skill 变更建议遵循以下路径：

1. draft
2. local evaluation
3. benchmark comparison
4. reviewer approval
5. production release

一个 skill 不能只因为“prompt 看起来更好”就直接上线。
它必须经过评测门槛。

## 10. Skill 评测框架

每个 skill 至少应在四个维度上被评估：

- 问题发现质量
- 证据锚定质量
- 指导建议可操作性
- policy 合规性

推荐的离线指标：

- high-severity issue recall
- false positive rate
- evidence-anchor validity
- human-rated actionability
- policy violation rate
- run-to-run stability

## 11. Skills 与 Multi-Agent Debate 的关系

Debate 本身也不应依赖临时 prompt。
应尽量通过专门的 comparison skills 来规范。

推荐的 debate 相关 skills：

- `disagreement-detection-rules`
- `debate-judging-schema`
- `severity-resolution-rubric`

这样 debate 也具备标准化和可维护性。

## 12. V1 最小 Skill 集合

PaperMentor OS V1 至少建议具备以下 skills：

- `topic-clarity-rubric`
- `logic-chain-rubric`
- `literature-support-rubric`
- `novelty-depth-rubric`
- `writing-format-rubric`
- `no-ghostwriting-policy`
- `education-guidance-policy`
- `evidence-required-policy`
- `review-finding-schema`
- `dimension-report-schema`
- `final-report-schema`
- `proposal-stage-review-rules`
- `computer-science-thesis-rules`

这一套已经足以支撑比赛级 MVP。

## 13. 哪些内容不应过早做成 Skill

不要把所有东西都 skill 化。

以下内容应保留在稳定架构中：

- `ChiefReviewer`
- `EvidenceLedger`
- debate trigger thresholds
- final report assembly pipeline
- worker responsibility boundaries

如果这些核心部件也过早做成 skills，系统会变得难以推理且不稳定。

## 14. 为什么这套设计应尽量稳定

这套 skill 设计之所以应保持稳定，是因为它清晰区分了：

- 架构问题
- 评审标准
- policy 约束
- 领域适配
- 评测资产

正是这种拆分，才能让系统在不推翻整体架构的前提下持续演进。

## 15. V1 实现建议

如果时间紧，建议按以下顺序落 skill 系统：

1. rubric skills
2. policy skills
3. output schema skills
4. 一个计算机领域的 domain adaptation skill
5. evaluation assets

这个顺序能在控制复杂度的前提下，最大化比赛演示价值。
