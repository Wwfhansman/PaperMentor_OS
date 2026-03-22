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
- reporting 单元测试
- 扩展样本下的五维端到端集成测试

当前基线结果：

- `pytest` 通过，当前为 `126 passed`
- `scripts/run_benchmark.py --format markdown` 当前在 51 个评测样本上输出：
  - `fully_passed_cases = 51/51`
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
3. 在五个维度都具备精度样本后，继续补“真实论文模板差异”与“跨模板误报”样本，并逐步扩展到更复杂的前置区 / 目录 / 附录混排模板
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
