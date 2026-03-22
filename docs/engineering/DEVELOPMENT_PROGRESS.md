# PaperMentor OS 开发进度

## 1. 文档目的

本文件用于持续记录 PaperMentor OS 的实际开发进展，避免项目状态只存在于对话、终端输出或个人记忆中。

使用原则：

- 只记录已经完成、正在推进或明确排定的开发事项
- 不重定义 PRD 和架构边界
- 如果实现过程中发现与 `PRD.md` 或 `ARCHITECTURE.md` 冲突，先单独标记，不在此文档里直接改边界

## 2. 当前状态

更新时间：`2026-03-22`

当前已进入：

- Sprint 2 后半段，开始补足 V1 导出与评测资产

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
- 基础 PDF 报告导出能力
- 显式按“研究内容优先于文本表达”整理的基础报告优先级逻辑
- 最小 `disagreement detection`，可为未来 selective debate 提供候选 case
- 最小 selective debate 闭环：`DebateJudgeAgent` 可对候选维度做受控裁决

当前系统尚未具备：

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
- 已支持对 `摘 要`、`参考 文献` 等带空格标题标签做规范化识别，降低模板差异导致的解析偏差
- 已支持在摘要前的前置区中选择更合理的标题候选，降低封面/院校信息导致的标题误识别
- 已支持识别并跳过摘要后的目录页与目录项，减少目录噪声污染正文结构

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
- 已开始第一轮 benchmark 驱动的 worker 精度迭代，`TopicScopeAgent` 现已区分“泛化系统标题”和“带明确对象/场景限定的系统标题”
- `LogicChainAgent` 现已识别“讨论与展望 / closing signal”类收束章节，减少对非标准结论标题的误报
- `LiteratureSupportAgent` 现已识别“已有方法比较 / 方法比较 / 对比分析”类相关工作章节，减少对非标准相关工作标题的误报
- `NoveltyDepthAgent` 现已识别“相较已有方案的差异定位 + 深度支撑”类贡献表达，减少对未直接写出“创新/贡献”字样论文的误报
- `WritingFormatAgent` 现已区分“冗长不足的摘要”和“紧凑但问题/方法/结果完整的摘要”，减少对高信息密度摘要的误报

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
- debug trace 中可回传 worker 级 skill 解析结果（rubric / policy / schema / domain）
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
- 将 fixtures 扩展为 `baseline / strong / weak / boundary` 四类样本
- 新增基于样本 catalog 的集成测试，覆盖强样本稳定输出、弱样本研究风险优先暴露、边界样本 selective debate 触发
- 新增最小离线评测模型与 benchmark runner
- 新增 `scripts/run_benchmark.py`，可基于评测样本自动生成 `docx`、运行 `ChiefReviewer` 并输出 JSON 指标摘要
- 新增评测元数据构建与加载层，benchmark case 的 expectation 生成逻辑已从脚本内联逻辑抽出
- `scripts/run_benchmark.py` 已支持 `json / markdown` 两种摘要输出，便于阶段性人工复盘
- `scripts/run_benchmark.py` 已支持基于阈值的 benchmark gate，可在指标回归时返回非零退出码
- 新增 `topic_precision_case`，用于约束 `TopicScopeAgent` 不要把“对象/场景已明确的系统设计与实现标题”误判为泛标题
- 新增 `logic_precision_case`，用于约束 `LogicChainAgent` 不要把“讨论与展望 / closing signal”类收束章节误判为缺少结论
- 新增 `literature_precision_case`，用于约束 `LiteratureSupportAgent` 不要把“已有方法比较 / 方法比较”类章节误判为缺少相关工作
- 新增 `novelty_precision_case`，用于约束 `NoveltyDepthAgent` 不要把“有比较定位和实验支撑，但未直接写创新字样”的论文误判为缺少贡献表达
- 新增 `writing_precision_case`，用于约束 `WritingFormatAgent` 不要把“紧凑但闭环完整的摘要”误判为信息量不足
- 新增 `template_variation_case`，用于约束 parser 与规则链路在 `摘 要`、`参考 文献`、章节命名差异下仍能稳定解析与评审
- 新增 `cover_page_variation_case`，用于约束 parser 在封面/院校信息位于标题前时仍能稳定定位真实论文标题
- 新增 `contents_variation_case`，用于约束 parser 在目录页位于摘要后时仍能稳定跳过目录噪声并保留真实章节结构
- 当前 benchmark 指标已覆盖：高严重度维度召回、priority first 维度准确率、debate 候选维度召回、issue title 召回、issue title 误报率、case 级通过率

当前限制：

- 仍未引入更丰富的报告去重与合并策略
- 评测样本目前虽然已有问题标题级 expectation 和可读 benchmark 摘要，但仍主要来自内部 fixture，还没有真实人工评审对照和跨模板误报统计

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
- debug 接口可返回 worker skill trace、worker run trace、orchestration trace、`debate_candidates` 和 `debate_resolutions`
- 新增 `/review/docx/pdf` 导出接口，直接返回 PDF 报告文件
- `/review/docx/pdf` 当前已在响应完成后自动清理临时导出文件，避免临时目录累积无主 PDF

当前限制：

- debug trace 当前已覆盖 skill/load/orchestration 的摘要级状态，但还没有记录更细粒度的 ledger 写入事件或每一步原始 prompt/规则命中明细
- 仍未做鉴权、访问控制或调试信息分级

### 3.10 PDF 导出

已完成：

- 新增 `PdfReportExporter`
- 采用纯 Python 最小实现生成多页 PDF，避免引入额外重依赖
- PDF 内容已覆盖总体总结、高优先级问题、维度结果、学生建议、导师摘要和安全提示
- 当前导出能力以独立 reporting 模块和独立 API 落点接入，没有修改现有 `/review/docx` JSON 契约

当前限制：

- 当前 PDF 样式仍偏基础，主要目标是稳定导出而不是视觉包装
- 暂未附加页眉页脚、学校模板样式或 debate 过程明细展开

## 4. 测试与验证

截至 `2026-03-22`，当前已通过：

- debug API 集成测试
- PDF 导出单元测试
- PDF 导出 API 集成测试
- 扩展 debug trace 的集成测试
- benchmark 逻辑单元测试
- benchmark runner 集成测试
- issue title 级 benchmark 单元测试
- benchmark dataset / markdown renderer 单元测试
- benchmark threshold gate 单元测试
- selective debate 单元测试
- schema 单元测试
- disagreement detection 单元测试
- `docx parser` 单元测试
- 模板差异 parser 单元测试
- `SkillLoader` 单元测试
- reporting 单元测试
- 扩展样本下的五维端到端集成测试

当前基线结果：

- `pytest` 通过，当前为 `45 passed`
- `scripts/run_benchmark.py` 当前在 11 个评测样本上输出：
  - `fully_passed_cases = 11/11`
  - `high_severity_dimension_recall = 1.0`
  - `priority_first_dimension_accuracy = 1.0`
  - `debate_dimension_recall = 1.0`
  - `issue_title_recall = 1.0`
  - `issue_title_false_positive_rate = 0.0`
  - 支持 `--format markdown` 输出阶段性复盘摘要
  - 支持以阈值形式作为回归门槛运行

## 5. 下一步计划

按当前顺序继续推进：

1. 继续扩展 fixtures 和评测样本，覆盖强样本/弱样本/边界样本
2. 继续把测试级 fixture 向可复用离线评测样本推进，补人工对照结果、误报统计口径和真实论文模板覆盖
3. 在五个维度都具备精度样本后，继续补“真实论文模板差异”与“跨模板误报”样本，并逐步扩展到更复杂的模板变体
4. 为 benchmark 增加问题标题层面的 precision / false positive 审核样本
5. 逐步把 benchmark gate 接入日常开发回归流程

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
