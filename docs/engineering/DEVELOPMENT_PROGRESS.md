# PaperMentor OS 开发进度

## 1. 文档目的

本文件用于持续记录 PaperMentor OS 的实际开发进展，避免项目状态只存在于对话、终端输出或个人记忆中。

使用原则：

- 只记录已经完成、正在推进或明确排定的开发事项
- 不重定义 PRD 和架构边界
- 如果实现过程中发现与 `PRD.md` 或 `ARCHITECTURE.md` 冲突，先单独标记，不在此文档里直接改边界

## 2. 当前状态

更新时间：`2026-03-21`

当前已进入：

- Sprint 2 后半段

当前系统已经具备：

- Python 项目骨架
- 核心 schema 校验层
- `docx` 解析
- 内存版 `EvidenceLedger`
- 基础 `GuidanceComposer`
- 可运行的 `ChiefReviewer`
- 五个已接入主链路的 workers：
  - `TopicScopeAgent`
  - `LogicChainAgent`
  - `LiteratureSupportAgent`
  - `NoveltyDepthAgent`
  - `WritingFormatAgent`
- 文件系统版最小 `SkillLoader`
- FastAPI 最小接口入口
- 非破坏式 debug review API，可返回 review trace
- 显式按“研究内容优先于文本表达”整理的基础报告优先级逻辑
- 最小 `disagreement detection`，可为未来 selective debate 提供候选 case
- 最小 selective debate 闭环：`DebateJudgeAgent` 可对候选维度做受控裁决

当前系统尚未具备：

- PDF 报告导出
- 完整评测样本集
- UI 层

## 3. 已完成事项

### 3.1 工程初始化

已完成：

- 建立 `src/`、`tests/`、`scripts/` 目录骨架
- 新增 `pyproject.toml`
- 新增 `.gitignore`
- 安装基础依赖并完成本地可运行环境

### 3.2 核心契约

已完成：

- `PaperPackage`
- `ReviewFinding`
- `DimensionReport`
- `FinalReport`
- `Dimension / Severity / Stage / Discipline` 等基础枚举

当前约束：

- 没有修改冻结的 V1 报告契约
- 没有扩大输入范围，仍只支持 `docx`

### 3.3 Parser

已完成：

- 第一版 `DocxPaperParser`
- 标题、摘要、章节、参考文献提取
- 稳定 anchor 生成

当前限制：

- 还没有处理复杂表格、图片、脚注和 `pdf`
- 对格式混乱的 `docx` 容错仍有限

### 3.4 Worker 与编排

已完成：

- `TopicScopeAgent`
- `LogicChainAgent`
- `LiteratureSupportAgent`
- `NoveltyDepthAgent`
- `WritingFormatAgent`
- `ChiefReviewer` 串联解析、skill 解析、worker 执行、ledger 记录和最终报告生成

当前特点：

- 仍是确定性编排
- 已引入最小 selective debate，但还不是完整多 reviewer 裁决
- 研究内容类问题在 ledger 优先级中高于写作格式类问题
- 最终报告层也显式保证研究内容类问题优先于写作规范类问题

### 3.5 Skill 系统

已完成：

- 最小 `SkillLoader`
- `skill.yaml` metadata 解析
- rubric / policy / output schema / domain skill bundle 解析
- 第一批 skill 资产：
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
  - `computer-science-thesis-rules`

当前限制：

- 仍使用静态 worker-to-skill 映射
- 还没有做版本回滚、production active version 管理和 evaluation skill

### 3.6 Reporting 与测试资产

已完成：

- `GuidanceComposer` 增加报告层显式优先级整理逻辑
- priority actions 去重
- student guidance 去重
- advisor view 区分研究内容类与写作规范类问题
- 新增测试辅助 fixture，用于生成最小 `docx` 样本
- 新增可枚举的 `review case` fixtures
- 新增 `review case catalog`，用于组织 baseline / debate candidate 等样本

当前限制：

- 仍未引入更丰富的报告去重与合并策略
- 还没有正式的离线评测样本集，只是测试级 fixtures

### 3.7 Disagreement Detection

已完成：

- 新增 `DebateCase` schema
- 新增最小 `DisagreementDetector`
- `ChiefReviewer` 运行后会记录 `last_debate_candidates`
- 当前只对主观维度候选进行检测，并交由最小 selective debate 复核

当前限制：

- 仍是单评审输出上的“歧义/边界情况”检测，不是真正多 reviewer 分歧检测
- 候选结果尚未写入最终报告

### 3.8 Selective Debate

已完成：

- 新增 `DebateResolution` schema
- 新增 `DebateJudgeAgent`
- `ChiefReviewer` 会对 `last_debate_candidates` 命中的主观维度执行最小裁决
- `EvidenceLedger` 可记录 debate result
- 被复核的维度会将 `debate_used` 标记为 `true`

当前限制：

- 仍不是多 reviewer 对比后的正式 debate，只是单次受控复核
- debate 结果目前主要体现在维度 summary、findings 过滤和内部 trace 中
- 最终报告没有单独展开 debate 过程明细

### 3.9 API 与 Debug Trace

已完成：

- 保留正式 `/review/docx` 报告接口不变
- 新增 `/review/docx/debug` 调试接口
- debug 接口可返回 `debate_candidates` 和 `debate_resolutions`

当前限制：

- debug trace 只暴露 debate 相关内部状态，还没有暴露完整 skill/load/orchestration trace
- 仍未做鉴权、访问控制或调试信息分级

## 4. 测试与验证

截至 `2026-03-21`，当前已通过：

- debug API 集成测试
- selective debate 单元测试
- schema 单元测试
- disagreement detection 单元测试
- `docx parser` 单元测试
- `SkillLoader` 单元测试
- reporting 单元测试
- 五维端到端集成测试

当前基线结果：

- `pytest` 通过，当前为 `16 passed`

## 5. 下一步计划

按当前顺序继续推进：

1. 继续扩展 fixtures 和评测样本，覆盖强样本/弱样本/边界样本
2. 评估 PDF 导出落点
3. 逐步替换启发式规则为更强的 skill 驱动实现
4. 继续补真实论文模板与样本覆盖
5. 评估是否需要更多调试 trace（如 skill 选择与编排日志）

## 6. 当前风险

主要风险：

- parser 对真实论文模板差异的适配还不够强
- 五个维度仍都是启发式规则版本，不是最终效果上限
- skill loader 现在只够支撑 MVP，不够支撑完整治理流程
- disagreement detection 目前仍是启发式候选机制，不代表最终 debate 效果
- 当前 selective debate 仍是最小复核版，不代表最终多 reviewer 裁决效果

控制方式：

- 先扩大测试样本，而不是过早引入复杂架构
- 继续按固定维度逐个补 worker
- 在进入 debate 前先把单 worker 质量打稳

## 7. 维护规则

后续每次有实质性开发推进时，本文件应至少更新以下内容之一：

- 当前状态
- 已完成事项
- 测试与验证
- 下一步计划
