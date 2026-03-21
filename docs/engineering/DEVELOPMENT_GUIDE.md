# PaperMentor OS 开发文档

## 1. 文档目的

本文件用于把产品设计和架构设计转化为可以执行的开发路径。

它刻意写得更细，是为了让团队按顺序落地，而不是边做边发散。

## 2. 开发原则

先做一条窄而完整的纵向链路。

不要一开始就做：

- 过多 agent
- 过多学科
- 过多 UI 功能
- 过多动态路由逻辑

应该先打通这样一条完整路径：

- 一种稳定输入格式
- 一个明确领域
- 一个固定报告契约
- 一条稳定编排流程

当前 V1 冻结建议：

- 输入优先只做 `docx`
- 目标场景固定为“计算机专业本科毕业论文草稿”
- 输出固定为“按维度展示的 10 分制 PDF 报告”

## 3. 建议的工程结构

建议后续采用如下目录结构：

```text
PaperMentor OS/
  README.md
  docs/
  references/
  src/
    agents/
    orchestrator/
    skills/
    schemas/
    parsers/
    ledger/
    reporting/
    policies/
    evals/
    shared/
  tests/
    unit/
    integration/
    fixtures/
  scripts/
```

在正式进入大规模编码前，应先按这个结构建立工程骨架。

补充约束：

- 建议开发环境使用 `Python 3.11`
- 不建议使用 macOS 自带的 `Python 3.9` 作为项目运行时
- agent 编排层优先采用 `LangGraph` 或轻量自写编排，不建议直接重度依赖 `CrewAI`

## 4. 开发阶段划分

整个项目建议分为八个阶段推进。

### 阶段 1：冻结核心契约

目标：

- 在编码前先阻止架构漂移

任务：

1. 冻结固定 worker 列表
2. 冻结 report schema
3. 冻结 `ReviewFinding` schema
4. 冻结 `PaperPackage` schema
5. 冻结 debate 触发规则

产出：

- schema 定义
- 架构确认版本

退出条件：

- 团队对核心数据契约达成一致
- 不再随意改动角色边界

### 阶段 2：实现输入解析

目标：

- 将论文原始文本转成可被系统消费的结构化对象

任务：

1. 定义 V1 接受的输入格式
2. 解析标题、摘要、章节和参考文献
3. 标准化标题层级与段落
4. 生成 section ID 和 paragraph anchor
5. 输出 `PaperPackage`

实现说明：

- V1 输入优先支持 `docx`
- 不要在第一阶段就被 `pdf` 解析拖住
- evidence anchor 必须稳定、可复现

产出：

- parser 模块
- 解析样例

退出条件：

- 至少 3 篇样本文档可以被稳定解析成统一结构

### 阶段 3：实现核心 Schemas

目标：

- 让所有 agent 遵循同一套输入输出契约

任务：

1. 定义 `PaperPackage`
2. 定义 `ReviewFinding`
3. 定义 `DimensionReport`
4. 定义 `FinalReport`
5. 定义 `DebateCase`

实现说明：

- schema 字段要明确，尽量少而精
- 不要过早引入大量可选字段
- 每条 finding 至少要包含 severity、confidence、evidence、diagnosis 和 next action

产出：

- schema 文件
- 校验层

退出条件：

- 非法 agent 输出可以被自动拦截

### 阶段 4：实现 Evidence Ledger

目标：

- 在最终报告生成前，统一沉淀所有中间 findings

任务：

1. 创建 ledger 存储接口
2. 按维度存储 review findings
3. 存储 worker metadata
4. 存储 skill version metadata
5. 存储 debate 记录
6. 提供给 composer 的查询接口

实现说明：

- V1 可以先用内存存储或简单 JSON 持久化
- 不要过早引入复杂数据库设计

产出：

- ledger 模块
- ledger 测试样例

退出条件：

- 所有 worker 的 findings 都能被统一读取

### 阶段 5：实现 Worker Agents

目标：

- 让每个评审维度都可以独立运行

推荐实现顺序：

1. `WritingFormatAgent`
2. `TopicScopeAgent`
3. `LogicChainAgent`
4. `LiteratureSupportAgent`
5. `NoveltyDepthAgent`

为什么这样排：

- 先做主观性最低的模块
- 再逐步进入更难判断的模块

每个 worker 的任务：

1. 定义角色 prompt
2. 定义所需 skills
3. 绑定输出 schema
4. 定义 confidence 规则
5. 输出 `DimensionReport`

实现说明：

- 每个 worker 都应可以单独测试
- worker 不应知道最终报告长什么样
- worker 只负责输出结构化 findings

退出条件：

- 每个 worker 都能在样本文本上输出 schema 合法的结果

### 阶段 6：实现 Orchestrator

目标：

- 用稳定顺序调度全部 worker

任务：

1. 实现 `ChiefReviewer`
2. 按学科与阶段加载必需 skills
3. 并行或伪并行分发 workers
4. 汇总 dimension reports
5. 检测分歧
6. 在需要时触发 debate
7. 将汇总结果传给 composer

实现说明：

- V1 应优先采用确定性编排，而不是复杂自主规划
- 编排日志应可追溯，便于调试和演示

退出条件：

- 一个请求可以从输入一路走到最终报告

### 阶段 7：实现 Debate 与最终报告组装

目标：

- 在不把系统做成论坛模拟器的前提下提升主观评审质量

任务：

1. 实现分歧阈值检测
2. 定义 `DebateCase`
3. 实现 `DebateJudgeAgent`
4. 将裁决结果写回 ledger
5. 实现 `GuidanceComposer`
6. 生成学生视图和导师视图
7. 支持 PDF 报告导出

实现说明：

- 只有主观维度应该启用 debate
- debate prompt 必须强制引用证据
- composer 应按优先级组织问题，而不是按 worker 原始顺序堆叠

退出条件：

- 最终报告结构清晰、内容不重复、可直接展示

### 阶段 8：实现评测与演示资产

目标：

- 证明系统有用，并且具备比赛展示能力

任务：

1. 设计单模型 baseline prompt
2. 构建论文样本 fixtures
3. 定义人工评测表
4. 对比主要问题发现质量
5. 对比建议可操作性
6. 准备一组强展示效果的 before/after 样例

退出条件：

- 团队能够解释为什么 PaperMentor OS 明显优于单一通用 prompt

## 5. 推荐的模块开发顺序

如果多人并行开发，建议按以下顺序推进：

1. schema 和 parser
2. ledger
3. writing/format worker
4. topic 和 logic workers
5. literature 和 novelty workers
6. orchestrator
7. debate
8. report composer
9. evaluation
10. UI 层

这样可以最大程度减少集成混乱。

## 6. 模块详细设计

### 6.1 Parser 模块

职责：

- 切分论文内容
- 识别标题、摘要、章节、参考文献
- 分配稳定 anchor

最小接口：

- `parse_raw_input() -> PaperPackage`
- `extract_sections()`
- `extract_references()`
- `build_anchor_map()`

关键实现点：

- anchor ID 应尽量具备可读性，方便报告和界面反向定位

### 6.2 Schema 模块

职责：

- 定义所有核心数据契约
- 校验 worker 输出

最小接口：

- `validate_paper_package()`
- `validate_review_finding()`
- `validate_dimension_report()`
- `validate_final_report()`

关键实现点：

- schema 校验错误必须尽早暴露，不能拖到集成后期才发现

### 6.3 Skills 模块

职责：

- 从文件系统加载 skills
- 校验 skill metadata
- 为 worker 解析出可执行的 skill bundle

最小接口：

- `load_skill(skill_id, version=None)`
- `resolve_worker_skills(worker_id, context)`
- `validate_skill_metadata()`

关键实现点：

- 缺失必需 skill 时应明确报错，不能静默降级

### 6.4 Worker 模块

职责：

- 运行单个维度的专项评审
- 绑定 rubric 与 policy skills
- 输出结构化 findings

最小接口：

- `run_worker(paper_package, skill_bundle) -> DimensionReport`

关键实现点：

- worker 必须显式引用 evidence anchors，而不是只给抽象判断

### 6.5 Ledger 模块

职责：

- 存储 findings 与 debate 裁决
- 保证最终组装结果具备确定性

最小接口：

- `record_dimension_report()`
- `record_debate_result()`
- `get_findings_by_priority()`
- `get_dimension_summary()`

### 6.6 Orchestrator 模块

职责：

- 路由任务
- 调度 workers
- 执行决策逻辑

最小接口：

- `create_review_plan()`
- `run_review()`
- `detect_disagreement()`
- `trigger_debate_if_needed()`

关键实现点：

- 编排日志应被保留，便于调试和比赛说明

### 6.7 Reporting 模块

职责：

- 组装最终的导师式报告

最小接口：

- `compose_final_report()`
- `build_priority_actions()`
- `build_student_guidance()`
- `build_advisor_view()`

关键实现点：

- 报告层应主动合并重复 findings，而不是原样堆叠多 worker 输出

## 7. Skill 开发流程

每个 skill 建议按以下顺序开发：

1. 定义用途
2. 编写 metadata
3. 编写 rubric 或 policy 正文
4. 定义预期输出契约
5. 编写正反样例
6. 编写评测用例
7. 跑 benchmark
8. 发布版本

不要跳过评测环节。

## 8. 测试策略

测试建议分四层推进。

### 8.1 单元测试

测试内容：

- parsers
- schemas
- skill loading
- ledger operations
- disagreement detection

### 8.2 Worker 测试

测试内容：

- 输出 schema 是否合法
- evidence anchor 是否存在
- policy 是否被遵守

### 8.3 集成测试

测试内容：

- 端到端评审流程
- debate 触发
- 最终报告生成

### 8.4 人工评测

测试内容：

- 问题发现完整性
- 建议可操作性
- 评审维度覆盖度
- 专业合理性

## 9. 评测数据集策略

应尽早建立一个小规模内部数据集。

数据集建议包括：

- 计算机专业本科毕业论文较强样本片段
- 计算机专业本科毕业论文较弱样本片段
- 结构明显有问题的论文
- 文献支撑明显不足的论文
- 创新点论证薄弱的论文

每个样本应附带：

- 预期主要问题
- 预期严重等级
- 预期所属维度

这是后续规范调 prompt 和 skill 的必要基础。

## 10. 团队分工建议

如果团队人数不少于 4 人，可按以下方向分工：

1. parser 和 schemas
2. skills 与 worker prompts
3. orchestrator 与 ledger
4. report 层与 demo UI

如果团队规模更小：

- 必须有 1 个人专门负责架构一致性
- 不要让多人同时改同一组核心契约

## 11. 实现风险与控制方式

### 风险：架构写得很多，但始终跑不出结果

控制方式：

- 先做一条纵向可运行链路

### 风险：Debate 逻辑太重，导致成本高、速度慢

控制方式：

- V1 只在 1 到 2 个维度上启用 debate

### 风险：报告很长，但不真正有帮助

控制方式：

- 强制问题优先级排序
- 强制输出动作化建议

### 风险：团队持续变更范围

控制方式：

- 把 PRD 和架构文档视为冻结基线

## 12. 第一轮 Sprint 建议

Sprint 1 只需要做出下面这些：

1. 一个能解析 `docx` 并输出 `PaperPackage` 的 parser
2. 一个可运行的 `WritingFormatAgent`
3. 一个可运行的 `TopicScopeAgent`
4. 一个简单 ledger
5. 一版基础最终报告

这些已经足以证明方向是通的。

Sprint 1 不要开始做 debate、完整 skill versioning，也不要先卷 UI。

## 13. 第二轮 Sprint 建议

Sprint 2 建议新增：

1. `LogicChainAgent`
2. `LiteratureSupportAgent`
3. 第一版 skill loader
4. 更好的报告优先级整理逻辑
5. 初始评测样本

## 14. 第三轮 Sprint 建议

Sprint 3 建议新增：

1. `NoveltyDepthAgent`
2. disagreement detection
3. `DebateJudgeAgent`
4. 单模型 baseline 对比

## 15. 比赛前检查清单

在正式演示前，团队至少应具备：

1. 一组可靠的计算机专业本科毕业论文草稿样例
2. 一组 baseline 对比样例
3. 一张清晰的架构图
4. 一套清楚的“为什么需要 multi-agent”表达
5. 一套清楚的“为什么这是指导系统而不是代写系统”表达

## 16. 最终工程规则

如果一个新想法需要改动以下任一项：

- 固定 worker 集合
- 评审维度
- 报告契约
- evidence ledger 的角色定义

那它就不是小优化，而是架构改动。
应按架构决策处理，而不是随手修改。
