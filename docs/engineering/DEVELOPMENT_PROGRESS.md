# PaperMentor OS 开发进度

## 1. 文档目的

本文件用于持续记录 PaperMentor OS 的实际开发进展，避免项目状态只存在于对话、终端输出或个人记忆中。

使用原则：

- 只记录已经完成、正在推进或明确排定的开发事项
- 不重定义 PRD 和架构边界
- 如果实现过程中发现与 `PRD.md` 或 `ARCHITECTURE.md` 冲突，先单独标记，不在此文档里直接改边界

## 2. 当前状态

更新时间：`2026-03-23`

当前已进入：

- Sprint 3 中段，开始切并发 orchestrator 第一阶段，并继续保留规则版/模型版双轨基础能力

当前系统已经具备：

- Python 项目骨架
- 核心 schema 校验层
- `docx` 解析
- 内存版 `EvidenceLedger`
- 基础 `GuidanceComposer`
- 可运行的 `ChiefReviewer`
- orchestrator 内部五维 worker batch 并发执行基线
- `ReviewRun / WorkerRun / RunState` 运行态对象基线
- 五个已接入主链路的 workers：
  - `TopicScopeAgent`
  - `LogicChainAgent`
  - `LiteratureSupportAgent`
  - `NoveltyDepthAgent`
  - `WritingFormatAgent`
- 文件系统版最小 `SkillLoader`
- FastAPI 最小接口入口
- 非破坏式 debug review API，可返回 review trace
- 最小 async review run API 原型
- review run 文件快照恢复基线
- review run SSE 事件流原型
- review run SSE `Last-Event-ID` 续传与明确终止事件
- review run SSE 心跳节流与代理友好 header
- review run snapshot 跨进程锁与跨实例回读
- review run ownership / lease 基线
- review run stale lease 显式 claim 与 owner 写保护
- review run claim 后基于 source_path/checkpoint 的自动 resume
- review run local cooperative cancel 基线
- async run registry 生命周期关闭与 executor 清理
- review run 终态竞态修正、TTL 清理与原子快照写入
- 基础 PDF 报告导出能力
- 最小 `LLM` 抽象层基线
- 显式按“研究内容优先于文本表达”整理的基础报告优先级逻辑
- 最小 `disagreement detection`，可为未来 selective debate 提供候选 case
- 最小 selective debate 闭环：`DebateJudgeAgent` 可对候选维度做受控裁决

当前系统尚未具备：

- 全维度真实模型 worker 接入
- 真实在线 provider 的端到端验证基线
- 跨进程协调的一致性 run registry
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
- 已支持识别并跳过带多级编号、无空格目录项和制表符页码的复杂目录页，降低复杂目录布局误入正文的风险
- 已支持保留双语摘要场景下的中英文摘要内容，减少第二摘要块对正文起点的污染
- 已支持将 `关键词 / Key words` 识别为摘要前置区的一部分，减少关键词区被误判为正文标题的风险
- 已支持识别并跳过摘要后的 `分类号 / 学校代码 / 学号 / UDC` 元数据块，减少元数据区误入摘要和正文结构的风险
- 已支持识别并跳过摘要后的 `保密级别 / 作者姓名 / 指导教师` 作者信息区，减少作者信息块误入正文结构的风险
- 已支持识别并跳过附录目录项与附录正文，减少附录内容对主正文五维评审的污染
- 已支持识别并跳过带标题的英文附录章节（如 `Appendix A Prompt Templates`），减少英文附录补充材料对主正文评审的污染
- 已支持识别并跳过摘要后的 `学院 / 院系 / 专业 / 班级 / 作者单位` 组合信息区，减少院系信息块误入正文结构的风险
- 已支持在正文开始前识别并跳过 `独创性声明 / 学术诚信承诺书` 等声明类前置页，减少前置说明页污染正文结构
- 已支持识别并跳过摘要后的复合前置区组合（如 `关键词 / Key words`、`分类号 / 学校代码 / 学号 / UDC`、`学院 / 专业`、`导师组 / 学位类型`、英文目录与附录目录的叠加布局），减少复杂学校模板前置区污染正文结构的风险
- 已支持在进入附录后持续忽略附录内的图表标题等短标题项，减少附录图表说明被重新误判为正文标题的风险
- 已支持识别 `关键词 本科论文初审`、`学校代码 10487`、`导师组 智能系统导师组`、`学位类型 工学学士` 等空格对齐前置区字段，减少仅因学校模板未使用冒号分隔而导致的前置区误入正文风险
- 已支持在 `abstract / keywords / front_matter` 状态下保留跨行前置区字段值（如 `学校代码` 下一行 `10487`、`导师组` 下一行 `智能系统导师组`），减少字段值被误判为正文标题的风险
- 已支持识别正文后的 `附录目录` 页，并在进入附录目录后持续隔离附录目录项与附录正文，减少附录目录页和补充材料污染主正文结构的风险
- 已支持识别制表符/表格化对齐的前置区字段（如 `学校代码<TAB>10487`、`导师组<TAB>智能系统导师组`），减少表格化学校模板前置区误入正文的风险
- 已支持识别 `附录图目录 / 附录表目录 / List of Appendix Figures / List of Appendix Tables` 等附录图表目录页标题，并在进入后持续隔离后续附录目录项与附录正文
- 已支持按 docx 正文块顺序提取段落与表格行，并解析摘要后表格单元格中的 `关键词 / Key words / 学校代码 / 学号 / 学院 / 专业 / 导师组 / 学位类型` 等前置区字段，减少真实学校模板中表格元数据被整体忽略的风险
- 已支持递归提取合并单元格与嵌套表格中的前置区字段，并去重相邻重复单元格文本，减少复杂学校模板中的表格元数据污染摘要与正文结构的风险
- 已支持在 `contents` 模式下识别并跳过 `PAGEREF / HYPERLINK / TOC / _Toc... / \h / \z / \u` 等目录字段代码残留，减少 Word 自动目录超链接噪声误触发正文起点的风险
- 已支持在标题选择阶段显式压低封面页表格块中的元数据行、关键词行和目录噪声候选分数，减少 `学校 / 专业 / 指导教师 / 学号` 表格块与真实论文题名竞争时的误选风险
- 已支持在标题前存在学校封面表格块时稳定保留真实论文题名，减少 `学院 / 专业 / 指导教师 / 学号` 等封面表格行在无样式场景下被误选为标题的风险
- 已支持在正文尾部识别并隔离 `致谢 / 后记 / Acknowledgements / 攻读学位期间取得的成果` 等 back matter 页面，减少参考文献前说明性页面污染主正文五维评审的风险
- 已支持在 `references` 模式下识别 `作者简介 / Author Biography / About the Author / 个人简历` 等参考文献后页面，并在进入后停止继续累积参考文献，减少作者简介页污染参考文献列表的风险
- 已支持在 `contents` 模式下忽略不构成真实章节起点的学校名、论文类型、孤立页码等目录页页眉/页脚残留，减少目录页噪声误触发正文开始的风险
- 已支持识别正文中的 `图 1-1 ... / 表 2-1 ... / Figure 3-1 ... / Table 4-2 ...` 等图表标题，并将其保留为当前章节段落而不是新章节，减少 caption 误拆章节的风险
- 已支持识别正文中的 `式 1-1 ... / 公式 1-2 ... / Equation 2-1 ... / Equation (2-2) ...` 等公式说明块，并将其保留为当前章节段落而不是新章节，减少公式 caption 误拆章节的风险
- 已支持识别正文中的 `注 1-1 ... / 说明 1-2 ... / Note 2-1 ... / Remark 2-2 ...` 等注释性说明块，并将其保留为当前章节段落而不是新章节，减少图片注释块和说明性短行误拆章节的风险
- 已支持过滤正文中的孤立页码、罗马页码和脚注标记行（如 `- 1 - / ii / [1] / ①`），减少页脚残留和脚注锚点误入正文内容或误拆章节的风险
- 已支持过滤正文中重复出现的学校页眉、题名重复行和表格化元数据残留（如 `某某大学本科毕业论文 / 学号 2020123456 / 专业 软件工程`），减少页眉页脚噪声污染正文证据的风险
- 已支持过滤正文中重复出现的英文页眉、英文题名重复行和英文元数据短行（如 `Undergraduate Thesis / Student ID 2020123456 / Major Software Engineering`），减少英文页眉页脚噪声污染正文证据的风险
- 已支持在正文已经开始后忽略再次出现的 `Abstract / 摘要` 页眉残留，减少跨页英文摘要页眉将 parser 错误拉回摘要模式的风险
- 已支持在正文进入当前章节后忽略再次出现的同名章节标题残留，减少跨页重复章节页眉将 parser 错误拆成重复章节的风险
- 已支持过滤正文中的脚注正文说明块（如 `[1] 注：... / ① Remark: ...`），减少脚注正文残留污染正文证据和问题定位的风险
- 已支持在子章节正文中忽略再次出现的上级章节标题残留，减少跨页页眉中的父章节标题将 parser 错误拆成重复章节的风险
- 已支持在更细一级小节正文中忽略再次出现的子章节标题残留，减少跨页页眉中的子章节标题将 parser 错误拆成重复 subsection 的风险
- 已支持在更细一级正文中忽略编号一致且文本为已出现章节标题前缀的缩写章节标题残留，减少跨页页眉中的缩写标题将 parser 错误拆成重复章节的风险
- 已支持在更细一级正文中忽略无编号且文本为已出现编号章节标题前缀的缩写页眉标题残留，减少跨页页眉中的无编号缩写标题将 parser 错误拆成重复章节的风险
- 已支持读取 `word/footnotes.xml` 中的真实 docx 脚注对象文本，并过滤与脚注对象完全一致的漂移正文块，减少脚注对象和脚注正文重复污染正文证据的风险
- 已支持读取 `word/endnotes.xml` 中的真实 docx 尾注对象文本，并过滤与尾注对象完全一致的漂移正文块，减少尾注对象和尾注正文重复污染正文证据的风险
- 已支持在脚注与尾注混排时仅过滤与对象级注释文本完全一致的漂移正文块，并保留正文中的相似说明句，减少混排注释对象误伤正文论证的风险
- 已支持将真实脚注/尾注对象中的分段文本纳入精确匹配，过滤跨行脚注/尾注漂移正文块，同时保留正文中的总结性说明句，减少多段注释对象污染正文证据的风险
- 已支持默认不将正文中的表格行视为章节标题，并在表格邻接注释对象场景下稳定过滤重复注释正文，减少参数表/配置表被误拆成章节的风险

当前限制：

- 仍未处理更复杂的富文本注释对象、图片与 `pdf`
- 对格式混乱的 `docx` 容错仍有限

### 3.4 Worker 与编排

已完成：

- `TopicScopeAgent`
- `LogicChainAgent`
- `LiteratureSupportAgent`
- `NoveltyDepthAgent`
- `WritingFormatAgent`
- `ChiefReviewer` 串联解析、skill 解析、worker 执行、ledger 记录和最终报告生成
- `ChiefReviewer` 已从固定五维串行 `for-loop` 升级为固定 worker batch 并发执行，聚合阶段仍按固定五维顺序写回 `ledger / checkpoint / report`
- orchestrator 已增加最小 worker run 状态记录，当前内部可区分 `pending / running / completed / failed / fallback_completed`
- 新增 `src/papermentor_os/orchestrator/run_state.py`
  - 引入 `RunState`
  - 引入 `WorkerRun`
  - 引入 `ReviewRun`
- `ChiefReviewer` 已开始在每次运行时维护 `last_review_run`
  - 记录 `run_id / worker_sequence / selected_worker_ids`
  - 记录 `resumed_from_checkpoint / checkpoint_completed_worker_count`
  - 记录每个 worker 的 `state / from_checkpoint / score / finding_count / summary / fallback_used / error_message`
- 已开始第一轮 benchmark 驱动的 worker 精度迭代，`TopicScopeAgent` 现已区分“泛化系统标题”和“带明确对象/场景限定的系统标题”
- `LogicChainAgent` 现已识别“讨论与展望 / closing signal”类收束章节，减少对非标准结论标题的误报
- `LiteratureSupportAgent` 现已识别“已有方法比较 / 方法比较 / 对比分析”类相关工作章节，减少对非标准相关工作标题的误报
- `NoveltyDepthAgent` 现已识别“相较已有方案的差异定位 + 深度支撑”类贡献表达，减少对未直接写出“创新/贡献”字样论文的误报
- `WritingFormatAgent` 现已区分“冗长不足的摘要”和“紧凑但问题/方法/结果完整的摘要”，减少对高信息密度摘要的误报

当前特点：

- 五个固定维度 worker 已在 orchestrator 内部并发提交执行
- 结果聚合、checkpoint 写回、维度输出顺序和最终 compose 仍保持确定性
- 已引入最小 selective debate，但还不是完整多 reviewer 裁决
- 研究内容类问题在 ledger 优先级中高于写作格式类问题
- 最终报告层也显式保证研究内容类问题优先于写作规范类问题

当前限制：

- API 仍是同步请求，尚未暴露 `ReviewRun / WorkerRun / RunState` 查询接口
- 当前并发能力先停留在 orchestrator 内部，前端还不能直接订阅节点级进度事件
- selective debate 仍在聚合阶段触发，没有改成 worker 间自由交互
- 当前 `ReviewRun` 还只存在于进程内存里，尚未持久化，也还没有独立查询接口

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
- 新增 `complex_contents_variation_case`，用于约束 parser 在复杂目录页包含多级编号、无空格目录项和制表符页码时仍能稳定跳过目录噪声
- 新增 `keyword_variation_case`，用于约束 parser 在 `关键词 / Key words` 位于摘要后、正文前时仍能保留关键词区并稳定定位正文章节
- 新增 `metadata_block_variation_case`，用于约束 parser 在摘要后出现 `分类号 / 学校代码 / 学号 / UDC` 元数据块时仍能稳定跳过元数据并保留真实正文结构
- 新增 `author_info_variation_case`，用于约束 parser 在摘要后出现 `保密级别 / 作者姓名 / 指导教师` 作者信息区时仍能稳定跳过信息块并保留真实正文结构
- 新增 `appendix_variation_case`，用于约束 parser 在目录页出现附录项且正文包含附录章节时仍能隔离附录内容，不污染主正文结构
- 新增 `english_appendix_variation_case`，用于约束 parser 在目录页出现英文附录项且正文包含带标题英文附录章节时仍能隔离附录内容
- 新增 `department_info_variation_case`，用于约束 parser 在摘要后出现 `学院 / 专业 / 班级 / 作者单位` 组合信息区时仍能稳定跳过信息块
- 新增 `bilingual_abstract_case`，用于约束 parser 在中英双语摘要共存时仍能保留摘要内容并稳定定位正文章节
- 新增 `declaration_variation_case`，用于约束 parser 在摘要后出现声明页/承诺书时仍能跳过前置说明并保留真实正文结构
- 新增 `front_matter_combo_variation_case`，用于约束 parser 在 `关键词 / Key words`、多元数据块、院系信息、`导师组 / 学位类型`、英文目录、附录目录和多附录正文叠加场景下仍能稳定定位真实正文
- 新增 `front_matter_spacing_variation_case`，用于约束 parser 在关键词区、元数据区和院系信息区使用空格对齐而非冒号分隔时仍能稳定保留摘要并定位真实正文
- 新增 `front_matter_multiline_variation_case`，用于约束 parser 在关键词区、元数据区和导师组信息区采用跨行字段值布局时仍能稳定保留摘要并定位真实正文
- 新增 `appendix_contents_variation_case`，用于约束 parser 在正文结束后出现 `附录目录` 页，并跟随多个附录正文时仍能稳定隔离附录目录和附录内容
- 新增 `front_matter_table_variation_case`，用于约束 parser 在前置区字段采用制表符/表格化对齐时仍能稳定保留摘要并定位真实正文
- 新增 `appendix_figure_list_variation_case`，用于约束 parser 在正文结束后出现 `附录图目录 / 附录表目录 / List of Appendix Tables` 等图表目录页时仍能稳定隔离目录页与附录正文
- 新增 `docx_table_front_matter_case`，用于约束 parser 在摘要后前置区字段位于 docx 表格单元格中时仍能稳定保留摘要并定位真实正文
- 新增 `complex_table_front_matter_case`，用于约束 parser 在摘要后前置区字段采用合并单元格与嵌套表格混排时仍能稳定保留摘要并定位真实正文
- 新增 `contents_field_code_variation_case`，用于约束 parser 在目录页出现 `PAGEREF / HYPERLINK / _Toc...` 等字段代码残留时仍能稳定跳过目录噪声并定位真实正文
- 新增 `cover_page_table_variation_case`，用于约束 parser 在标题前存在学校封面表格块时仍能稳定选择真实论文标题而非表格元数据行
- 新增 `back_matter_variation_case`，用于约束 parser 在参考文献前出现 `致谢 / 成果页 / Acknowledgements` 等尾部页面时仍能稳定隔离 back matter 并保留参考文献
- 新增 `post_reference_bio_variation_case`，用于约束 parser 在参考文献后出现 `作者简介 / Author Biography` 等页面时仍能稳定终止参考文献提取并隔离作者简介页
- 新增 `contents_header_footer_variation_case`，用于约束 parser 在目录页夹带学校名、论文类型和页码等页眉/页脚残留时仍能稳定跳过目录噪声并定位真实正文
- 新增 `caption_variation_case`，用于约束 parser 在正文中出现中英文图表标题时仍能将 caption 保留为当前章节段落而不是误判为新章节
- 新增 `equation_caption_variation_case`，用于约束 parser 在正文中出现中英文公式说明块时仍能将公式 caption 保留为当前章节段落而不是误判为新章节
- 新增 `annotation_block_variation_case`，用于约束 parser 在正文中出现中英文注释性说明块时仍能将 annotation block 保留为当前章节段落而不是误判为新章节
- 新增 `footer_footnote_noise_variation_case`，用于约束 parser 在正文中出现孤立页码、罗马页码和脚注标记残留时仍能稳定过滤结构噪声短行
- 新增 `running_header_footer_metadata_case`，用于约束 parser 在正文中出现学校页眉、题名重复行和表格化元数据残留时仍能稳定过滤运行中的页眉页脚噪声
- 新增 `running_english_header_footer_case`，用于约束 parser 在正文中出现英文页眉、英文题名重复行和英文元数据短行时仍能稳定过滤运行中的英文页眉页脚噪声
- 新增 `abstract_running_header_variation_case`，用于约束 parser 在正文中再次出现 `Abstract` 页眉残留时仍能稳定保持正文状态而不是错误回退到摘要模式
- 新增 `repeated_section_header_noise_case`，用于约束 parser 在正文中再次出现当前章节标题残留时仍能稳定保持当前章节而不是错误拆出重复章节
- 新增 `footnote_body_variation_case`，用于约束 parser 在正文中出现脚注正文说明块残留时仍能稳定过滤脚注正文噪声而不是将其纳入正文证据
- 新增 `repeated_parent_section_header_noise_case`，用于约束 parser 在子章节正文中再次出现上级章节标题残留时仍能稳定保持当前章节层级而不是错误拆出重复父章节
- 新增 `repeated_subsection_header_noise_case`，用于约束 parser 在更细一级小节正文中再次出现子章节标题残留时仍能稳定保持当前小节层级而不是错误拆出重复 subsection
- 新增 `abbreviated_section_header_noise_case`，用于约束 parser 在更细一级正文中再次出现已出现章节标题的缩写残留时仍能稳定保持当前章节层级而不是错误拆出重复章节
- 新增 `unnumbered_abbreviated_section_header_noise_case`，用于约束 parser 在更细一级正文中再次出现已出现编号章节标题的无编号缩写残留时仍能稳定保持当前章节层级而不是错误拆出重复章节
- 新增 `docx_footnote_object_variation_case`，用于约束 parser 在正文中出现真实 docx 脚注对象及其重复漂移正文块时仍能稳定过滤脚注正文污染并保留后续正文
- 新增 `docx_endnote_object_variation_case`，用于约束 parser 在正文中出现真实 docx 尾注对象及其重复漂移正文块时仍能稳定过滤尾注正文污染并保留后续正文
- 新增 `mixed_note_object_variation_case`，用于约束 parser 在脚注尾注混排且正文包含相似说明句时仍能稳定过滤重复注释正文并保留真实正文说明句
- 新增 `multiline_note_object_variation_case`，用于约束 parser 在脚注尾注对象均为多段文本且正文存在总结性说明句时仍能稳定过滤跨行注释正文并保留真实正文总结句
- 新增 `table_adjacent_note_object_variation_case`，用于约束 parser 在表格单元格邻接脚注尾注对象且表格内出现重复注释正文时仍能稳定过滤表格噪声并保留正文总结句
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
- 新增 `/review/docx/async` 异步提交接口
- 新增 `/review/runs/{run_id}` 运行态查询接口
- 新增 `/review/runs/{run_id}/events` 事件列表接口
- 新增 `/review/runs/{run_id}/events/stream` SSE 事件流接口
- 新增内存态 `InMemoryReviewRunRegistry`
  - 使用后台线程池提交 review run
  - 使用 `ChiefReviewer` 的 run update hook 持续写回最新 `ReviewRun` 快照
  - 在 run 完成后回填最终 `report / trace / error`
  - 已修正 run 已标记 `completed` 但 `report` 尚未可见的终态竞态，避免查询接口提前暴露半完成状态
  - 已支持将 run 快照持久化到 JSON 文件，并在 app 初始化时恢复历史 run
  - 快照写入已改为同目录临时文件后原子替换，降低中途写坏 JSON 快照的风险
  - 已支持按 TTL 清理已完成/失败 run 及对应快照文件，避免单进程原型长期堆积历史运行记录
  - 已为 snapshot 目录扫描和单 run 读写补文件锁，降低多进程同时恢复、写回、清理时的冲突风险
  - 已支持在查询 `run` / `events` 时按需从 snapshot 回读 run 状态，避免并行 app 实例必须重启后才能看到另一实例写出的结果
  - 已为每个 async run 引入 `owner_instance_id / lease_expires_at / last_heartbeat_at` 所属权与租约元数据
  - 执行中的实例会周期性续租，完成/失败后释放活跃租约，但保留最后执行实例标识，便于查询侧区分 owner 与 follower
  - 查询结果已支持暴露 `stale_lease / claimable / owned_by_current_instance`，便于 follower 判断是否可接管
  - 已新增显式 `POST /review/runs/{run_id}/claim` 接口，仅允许对 stale lease 的非终态 run 发起 owner claim
  - 原 owner 在失去活跃 lease 后会停止继续写回 run 状态，降低被 stale claim 后再次覆盖 snapshot 的风险
  - 已为 ownership 引入持久化 `ownership_epoch` fencing token；每次 `submit / claim` 都会推进执行代次，run update / worker checkpoint / lease heartbeat / 最终 `report / trace / error` 写回都必须匹配当前 epoch
  - 已修正“旧执行分支先失去 ownership、后在新 owner 完成并释放 lease 后重新晚写覆盖终态”的竞态；一旦执行分支失去所属 epoch，就不能再重新拿到写权
  - 已在 snapshot 中持久化最小 resume 上下文：`source_path`、`stage`、`discipline`、可安全保留的 `llm` 配置，以及运行中累计的 `ReviewCheckpoint`
  - worker 完成时会实时写回 `WorkerCheckpoint`，claim 后的新 owner 可基于已完成 worker checkpoint 和原始 `docx` 自动 resume，而不是盲目从头重跑
  - 对带 request-scoped API key 的模型请求，snapshot 不持久化密钥；此类 run 允许 claim owner，但会显式标记 `resume_started=false`
  - 旧 owner 在观察到 foreign active lease 后会触发本地 cooperative cancel：停止续租，并在 orchestrator 继续推进前尽快自停，减少 claim 后继续跑完整条链的资源浪费
  - app 生命周期结束时会显式关闭 run registry：停止本地执行控制、回收线程池，降低多次创建 app/TestClient 后残留后台线程的风险
- SSE 事件流当前已支持：
  - 为每条 review run event 输出 SSE `id:` 字段，便于客户端记录已消费位置
  - 读取 `Last-Event-ID` 头并从对应 sequence 之后继续推送事件，支持断线重连后的增量续传
  - 在 run 结束时输出明确的 `review_run_completed` / `review_run_failed` 终止事件，而不是泛化的 stream close 提示
  - 通过 `heartbeat_interval_ms` 控制心跳节流频率，并输出标准 `heartbeat` 事件
  - 返回 `Cache-Control: no-cache, no-transform`、`Connection: keep-alive` 和 `X-PaperMentor-SSE-Heartbeat-Ms`，提高代理链路下的可用性
- 新增 `/review/docx/pdf` 导出接口，直接返回 PDF 报告文件
- `/review/docx/pdf` 当前已在响应完成后自动清理临时导出文件，避免临时目录累积无主 PDF

当前限制：

- debug trace 当前已覆盖 skill/load/orchestration 的摘要级状态，但还没有记录更细粒度的 ledger 写入事件或每一步原始 prompt/规则命中明细
- 仍未做鉴权、访问控制或调试信息分级
- 当前 async run registry 虽然已有文件快照恢复、TTL 清理、原子写入、基础跨进程锁、owner lease、显式 claim、自动 resume 和本地 cooperative cancel，但还没有做 provider 级强中断、跨进程抢占式终止或更完整的旧 owner 外部副作用治理
- 当前 SSE 事件流虽然已有 `Last-Event-ID` 续传、标准 heartbeat 和代理友好 header，但还没有做反向代理超时矩阵验证和 WebSocket 方案对比

### 3.10 PDF 导出

已完成：

- 新增 `PdfReportExporter`
- 采用纯 Python 最小实现生成多页 PDF，避免引入额外重依赖
- PDF 内容已覆盖总体总结、高优先级问题、维度结果、学生建议、导师摘要和安全提示
- 当前导出能力以独立 reporting 模块和独立 API 落点接入，没有修改现有 `/review/docx` JSON 契约

当前限制：

- 当前 PDF 样式仍偏基础，主要目标是稳定导出而不是视觉包装
- 暂未附加页眉页脚、学校模板样式或 debate 过程明细展开

### 3.11 LLM 调用抽象层

已完成：

- 新增 `src/papermentor_os/llm/` 目录，包含 provider 配置、基础异常、消息/响应模型和 `LLMClient`
- 新增 `ProviderConfig`，统一承载 `provider_id / base_url / api_key / model_name / temperature / max_tokens / timeout / max_retries / prompt_char_budget`
- 新增 `FakeLLMProvider`，用于离线测试结构化输出、重试和 fallback 路径
- 新增 `OpenAICompatibleProvider`，为后续接 OpenAI 风格接口预留统一 provider 落点
- `LLMClient` 已支持：
  - 超时配置透传
  - provider 级重试
  - 基于 `prompt_char_budget` 的最小输入预算控制
  - 结构化 JSON 输出解析与 schema 校验
- `TopicScopeAgent` 已增加模型版 PoC，可在 `rule_only / model_only / model_with_fallback` 三种后端模式下运行
- `LogicChainAgent` 已增加模型版 PoC，可在 `rule_only / model_only / model_with_fallback` 三种后端模式下运行
- `LiteratureSupportAgent` 已增加模型版 PoC，可在 `rule_only / model_only / model_with_fallback` 三种后端模式下运行
- `NoveltyDepthAgent` 已增加模型版 PoC，可在 `rule_only / model_only / model_with_fallback` 三种后端模式下运行
- `WritingFormatAgent` 已增加模型版 PoC，可在 `rule_only / model_only / model_with_fallback` 三种后端模式下运行
- 五个固定维度 worker 的模型版 PoC 默认仍复用原有 `DimensionReport` / `ReviewFinding` 契约，不修改 `/review/docx` JSON 输出结构
- 五个固定维度 worker 已保留规则版基线，并在模型输出无效时支持自动 fallback 到规则版
- `ChiefReviewer` 已可通过依赖注入接收五个模型版 worker，为后续 benchmark 双轨对照和逐维接模提供最小接入点
- 新增 `reviewer_factory`，统一承接 API 与 benchmark 脚本的 reviewer 构建逻辑，避免 provider 注入和 worker 装配在多处分叉
- 现有 provider 抽象已兼容 OpenAI 风格接口
- 新增 `scripts/run_live_llm_smoke.py`，提供 opt-in 的真实在线 provider smoke harness
  - 支持通过 CLI 参数或 `PAPERMENTOR_OS_SMOKE_*` 环境变量传入 `base_url / api_key / model_name / review_backend`
  - 默认使用内置 `topic_precision_case` 生成临时 `docx` 发起一次最小真实请求
  - 支持通过 `--worker-id` 只跑单个维度 worker，便于定位在线模型的 prompt / 超时瓶颈
  - 输出最小 JSON 观测结果，包括 parsed/fallback 状态、request attempts、retry、token 用量、finding 数和 priority action 数
  - 当任一 worker 未成功返回结构化模型输出时返回非零退出码，便于后续做最小在线验收
  - `--worker-id` 路径已改为优先调用 `ChiefReviewer.run_worker_smoke()` 公共接口，不再错误耦合 `_execute_worker_review()` 与未初始化的 `last_review_run`
  - 真实 `ChiefReviewer` 下的单 worker smoke 已可直接返回正确的 `DimensionReport + WorkerExecutionTrace`，并持续产出最小 orchestration/worker trace 观测
- `OpenAICompatibleProvider` 已补充 Ark `responses` 风格兼容
  - 当 `base_url` 指向 `volces.com` 或 `/api/v3` 时，普通文本生成优先走 `/responses`
  - 请求体会把现有 `system/user` 文本消息映射成 `instructions + input_text`
  - `usage.input_tokens / output_tokens` 会归一到现有 `prompt_tokens / completion_tokens / total_tokens`
  - provider JSON schema 路径仍保留 `chat/completions`，不破坏现有 OpenAI 风格兼容
  - 对 `deepseek-*` 模型已补充 Ark 路由例外，普通文本生成会改走 `chat/completions`
  - 对 `chat/completions` 返回的 `usage.*_details` 冗余字段已做兼容过滤，避免额外字段破坏最小 token 统计
- 本轮已补结构化输出链路的两个关键修正：
  - `ReviewLLMConfig` 已新增 `structured_output_mode`，并在 `reviewer_factory` 中按 provider 家族解析默认策略
  - 标准 OpenAI 风格 base URL 默认走 `provider_json_schema`
  - Ark `/api/v3` 默认仍走 `prompt_json`，避免把未验证的 provider-native schema 直接强行套到当前真实联调路径
  - `LLMClient.generate_structured()` 的 prompt-json 分支已改为保护前缀 schema 指令，避免它在预算裁剪时被尾部截断逻辑误删
- 本轮已将 `LogicChainAgent`、`LiteratureSupportAgent`、`NoveltyDepthAgent` 与 `WritingFormatAgent` 的模型 prompt 收敛到与 `TopicScopeAgent` 接近的体量
  - 删除 `paper_id / discipline / stage` 等低价值字段
  - 将章节上下文收缩为少量关键 section 与首段
  - 对 rubric / policy / domain / references preview / allowed anchors 做截断与按需注入
  - 继续保持 `DimensionReport` / `ReviewFinding` 契约不变
- 已用豆包 Ark `doubao-seed-2-0-lite-260215` 做最小真实联调
  - 最小 `curl /responses` 请求可正常返回，说明 `base_url / Authorization / responses` 兼容层已经打通
  - `scripts/run_live_llm_smoke.py --review-backend model_with_fallback --timeout 5 --max-retries 0` 下，五个 worker 均触发 fallback，错误类型为 `provider_network`
  - 缩小到 `--prompt-char-budget 2500 --timeout 15 --max-retries 0` 后，`TopicScopeAgent` 出现 `structured_output`，其余四个 worker 仍表现为 `provider_network`
  - 在 `--worker-id TopicScopeAgent --timeout 30 --max-retries 0 --prompt-char-budget 2500` 下，`TopicScopeAgent` 已能稳定返回 `parsed=true`，单次请求 `llm_total_tokens = 2199`
  - 当前结论是：接口兼容已验证，`TopicScopeAgent` 已通过单 worker 真实 smoke；剩余问题主要在其他四个维度的 prompt 负载和超时阈值
- 已用豆包 Ark `doubao-seed-2-0-code-preview-260215` 做对比 smoke
  - `--worker-id TopicScopeAgent --timeout 30 --max-retries 0 --prompt-char-budget 2500` 连续两次都能较快返回，但均触发 `structured_output`
  - 两次真实返回的 `llm_total_tokens` 分别为 `1524` 与 `1642`
  - 当前结论是：`code-preview` 相比 `lite` 响应更快，但在当前论文评审结构化 JSON 任务上服从性更差，不适合作为现阶段首选模型
- 已用豆包 Ark `doubao-seed-2-0-pro-260215` 做对比 smoke
  - 最小 `curl /responses` 请求可正常返回，说明模型本身可用、接口也没有问题
  - `--worker-id TopicScopeAgent --timeout 30 --max-retries 0 --prompt-char-budget 2500` 连续两次都触发 `provider_runtime`
  - 两次 smoke 都没有记录到可用 `llm_total_tokens`，说明当前失败发生在 provider 文本提取之前或文本不可消费阶段
  - 当前结论是：`pro` 在最小请求上可用，但在当前单 worker 评审 prompt 下稳定性还不如 `lite`
- 已用 Ark `deepseek-r1-250528` 做对比 smoke
  - 最小 `curl /chat/completions` 请求可正常返回，并且能按要求只输出 JSON 对象
  - 修正 `deepseek-*` 路由到 `chat/completions` 后，`--worker-id TopicScopeAgent --timeout 30 --max-retries 0 --prompt-char-budget 2500` 连续两次都触发 `structured_output`
  - 两次真实返回的 `llm_total_tokens` 分别为 `2289` 与 `2300`
  - 当前结论是：`deepseek-r1-250528` 在当前任务上不是 provider 兼容问题，而是结构化 JSON 服从性仍不稳定
- 已用 Ark `glm-4-7-251222` 做修复后 smoke
  - `--worker-id TopicScopeAgent --timeout 30 --max-retries 0 --prompt-char-budget 2500` -> `parsed=true`，`llm_total_tokens = 967`
  - `--worker-id LogicChainAgent --timeout 30 --max-retries 0 --prompt-char-budget 2500` -> `parsed=true`，`llm_total_tokens = 1982`
  - `--worker-id LiteratureSupportAgent --timeout 30 --max-retries 0 --prompt-char-budget 2500` -> `provider_runtime`
  - 完整五维 `model_with_fallback --timeout 30 --max-retries 0 --prompt-char-budget 2500` -> `1/5` worker `parsed`，其余 `LogicChain / LiteratureSupport / NoveltyDepth / WritingFormat` 触发 `provider_runtime`
  - 当前结论是：这轮修复已显著改善单 worker 可用性，整链问题已从“全维度不稳”收缩为“部分 worker 仍有 provider/runtime 压力 + 连续多次调用下的整链稳定性”
- `/review/docx`、`/review/docx/debug` 与 `/review/docx/pdf` 已支持可选的 request-scoped `llm` 配置，可接收 `review_backend / provider_id / base_url / api_key / model_name` 等字段，为后续前端 BYOK 模式提供最小入口
- API 层已补充最小前端友好错误映射：
  - `llm_configuration_error` -> `400`

### 3.12 运行时稳定性改造启动

已完成：

- 本轮开始落实运行时稳定性改造的第一阶段，只做 `WorkerRunPolicy`，不改 `/review/docx` JSON 报告契约，也不改变五维固定 worker 边界
- 新增 `src/papermentor_os/runtime/policy.py`
  - 引入 `WorkerRunPolicy`
  - 支持按 worker 覆盖 `timeout / max_retries / prompt_char_budget / structured_output_mode`
  - 支持最小 `cooldown_after_success_ms / cooldown_after_failure_ms`
- `reviewer_factory` 已开始为 `ChiefReviewer` 注入 worker 级 runtime policy
  - 当前默认先做保守策略：主要收敛各 worker 的 `prompt_char_budget`
  - 对 Ark `/api/v3` 家族增加了最小 cooldown 默认值，为后续真实 provider 稳定性调优预留落点
- `ChiefReviewer` 已开始在执行 worker 前应用 policy 覆盖，并在 worker batch 聚合阶段按固定顺序执行最小 cooldown
- 当前这一步已切到“固定五维并发提交 + 确定性聚合”，但还没有进入可查询异步 API，也没有改变 selective debate 的边界
- 新增单元测试覆盖：
  - `reviewer_factory` 的 worker policy 默认值
  - `ChiefReviewer` 的 policy 应用与 success/failure cooldown
  - `ChiefReviewer` 的并发 worker batch 起跑
  - 并发完成顺序下的 checkpoint / skill trace 稳定顺序
  - `ReviewRun` 生命周期与 checkpoint 集成状态

### 3.13 运行时恢复策略补强

已完成：

- `LLMClient` 已从“立即重试”升级为“按错误类型判定是否重试 + 指数退避 + jitter”
  - 新增 `retry_backoff_base_ms / retry_jitter_ms`
  - 当前重试只对 provider 明确标记为 `retryable=true` 的错误生效
  - 运行统计已补充 `retry_sleep_ms`
- `LLMProviderError` 已开始承载结构化错误元信息：
  - `category`
  - `retryable`
  - `status_code`
- `LLMStructuredOutputError` 已开始输出更细分类：
  - `structured_output_empty`
  - `structured_output_invalid_json`
  - `structured_output_schema_mismatch`
  - `structured_output_missing_json_object`
  - `structured_output_incomplete_json`
- `OpenAICompatibleProvider` 已开始输出更细 provider 错误类别：
  - `rate_limit`
  - `server_error`
  - `network_timeout`
  - `network_connect`
  - `endpoint_mismatch`
  - `auth_error`
  - `invalid_response_shape`
  - `empty_output`
- `BaseReviewAgent.categorize_llm_error()` 已改为优先消费结构化错误类别，避免继续依赖字符串前缀推断
- `ReviewLLMConfig / ProviderConfig / WorkerRunPolicy` 已增加最小退避参数承载能力，为后续 worker 级 retry 策略继续细化预留接口
- 新增单元测试覆盖：
  - `LLMClient` 可重试错误的指数退避与 sleep 统计
  - `LLMClient` 非可重试 provider 错误不重复请求
  - `OpenAICompatibleProvider` 的 `429 -> rate_limit`
  - `OpenAICompatibleProvider` 的无效响应体 -> `invalid_response_shape`

### 3.14 最小 checkpoint / resume

已完成：

- 新增 `src/papermentor_os/orchestrator/checkpoint.py`
  - 引入 `ReviewCheckpoint`
  - 引入 `WorkerCheckpoint`
- `ChiefReviewer` 已新增最小 checkpoint / resume 能力
  - `run_review_until(..., stop_after_worker_id=...)` 可在指定 worker 后产出 checkpoint
  - `review_paper(..., checkpoint=...)` 可从已完成 worker 继续执行，不重跑 checkpoint 中已有结果
  - checkpoint 当前校验 `paper_id / stage / discipline` 一致性，避免把不同论文的中间状态混用
- 当前 checkpoint 仍是内存态最小实现
  - 不改 `/review/docx` API 契约
  - 不引入持久化存储
  - 不改变 selective debate 的触发逻辑
- 新增单元测试覆盖：
  - partial checkpoint 生成
  - resume 后跳过已完成 worker
  - 不同 paper checkpoint 拒绝恢复

### 3.15 checkpoint 观测闭环

已完成：

- `OrchestrationTrace` 已新增 checkpoint / resume 观测字段：
  - `resumed_from_checkpoint`
  - `checkpoint_completed_worker_count`
  - `resumed_worker_ids`
  - `skipped_worker_ids`
  - `resume_start_worker_id`
- `ChiefReviewer` 在 resume 场景下已开始把上述信息写入 debug trace 的 `orchestration`
- benchmark 已开始消费 `orchestration_trace`
  - case 级结果可记录本次是否来自 resume
  - summary 级可汇总 resumed case 数、checkpoint 已完成 worker 数、resume 跳过 worker 数
- markdown renderer 已支持在存在 resume 样本时输出 checkpoint 观测摘要
- 新增测试覆盖：
  - checkpoint 恢复后的 orchestration trace 字段
  - benchmark 对 checkpoint / resume 观测的聚合
  - debug API 默认非 resume 情况下的 trace 字段兼容
  - `llm_provider_error` -> `502`
  - `llm_structured_output_error` -> `502`
- request-scoped `llm.base_url` 已增加最小安全约束：
  - 仅允许 `http/https`
  - 默认拒绝 `localhost` / 私有网段 / `.local`
  - 本地联调可通过 `PAPERMENTOR_OS_ALLOW_PRIVATE_LLM_BASE_URLS=1` 显式放开
- API 错误响应已默认做 provider 细节脱敏，避免把 request-scoped `api_key` 或下游报错原文直接透给前端
- `EvidenceLedger` 已可按维度记录 worker 执行元数据
- debug trace 的 `worker_runs` 已支持返回：
  - `review_backend`
  - `llm_provider_id`
  - `llm_model_name`
  - `llm_finish_reason`
  - `structured_output_status`
  - `fallback_used`

当前限制：

- 当前虽然五个维度都已有模型版 PoC，并且已有 opt-in live smoke harness，但还没有拿真实在线 provider / API key 跑出固定验收基线
- 豆包 Ark 已验证最小 `responses` 请求可通，但完整 reviewer smoke 仍不稳定，当前主要表现为 prompt 负载下的慢响应 / 超时，以及首维 JSON 结构化输出不稳定
- 还没有真实在线 provider 的集成测试或成本/时延观测
- API 层当前只支持统一的 OpenAI 兼容 provider 配置，还没有做更细粒度的多模型路由、服务端密钥托管或前端鉴权保护
- 当前预算控制使用字符预算近似，尚未接入真实 token 统计
- Ark / `glm-*` 等真实模型是否支持 provider-native JSON schema 仍未作为固定基线验证，因此当前仍保留 `prompt_json` 作为 Ark 默认 structured output 策略
- `glm-4-7-251222` 在单 worker 下已验证可用，但完整五维链路仍未通过固定 smoke 基线

### 3.16 benchmark resume 演练闭环

已完成：

- `scripts/run_benchmark.py` 已新增可选 `--resume-after-worker-id`
  - benchmark 可先对每个 case 执行 `run_review_until(..., stop_after_worker_id=...)`
  - 再复用同一 `ReviewCheckpoint` 走 `review_paper(..., checkpoint=...)`
  - 不改默认 benchmark 行为，不影响现有 gate
- benchmark resume 路径会复用现有 `orchestration_trace`
  - case 级结果可直接标记 `resumed_from_checkpoint`
  - summary 级可稳定汇总 resumed case 数、checkpoint 已完成 worker 数、resume 跳过 worker 数
- 新增集成测试覆盖：
  - benchmark 端到端 checkpoint resume 路径
  - CLI `--resume-after-worker-id` 参数透传与 markdown 输出

当前意义：

- checkpoint / resume 现在不再只是 orchestrator 内部能力
- benchmark 已可显式演练“先跑到第 N 个 worker，再恢复到整链”的路径
- 后续如果要把同一能力接到 live smoke 或真实 provider 验证，已经有现成脚手架可复用

### 3.17 live smoke resume 演练闭环

已完成：

- `scripts/run_live_llm_smoke.py` 已新增可选 `--resume-after-worker-id`
  - smoke 可先执行 `run_review_until(..., stop_after_worker_id=...)`
  - 再复用同一 `ReviewCheckpoint` 执行 `review_paper(..., checkpoint=...)`
  - 当前与 `--worker-id` 明确互斥，避免把单 worker smoke 和整链 resume 混成同一条路径
- smoke 输出 payload 已增加最小 resume 观测：
  - `resume_after_worker_id`
  - `resumed_from_checkpoint`
  - `checkpoint_completed_worker_count`
  - `skipped_worker_count`
  - `resume_start_worker_id`
- `scripts/run_live_llm_smoke.py` 现已支持 `--compare-resume-after-worker-id`
  - 可在同一条命令里同时跑“整链直跑”与“checkpoint 恢复”两条路径
  - 输出 `baseline / resume / parsed_worker_count_delta / fallback_worker_count_delta`
  - 便于真实在线 provider 稳定性对比，不必手动跑两次命令拼结果
- `scripts/run_live_llm_smoke.py` 现已支持 `--phase-timeout-seconds`
  - 可对单个 smoke phase 或 compare 分支施加硬超时
  - compare 路径下即便 baseline 或 resume 某一支超时/报错，也会保留另一支结果
  - 输出 `phase_error / phase_timed_out`，避免真实在线 provider 长时间卡住时整条命令失去诊断价值
- 新增集成测试覆盖：
  - smoke resume 路径的 payload 汇总
  - `--worker-id` 与 `--resume-after-worker-id` 互斥校验
  - 真实 `ChiefReviewer` 的单 worker smoke 路径
  - smoke compare-resume 路径与 CLI 参数透传
  - compare-resume 路径的 phase error 保留
  - `--phase-timeout-seconds` CLI 透传

当前意义：

- checkpoint / resume 现在已经同时接入 benchmark 和 live smoke
- 后续做真实在线 provider 稳定性验证时，可直接比较“整链直跑”与“先跑两维，再恢复”的差异
- 即使真实 provider 在整链阶段出现超长卡顿，也能拿到结构化的部分结果和超时诊断
- 当前模块已基本形成从 orchestrator 到 benchmark/smoke 的完整闭环
- 本轮真实 Ark 验证：
  - `glm-4-7-251222` + `model_with_fallback` + `prompt_char_budget=2500`
  - 使用 `--compare-resume-after-worker-id LogicChainAgent --phase-timeout-seconds 15`
  - baseline 与 resume 两条分支都在 15s phase timeout 内未完成，当前结论是整链时延瓶颈仍未被 resume 策略单独解决

### 3.12 双轨 Benchmark

已完成：

- `scripts/run_benchmark.py` 已支持在单次执行中运行多变体 benchmark，可通过 `--variant rule --variant model_with_fallback` 等方式输出对照结果
- benchmark 脚本现已支持传入 request-scoped `llm` 配置，字段与 API 侧保持一致，便于后续前端 BYOK 和命令行验收共用同一套 provider 参数
- 新增 benchmark comparison 输出模型，可同时保留多个变体的摘要、指标与耗时信息
- markdown renderer 已支持 comparison 视图，可同时展示规则版与模型版的 case 级结果和摘要指标
- benchmark 入口已复用 `reviewer_factory`，确保 API 与 benchmark 在 reviewer 构造、worker 装配和 provider 接入路径上保持一致
- `LLMClient` 已为每次模型调用补充最小运行统计，包括 request attempts、retry count 和 usage token 信息
- debug trace 的 `worker_runs` 已支持返回最小 LLM 观测字段：
  - `llm_request_attempts`
  - `llm_retry_count`
  - `llm_prompt_tokens`
  - `llm_completion_tokens`
  - `llm_total_tokens`
- debug trace 的 `worker_runs` 已支持返回 `llm_error_category`，用于区分 `provider_network / provider_http / structured_output / configuration` 等失败类型
- debug trace 已新增 `debate_resolution_traces`，把 selective debate 的 resolution、触发时的 candidate 上下文和对应 worker 的模型执行元数据关联在一起
- `DebateJudgeAgent` 已支持输出最小决策快照，`debate_resolution_traces` 现可返回：
  - `confidence_floor`
  - `decision_policy_summary`
  - `upheld_finding_count`
  - `dropped_finding_count`
  - `dropped_issue_reasons`
- benchmark case / summary 已支持汇总最小模型稳定性与成本观测：
  - request attempts
  - retry count
  - fallback count
  - error count
  - error categories
  - usage observation count
  - prompt/completion/total tokens
- `scripts/run_benchmark.py` 已支持通过用户显式传入的单价参数做最小成本估算：
  - `--llm-input-price-per-1k-tokens`
  - `--llm-output-price-per-1k-tokens`
- benchmark dataset 已支持按 variant 解析 expectation：
  - `rule`
  - `model_only`
  - `model_with_fallback`
- `build_expectation_from_case` 与 benchmark runner 已能按变体读取 case 级 override，为后续“规则版 vs 模型版”双轨验收预留基础设施
- 已为全部 `evaluation_fixture` 样本显式种下 `model_with_fallback` expectation override，当前覆盖 51 个 case，包括：
  - `strong_review_case`
  - `topic_precision_case`
  - `logic_precision_case`
  - `literature_precision_case`
  - `novelty_precision_case`
  - `writing_precision_case`
  - `weak_review_case`
  - `boundary_review_case`
  - `template_variation_case`
  - `cover_page_variation_case`
  - `cover_page_table_variation_case`
  - `back_matter_variation_case`
  - `post_reference_bio_variation_case`
  - `contents_variation_case`
  - `complex_contents_variation_case`
  - `contents_header_footer_variation_case`
  - `abstract_running_header_variation_case`
  - `footnote_body_variation_case`
  - `docx_footnote_object_variation_case`
  - `docx_endnote_object_variation_case`
  - `mixed_note_object_variation_case`
  - `multiline_note_object_variation_case`
  - `table_adjacent_note_object_variation_case`
  - `appendix_variation_case`
  - `english_appendix_variation_case`
  - `bilingual_abstract_case`
  - `declaration_variation_case`
  - `appendix_contents_variation_case`
  - `appendix_figure_list_variation_case`
  - `caption_variation_case`
  - `equation_caption_variation_case`
  - `annotation_block_variation_case`
  - `footer_footnote_noise_variation_case`
  - `running_header_footer_metadata_case`
  - `running_english_header_footer_case`
  - `repeated_section_header_noise_case`
  - `repeated_parent_section_header_noise_case`
  - `repeated_subsection_header_noise_case`
  - `abbreviated_section_header_noise_case`
  - `unnumbered_abbreviated_section_header_noise_case`
  - `contents_field_code_variation_case`
  - `keyword_variation_case`
  - `metadata_block_variation_case`
  - `author_info_variation_case`
  - `department_info_variation_case`
  - `front_matter_combo_variation_case`
  - `front_matter_spacing_variation_case`
  - `front_matter_multiline_variation_case`
  - `front_matter_table_variation_case`
  - `docx_table_front_matter_case`
  - `complex_table_front_matter_case`
- benchmark markdown comparison 已支持显示各变体的 `Expectation override cases`
- `scripts/run_benchmark.py` 已支持注入 reviewer builder 与 case loader，便于在本地测试中运行受控 fake-model benchmark，而不影响默认 CLI / API 链路
- 已补第一条 fake-model `model_only` 独立语义验收用例，用于验证模型版 expectation 可以与规则版基线真正分离
- 已为 `topic_precision_case`、`logic_precision_case`、`literature_precision_case`、`novelty_precision_case` 与 `writing_precision_case` 补上第一组真实 fixture 级 `model_only` 独立 expectation，并通过 fake-model benchmark 验证模型版 issue title 可以与规则版基线不同

当前限制：

- 当前双轨 benchmark 虽然已实现 `evaluation_fixture` 全量 model override 覆盖，并已有覆盖五个固定维度的 fake-model 独立语义样本，但大部分模型版 expectation 仍与规则版基线保持一致
- 当前 comparison 虽然已有最小 token / retry / error category 统计，但成本估算仍依赖手工传入单价，尚未接入模型价格注册表和按模型版本拆分的长期趋势记录
- 当前 `debate_resolution_traces` 已能关联 worker 级模型元数据，但还没有细化到 prompt 模板版本、judge 层证据裁剪原因和多轮 debate 链路
- 当前 `debate_resolution_traces` 已补到 judge 层裁剪原因，但还没有细化到 prompt 模板版本、judge 证据引用片段和多轮 debate 链路
- 当前模型版 benchmark 主要用于稳定性回归和 fallback 验证，还没有引入真实在线模型作为固定验收基线

## 4. 测试与验证

截至 `2026-03-23`，当前已通过：

- debug API 集成测试
- PDF 导出单元测试
- PDF 导出 API 集成测试
- 扩展 debug trace 的集成测试
- benchmark 逻辑单元测试
- benchmark runner 集成测试
- benchmark comparison / 多变体脚本集成测试
- benchmark 非法 LLM 配置边界测试
- benchmark LLM runtime 观测汇总单元测试
- benchmark pricing 参数与成本渲染测试
- benchmark variant-specific expectation 解析测试
- benchmark variant expectation 覆盖计数集成测试
- fake-model `model_only` 独立语义 benchmark 集成测试
- 覆盖五个固定维度的 fake-model `model_only` 语义 benchmark 集成测试
- issue title 级 benchmark 单元测试
- benchmark dataset / markdown renderer 单元测试
- benchmark threshold gate 单元测试
- selective debate 单元测试
- schema 单元测试
- disagreement detection 单元测试
- `docx parser` 单元测试
- 模板差异 parser 单元测试
- 双语摘要 / 声明页模板差异 parser 单元测试
- 复合前置区 / 多附录组合模板 parser 单元测试
- 空格对齐前置区模板 parser 单元测试
- 跨行前置区字段模板 parser 单元测试
- 附录目录页模板 parser 单元测试
- 表格化前置区字段模板 parser 单元测试
- 附录图表目录页模板 parser 单元测试
- docx 表格前置区模板 parser 单元测试
- 合并单元格 / 嵌套表格前置区模板 parser 单元测试
- 目录字段代码残留模板 parser 单元测试
- 封面页表格块标题选择模板 parser 单元测试
- 尾部致谢 / 成果页模板 parser 单元测试
- 参考文献后作者简介页模板 parser 单元测试
- 目录页页眉 / 页脚噪声模板 parser 单元测试
- 图表标题模板 parser 单元测试
- 公式说明块模板 parser 单元测试
- 注释性说明块模板 parser 单元测试
- 页码与脚注残留噪声模板 parser 单元测试
- 运行中页眉页脚元数据残留模板 parser 单元测试
- 运行中英文页眉页脚元数据残留模板 parser 单元测试
- 运行中英文摘要页眉残留模板 parser 单元测试
- 运行中重复章节标题残留模板 parser 单元测试
- 运行中脚注正文块残留模板 parser 单元测试
- 运行中上级章节标题残留模板 parser 单元测试
- 运行中子章节标题残留模板 parser 单元测试
- 运行中缩写章节标题残留模板 parser 单元测试
- 运行中无编号缩写章节标题残留模板 parser 单元测试
- 真实 docx 脚注对象残留模板 parser 单元测试
- 真实 docx 尾注对象残留模板 parser 单元测试
- 脚注尾注混排边界模板 parser 单元测试
- 跨行脚注尾注对象模板 parser 单元测试
- 表格邻接注释对象模板 parser 单元测试
- `SkillLoader` 单元测试
- `LLMClient` 单元测试
- `LLMClient` schema 指令预算保护单元测试
- `OpenAICompatibleProvider` 单元测试
- `DeepSeek` Ark `chat/completions` 路由与 usage 兼容单元测试
- `reviewer_factory` structured output 默认策略单元测试
- `TopicScopeAgent` 模型版 / fallback 单元测试
- `TopicScopeAgent` 在线模型 prompt 压缩单元测试
- `LogicChainAgent` 模型版 / fallback 单元测试
- `LogicChainAgent` 在线模型 prompt 压缩单元测试
- `LiteratureSupportAgent` 模型版 / fallback 单元测试
- `LiteratureSupportAgent` 在线模型 prompt 压缩单元测试
- `NoveltyDepthAgent` 模型版 / fallback 单元测试
- `NoveltyDepthAgent` 在线模型 prompt 压缩单元测试
- `WritingFormatAgent` 模型版 / fallback 单元测试
- `WritingFormatAgent` 在线模型 prompt 压缩单元测试
- reporting 单元测试
- 扩展样本下的五维端到端集成测试
- 模型版 `TopicScopeAgent` 接入 `ChiefReviewer` 的最小集成测试
- 模型版 `LogicChainAgent` 接入 `ChiefReviewer` 的最小集成测试
- 模型版 `LiteratureSupportAgent` 接入 `ChiefReviewer` 的最小集成测试
- 模型版 `NoveltyDepthAgent` 接入 `ChiefReviewer` 的最小集成测试
- 模型版 `WritingFormatAgent` 接入 `ChiefReviewer` 的最小集成测试
- live LLM smoke harness 集成测试
- API request-scoped `llm` 配置集成测试
- API request-scoped `llm` 私网 base URL 安全约束测试
- API `model_only` provider 异常脱敏测试
- debug trace 模型 fallback 元数据集成测试
- orchestrator 并发 worker batch 与 checkpoint 顺序稳定性单元测试
- orchestrator `ReviewRun` 生命周期与 worker 状态单元测试
- async review run API 集成测试
- review run event log API 集成测试
- review run not found API 边界测试
- review run 文件快照恢复 API 集成测试
- review run 跨 app 实例 snapshot 回读 API 集成测试
- review run TTL 清理与快照回收 API 集成测试
- review run ownership 可见性 API 集成测试
- review run lease 续租 API 集成测试
- review run active foreign lease claim 冲突 API 集成测试
- review run stale foreign lease claim API 集成测试
- review run stale claim 自动 resume API 集成测试
- review run stale claim 后旧 owner 本地 cooperative cancel API 集成测试
- review run ownership epoch fencing API/单元测试
  - 新 owner 先完成后，旧 baseline 分支晚写不能覆盖终态
  - 更晚 claim 的新 owner 完成后，旧 resumed 分支晚写不能覆盖终态
- review run request-scoped key claim 不自动 resume 边界测试
- review run terminal claim 边界测试
- review run SSE 事件流 API 集成测试
- review run SSE `Last-Event-ID` 续传 API 集成测试
- review run SSE heartbeat API 集成测试
- review run SSE invalid `Last-Event-ID` 边界测试
- review run SSE invalid heartbeat interval 边界测试
- review run SSE unknown-run API 边界测试
- 豆包 Ark 最小真实 `responses` 连通性验证
- 豆包 Ark 完整 smoke 尝试：
  - `model_with_fallback --timeout 5 --max-retries 0` -> 5/5 worker `provider_network`
  - `model_with_fallback --timeout 15 --max-retries 0 --prompt-char-budget 2500` -> 1 个 `structured_output`，4 个 `provider_network`
  - `model_with_fallback --worker-id TopicScopeAgent --timeout 15 --max-retries 0 --prompt-char-budget 2500` -> `provider_network`
  - `model_with_fallback --worker-id TopicScopeAgent --timeout 30 --max-retries 0 --prompt-char-budget 2500` -> `parsed=true`
  - `model_with_fallback --worker-id TopicScopeAgent --model-name doubao-seed-2-0-code-preview-260215 --timeout 30 --max-retries 0 --prompt-char-budget 2500` -> 连续两次 `structured_output`
  - `model_with_fallback --worker-id TopicScopeAgent --model-name doubao-seed-2-0-pro-260215 --timeout 30 --max-retries 0 --prompt-char-budget 2500` -> 连续两次 `provider_runtime`
  - `model_with_fallback --worker-id TopicScopeAgent --model-name deepseek-r1-250528 --timeout 30 --max-retries 0 --prompt-char-budget 2500` -> 连续两次 `structured_output`

当前基线结果：

- `pytest` 通过，当前为 `217 passed`
- `scripts/run_benchmark.py --format markdown` 当前在 51 个评测样本上输出：
  - `fully_passed_cases = 51/51`
  - `high_severity_dimension_recall = 1.0`
  - `priority_first_dimension_accuracy = 1.0`
  - `debate_dimension_recall = 1.0`
  - `issue_title_recall = 1.0`
  - `issue_title_false_positive_rate = 0.0`
  - `elapsed_seconds = 6.26`
  - `average_case_duration_ms = 122.73`
  - 支持 `--format markdown` 输出阶段性复盘摘要
  - 支持以阈值形式作为回归门槛运行
- `scripts/run_benchmark.py --format markdown --variant rule --variant model_with_fallback` 已可输出双轨 comparison 摘要
  - `model_with_fallback` 当前 `Expectation override cases = 51`
  - 双变体 smoke 下 `rule` 与 `model_with_fallback` 仍均为 `51/51`

## 5. 下一步计划

按当前顺序继续推进：

1. 继续完善 SSE 事件流：补更明确的客户端消费约定和反向代理超时矩阵验证
2. 继续完善 run registry 生命周期治理：补接管后真正终止旧 owner 外部副作用、快照冲突恢复和更明确的失败恢复语义
3. 将 debug trace 和 run 查询结果进一步对齐到节点级 partial result、failure/fallback 观测和耗时统计
4. 在并发 orchestrator 基线上重新评估真实在线 provider 的整链时延瓶颈，确认问题是模型慢、provider 抖动，还是聚合前等待策略仍然保守
5. 在并发主链稳定后，再继续扩展模型版 benchmark 观测、BYOK 托管策略和更细粒度限流

## 6. 当前风险

主要风险：

- parser 对真实论文模板差异的适配还不够强
- 当前虽然双轨 benchmark 入口和 variant-specific expectation 基础设施已打通，但 expectation 内容仍主要围绕规则版基线组织
- skill loader 现在只够支撑 MVP，不够支撑完整治理流程
- disagreement detection 目前仍是启发式候选机制，不代表最终 debate 效果
- 当前 selective debate 仍是最小复核版，不代表最终多 reviewer 裁决效果
- ledger 与 trace 已具备最小模型元数据、retry/token、error category 和 debate resolution 级追踪，但还没有细化到 prompt 模板版本、judge 证据引用片段、provider 原始响应体归档和多轮调用链路
- request-scoped BYOK 目前仍是直传密钥模式，适合开发与联调，不适合直接作为生产态密钥托管方案
- 当前结构化输出的预算控制仍是字符级近似，不代表真实 token 成本

控制方式：

- 优先把 provider 抽象、fake provider、结构化输出和 fallback 路径打稳，再逐维接模型
- 模型接入阶段继续保留规则版作为 baseline，不直接替换现有规则链
- 在进入更强 debate 与 ledger 扩展前，先稳定单维模型 worker 的输出质量与双轨 benchmark 观测能力

## 7. 维护规则

后续每次有实质性开发推进时，本文件应至少更新以下内容之一：

- 当前状态
- 已完成事项
- 测试与验证
- 下一步计划
