from __future__ import annotations

from dataclasses import dataclass

from papermentor_os.schemas.types import Dimension


@dataclass(frozen=True)
class ParagraphSpec:
    text: str
    footnote: str | tuple[str, ...] | None = None
    endnote: str | tuple[str, ...] | None = None


@dataclass(frozen=True)
class SectionSpec:
    heading: str
    paragraphs: tuple[str | ParagraphSpec, ...]
    tables: tuple[TableSpec | tuple[tuple[str, ...], ...], ...] = ()


@dataclass(frozen=True)
class TableCellSpec:
    text: str = ""
    nested_table_rows: tuple[tuple[str, ...], ...] = ()
    footnote: str | tuple[str, ...] | None = None
    endnote: str | tuple[str, ...] | None = None


@dataclass(frozen=True)
class TableSpec:
    rows: tuple[tuple[TableCellSpec | str, ...], ...]
    merges: tuple[tuple[int, int, int, int], ...] = ()


@dataclass(frozen=True)
class ReviewCaseSpec:
    case_id: str
    tags: tuple[str, ...]
    title: str
    abstract: str
    sections: tuple[SectionSpec, ...]
    references: tuple[str, ...]
    expected_dimensions: tuple[Dimension, ...]
    front_matter: tuple[str, ...] = ()
    front_matter_tables: tuple[TableSpec | tuple[tuple[str, ...], ...], ...] = ()
    post_abstract_front_matter: tuple[str, ...] = ()
    post_abstract_front_matter_tables: tuple[TableSpec | tuple[tuple[str, ...], ...], ...] = ()
    post_reference_back_matter_sections: tuple[SectionSpec, ...] = ()
    title_style: str | None = None
    abstract_heading: str = "摘要"
    reference_heading: str = "参考文献"
    heading_style: str = "Heading 1"
    expected_debate_dimensions: tuple[Dimension, ...] = ()
    expected_high_severity_dimensions: tuple[Dimension, ...] = ()
    expected_priority_first_dimension: Dimension | None = None
    expected_issue_titles: tuple[str, ...] = ()


MINIMAL_REVIEW_CASE = ReviewCaseSpec(
    case_id="minimal_review_case",
    tags=("baseline", "five_dimension", "research_first"),
    title="某系统设计与实现研究",
    abstract="本文提出一套论文评审辅助系统，目标是提升初审效率，但当前仅完成基础系统实现。",
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=("本课题来源于教学场景，目标是提升论文初审效率。",),
        ),
        SectionSpec(
            heading="2 系统设计",
            paragraphs=("系统采用前后端分离设计，并显著提升了处理效率。",),
        ),
        SectionSpec(
            heading="3 相关工作",
            paragraphs=("现有研究多关注通用写作辅助，而较少提供结构化评审流程。",),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=("当前只进行了初步功能验证，尚未与基线方法做系统对比。",),
        ),
    ),
    references=("[1] Zhang. Research on Academic Writing Support. 2023.",),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


STRONG_REVIEW_CASE = ReviewCaseSpec(
    case_id="strong_review_case",
    tags=("strong_sample", "evaluation_fixture", "five_dimension"),
    title="多智能体评审框架",
    abstract=(
        "多智能体评审框架。"
        "该框架聚焦导师初审中的问题定位效率问题。"
        "本文提出一套围绕选题、论证、文献、创新和写作五个维度的评审框架，"
        "并结合 evidence ledger 与 selective debate 机制组织分析流程。"
        "实验评估基于三组计算机专业论文草稿，结果表明该框架能够更稳定地识别高优先级问题。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "本科毕业论文初审效率不足是当前教学场景中的现实问题，因此本文明确提出需要构建一套结构化评审框架。[1]",
                "本文的目标是让评审者能够围绕固定维度快速定位问题，并减少只看功能实现描述而忽略研究问题的情况。[2]",
            ),
        ),
        SectionSpec(
            heading="2 相关工作",
            paragraphs=(
                "现有研究已讨论写作辅助、评分系统和评审流程自动化，但不同方法在证据绑定和基线对比方面仍存在差异。[1][3]",
                "本文在对比 baseline 系统后，进一步说明多维 rubric 和证据锚点如何改善导师初审中的可解释性。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文提出的框架包含 ChiefReviewer、五个专项 worker 与 debate judge，并通过 evidence ledger 串联结论与原文证据。[2][4]",
                "框架的创新点在于把固定维度评审、证据约束与 selective debate 组合起来，从而在保持稳定流程的同时提升问题发现质量。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估采用三类论文草稿和人工标注结果进行对比，指标包括高严重度问题召回率、误报率与建议可操作性。[3][5]",
                "结果分析显示，该框架在高优先级问题识别上优于单一 prompt baseline，并且在重复运行时保持更稳定的评估效果。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与展望",
            paragraphs=(
                "结论部分回收研究问题、方法与结果，说明多智能体评审框架能够支持本科论文初审中的结构化分析。",
                "本文也讨论了局限性，例如样本规模仍有限，后续工作将继续扩展真实论文模板、误差分析与更多对比实验。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


TOPIC_PRECISION_CASE = ReviewCaseSpec(
    case_id="topic_precision_case",
    tags=("precision_sample", "evaluation_fixture", "topic_precision"),
    title="面向本科论文初审的多智能体评审系统设计与实现",
    abstract=(
        "面向本科论文初审的多智能体评审系统设计与实现聚焦导师早期反馈效率不足的问题。"
        "本文提出一套结合五维 rubric、evidence ledger 与 selective debate 的评审系统框架，"
        "用于提升计算机专业本科毕业论文草稿的结构化诊断能力。"
        "实验评估表明，该系统在高优先级问题识别与稳定性方面优于基线方案，并在结论部分讨论了当前局限。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对本科论文初审反馈滞后的问题，本文提出一套多智能体评审系统，以支持导师在草稿阶段快速定位研究问题。[1]",
                "本文的研究目标是提高高优先级问题识别效率，并验证系统化评审流程是否优于单一 prompt 方案。[2]",
            ),
        ),
        SectionSpec(
            heading="2 相关工作",
            paragraphs=(
                "现有研究主要关注写作辅助、自动评分和教育场景中的反馈系统，但对证据约束和选择性复核讨论不足。[1][3]",
                "本文在相关工作中对比 baseline、benchmark 与已有结构化反馈方案，以明确系统定位和差异。[4]",
            ),
        ),
        SectionSpec(
            heading="3 系统设计",
            paragraphs=(
                "本文设计的多智能体评审系统由 ChiefReviewer、五个维度 worker、evidence ledger 和 debate judge 构成。[2][4]",
                "系统的创新点在于将维度评审、证据锚点和 selective debate 结合，从而更稳定地处理边界型判断。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取四组计算机专业本科毕业论文草稿，并围绕高严重度问题召回率、误报率和 actionability 做对比实验。[3][5]",
                "结果分析显示，该系统在问题识别和复核稳定性方面均优于 baseline，并给出误差分析和适用边界讨论。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、系统方法与实验结果，说明多智能体评审系统对论文初审具有现实价值。",
                "本文也讨论了当前系统的局限性，包括真实论文模板覆盖仍有限，后续工作将继续扩展样本与对照实验。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


LOGIC_PRECISION_CASE = ReviewCaseSpec(
    case_id="logic_precision_case",
    tags=("precision_sample", "evaluation_fixture", "logic_precision"),
    title="面向本科论文初审的论证链审查框架设计",
    abstract=(
        "面向本科论文初审的论证链审查框架设计聚焦毕业论文草稿中验证链条不完整的问题。"
        "本文提出一套结合章节结构分析、claim-evidence 对齐和 debate 复核的审查框架，"
        "并通过实验评估检验其在高严重度问题识别上的稳定性。"
        "结果表明该框架能够提升论证缺口定位效率，并在讨论与展望部分总结了当前局限。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对本科论文草稿中论证链常出现断裂的问题，本文提出一套论证链审查框架，用于帮助导师初审快速识别验证缺口。[1]",
                "本文的目标是分析 claim 与 evidence 的对应关系，并验证该框架能否提高高优先级问题定位效率。[2]",
            ),
        ),
        SectionSpec(
            heading="2 相关工作",
            paragraphs=(
                "现有研究关注自动评分、写作辅助和教育反馈系统，但较少显式分析论证闭环与证据链完整性。[1][3]",
                "本文对比已有 benchmark 和 baseline 方案，说明本框架在论证结构审查上的定位。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "该框架围绕研究问题、关键论断、实验设计和结果解释构建审查流程，并结合 evidence ledger 记录证据锚点。[2][4]",
                "框架的核心方法是识别 claim 与 evidence 的失配点，并对边界样本触发 selective debate 复核。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估基于四组计算机专业本科论文草稿，指标包括高严重度问题召回率、误报率和 actionability。[3][5]",
                "结果分析显示，该框架在论证缺口识别上优于 baseline，并能通过实验结果和人工标注进行双重验证。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 讨论与展望",
            paragraphs=(
                "综上所述，本文框架能够回收研究问题、方法与实验结果，并说明当前方案对导师初审具有现实意义。",
                "本章也讨论了局限性和后续工作，包括真实论文模板覆盖仍有限、更多对比实验仍需补充。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


LITERATURE_PRECISION_CASE = ReviewCaseSpec(
    case_id="literature_precision_case",
    tags=("precision_sample", "evaluation_fixture", "literature_precision"),
    title="面向本科论文初审的文献支撑分析框架",
    abstract=(
        "面向本科论文初审的文献支撑分析框架聚焦毕业论文草稿中相关工作定位不清和比较分析不足的问题。"
        "本文提出一套结合已有方法比较、正文引用检查和基线对照分析的评审框架，"
        "并在实验评估中验证该框架对高严重度文献问题的识别能力。"
        "结果表明该框架能够提升文献缺口定位效率，并在结尾讨论了当前局限。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对本科毕业论文草稿中相关工作定位不清的问题，本文提出一套文献支撑分析框架，以帮助导师初审快速识别文献缺口。[1]",
                "本文的研究目标是分析参考文献覆盖度、正文引用链路和已有方法比较是否充分。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "已有方法主要包括通用写作辅助、自动评分和结构化反馈系统，但不同方法在证据约束和反馈粒度方面存在明显差异。[1][3]",
                "本文将当前框架与 baseline、benchmark 方案和已有结构化反馈系统进行比较，以明确系统定位和适用边界。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "该框架结合参考文献数量、正文引用分布和方法比较段落，分析论文是否完成了必要的文献支撑闭环。[2][4]",
                "方法设计同时要求在实验分析中说明对比对象、局限和与已有方案的差异点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取四组计算机专业本科毕业论文草稿，指标包括高严重度文献问题召回率、误报率和 actionability。[3][5]",
                "结果分析显示，该框架在文献缺口识别和已有方法比较方面优于 baseline，并通过 benchmark 结果验证稳定性。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明该框架能够支持本科论文初审中的文献支撑分析。",
                "本章也讨论了局限性，包括真实论文模板覆盖和跨学校规范差异仍需进一步扩展。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


NOVELTY_PRECISION_CASE = ReviewCaseSpec(
    case_id="novelty_precision_case",
    tags=("precision_sample", "evaluation_fixture", "novelty_precision"),
    title="面向本科论文初审的多维证据约束评审框架",
    abstract=(
        "面向本科论文初审的多维证据约束评审框架聚焦毕业论文草稿中高优先级问题定位不稳定的现实问题。"
        "本文围绕固定维度评审、evidence ledger 与 selective debate 构建一套分析框架，"
        "并通过实验评估检验该框架在高严重度问题识别和重复运行稳定性上的表现。"
        "结果显示，该框架相较单一 prompt 方案在问题定位效率和一致性方面更稳定，并在结尾讨论了当前局限。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对本科毕业论文草稿初审中高优先级问题定位不稳定的情况，本文围绕证据约束和维度化评审构建一套分析框架。[1]",
                "研究目标是检验该框架是否能够在保持结构化输出的同时，提高问题识别的一致性和可解释性。[2]",
            ),
        ),
        SectionSpec(
            heading="2 相关工作",
            paragraphs=(
                "现有研究主要关注写作辅助、自动评分和教育反馈系统，但对证据约束与边界样本复核的组合讨论仍不充分。[1][3]",
                "本文将该框架与 baseline、benchmark 和已有结构化反馈系统进行比较，以明确其定位与适用边界。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "该框架围绕固定评审维度、evidence ledger 和 debate 复核设计分析流程，用于定位研究问题、论证缺口和文献支撑不足等风险。[2][4]",
                "相较通用写作辅助方案，该框架更强调证据约束、优先级排序和边界样本复核，从而减少高严重度问题识别的不稳定性。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取四组计算机专业本科毕业论文草稿，指标包括高严重度问题召回率、误报率和 actionability。[3][5]",
                "结果分析显示，该框架在高优先级问题定位和重复运行稳定性方面优于 baseline，并通过人工标注验证了差异来源。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明多维证据约束评审框架在本科论文初审中具有现实价值。",
                "本章也讨论了局限性，包括真实论文模板覆盖与跨学校规范差异仍需后续扩展。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


WRITING_PRECISION_CASE = ReviewCaseSpec(
    case_id="writing_precision_case",
    tags=("precision_sample", "evaluation_fixture", "writing_precision"),
    title="面向本科论文初审的结构化评审框架",
    abstract=(
        "本文针对本科论文初审效率不足的问题，构建结构化评审框架，"
        "结合多维分析与实验评估验证其稳定性，并总结局限。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对本科毕业论文草稿初审反馈滞后的问题，本文围绕结构化评审框架展开分析，并明确研究目标与评价范围。[1]",
                "研究目标是提高高优先级问题识别效率，并验证框架在重复运行下的稳定性。[2]",
            ),
        ),
        SectionSpec(
            heading="2 相关工作",
            paragraphs=(
                "现有研究主要关注写作辅助、自动评分和结构化反馈系统，但在证据约束和维度化评审方面仍存在差异。[1][3]",
                "本文通过 baseline 和 benchmark 对比，说明当前框架与已有方案的关系和适用边界。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "该框架围绕选题、论证、文献、创新和写作五个维度组织评审流程，并借助 evidence ledger 绑定结论与证据。[2][4]",
                "框架还通过 selective debate 处理边界样本，以减少主观维度上的判断不稳定性。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取四组计算机专业本科毕业论文草稿，指标包括高严重度问题召回率、误报率和 actionability。[3][5]",
                "结果分析显示，该框架在高优先级问题定位方面优于 baseline，并能通过人工标注进行稳定性验证。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法与实验结果，说明该框架适合用于本科论文初审。",
                "本章也说明了局限性，包括真实论文模板覆盖仍有限，后续工作将继续扩展样本与评测范围。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


TEMPLATE_VARIATION_CASE = ReviewCaseSpec(
    case_id="template_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的结构化评审模板适配分析",
    abstract="本文围绕本科论文草稿的模板差异适配问题，分析解析稳定性，并通过实验验证规则对不同章节命名方式的兼容性。",
    abstract_heading="摘 要",
    reference_heading="参考 文献",
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对不同院校论文模板中标题写法差异较大的问题，本文分析 docx 解析链路的稳定性与适配边界。[1]",
                "研究目标是让系统在不同章节命名方式下仍能稳定识别摘要、正文和参考文献。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有研究与系统实现方案在标题命名、引用风格和章节组织方式上存在明显差异，需通过规则增强兼容性。[1][3]",
                "本文将当前解析方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过标题标准化、章节识别与证据锚点约束，提升多种论文模板下的解析稳定性。[2][4]",
                "实验分析同时关注误分段、误识别和正文引用保留等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取四种学校模板和多篇计算机专业本科毕业论文草稿，指标包括解析成功率和结构一致性。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地处理模板差异，并减少结构识别误差。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明模板差异适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括复杂表格、图片和脚注仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


COVER_PAGE_VARIATION_CASE = ReviewCaseSpec(
    case_id="cover_page_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    front_matter=(
        "某某大学本科毕业论文",
        "计算机科学与技术专业",
        "指导教师：张老师",
    ),
    title="面向本科论文初审的结构化评审模板适配分析",
    title_style="Title",
    abstract="本文围绕本科论文草稿的模板差异适配问题，分析解析稳定性，并通过实验验证规则对不同封面与标题布局方式的兼容性。",
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文文档中封面信息和题名布局差异较大的情况，本文分析解析链路在标题识别上的稳定性与适配边界。[1]",
                "研究目标是让系统在标题前存在院校和专业信息时，仍能稳定定位真实论文标题与摘要区域。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案在结构化解析上通常默认首段即标题，但真实学校模板往往包含封面和指导教师信息，需要更稳健的标题定位策略。[1][3]",
                "本文将当前方案与 baseline、benchmark 文档样式进行比较，以验证标题定位策略的适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过前置区标题候选筛选、标题样式识别和证据锚点约束，提升多种封面模板下的解析稳定性。[2][4]",
                "实验分析同时关注标题误识别、摘要错位和章节切分偏差等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取多种学校封面模板和计算机专业本科毕业论文草稿，指标包括标题定位准确率和结构一致性。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地处理封面差异，并减少标题定位误差。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明封面差异适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括复杂目录页和多语言模板仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


COVER_PAGE_TABLE_VARIATION_CASE = ReviewCaseSpec(
    case_id="cover_page_table_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    front_matter_tables=(
        (
            ("某某大学本科毕业论文",),
            ("学院", "计算机科学与技术学院"),
            ("专业", "软件工程"),
            ("指导教师", "张老师"),
            ("学号", "2020123456"),
        ),
    ),
    title="面向本科论文初审的封面表格模板适配分析",
    abstract=(
        "本文围绕本科论文草稿的封面表格模板适配问题，分析解析链路在表格化封面前置区存在时的标题识别稳定性，"
        "并通过实验验证标题候选筛选策略对真实学校模板的兼容性。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文文档中封面信息常以表格布局出现的情况，本文分析解析链路在标题识别上的稳定性与适配边界。[1]",
                "研究目标是让系统在标题前存在学校、专业、导师和学号表格块时，仍能稳定定位真实论文标题与摘要区域。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案在结构化解析上通常默认首段即标题，但真实学校模板往往先出现封面表格块，需要更稳健的标题定位策略。[1][3]",
                "本文将当前方案与 baseline、benchmark 文档样式进行比较，以验证标题定位策略的适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过表格前置区候选筛选、标题语义特征识别和证据锚点约束，提升多种封面模板下的解析稳定性。[2][4]",
                "实验分析同时关注标题误识别、摘要错位和章节切分偏差等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取多种学校封面表格模板和计算机专业本科毕业论文草稿，指标包括标题定位准确率和结构一致性。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地处理封面表格差异，并减少标题定位误差。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明封面表格适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的合并单元格封面模板仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


BACK_MATTER_VARIATION_CASE = ReviewCaseSpec(
    case_id="back_matter_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的尾部致谢与成果页模板适配分析",
    abstract=(
        "本文围绕本科毕业论文尾部致谢与成果页模板适配分析问题，分析解析链路对致谢页、成果页和参考文献边界识别的影响，"
        "并通过实验验证尾部 back matter 隔离策略相较直接拼接规则的结构稳定优势。"
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中参考文献前常出现致谢页和成果页的情况，本文分析其对主正文识别和评审稳定性的影响。[1]",
                "研究目标是让系统在尾部致谢页与成果页并存时仍能稳定保留主正文结构，并避免尾部说明性内容误入五维评审正文。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只处理目录页和附录边界，而对参考文献前的致谢页、成果页支持不足。[1][3]",
                "本文将当前尾部隔离方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过尾部标题识别、说明性页面隔离和参考文献起点控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注致谢误入正文、成果列表干扰和参考文献边界漂移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含尾部致谢页和成果页的多种学校模板，指标包括主正文识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过尾部 back matter，并减少说明性内容对正文评审的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明尾部致谢与成果页适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的作者简介和英文成果页仍需后续扩展支持。",
            ),
        ),
        SectionSpec(
            heading="致谢",
            paragraphs=(
                "感谢指导教师、实验室同学和参与调研的同学在论文撰写过程中的帮助。",
                "致谢内容不应进入主正文五维评审结论。",
            ),
        ),
        SectionSpec(
            heading="攻读学位期间取得的成果",
            paragraphs=(
                "[1] 已投稿论文一篇。",
                "[2] 参与校级创新项目一项。",
            ),
        ),
        SectionSpec(
            heading="Acknowledgements",
            paragraphs=(
                "The author thanks the advisor and peers for support during the thesis preparation process.",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


POST_REFERENCE_BIO_VARIATION_CASE = ReviewCaseSpec(
    case_id="post_reference_bio_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的参考文献后作者简介页模板适配分析",
    abstract=(
        "本文围绕本科毕业论文参考文献后作者简介页模板适配分析问题，分析解析链路对参考文献边界和作者简介页隔离的影响，"
        "并通过实验验证 post-reference back matter 隔离策略相较直接读到文件末尾规则的结构稳定优势。"
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中参考文献后常附带作者简介页的情况，本文分析其对参考文献边界识别和评审稳定性的影响。[1]",
                "研究目标是让系统在作者简介页出现在参考文献后时，仍能稳定保留主正文结构和真实参考文献列表。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常默认参考文献读到文件结束，而对作者简介页和个人简历页支持不足。[1][3]",
                "本文将当前隔离方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过 post-reference 标题识别、作者简介页隔离和参考文献终止控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注作者简介误入参考文献、参考文献数量漂移和后记页干扰等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含作者简介页的多种学校模板，指标包括参考文献识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地在作者简介页出现时终止参考文献提取，并减少尾部噪声对正文评审的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明参考文献后作者简介页适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的英文简历页和作者照片块仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    post_reference_back_matter_sections=(
        SectionSpec(
            heading="作者简介",
            paragraphs=(
                "作者为某某大学软件工程专业本科生，研究方向为教育场景下的论文评审辅助系统。",
                "作者简介内容不应进入参考文献列表。",
            ),
        ),
        SectionSpec(
            heading="Author Biography",
            paragraphs=(
                "The author is an undergraduate student focusing on structured thesis review systems.",
            ),
        ),
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


CONTENTS_VARIATION_CASE = ReviewCaseSpec(
    case_id="contents_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的目录页模板适配分析",
    abstract="本文围绕目录页与章节标题共存的论文模板差异，分析解析链路对正文识别和结构稳定性的影响，并通过实验验证适配效果。",
    post_abstract_front_matter=(
        "目录",
        "第一章 绪论................................1",
        "第二章 已有方法比较..........................5",
        "第三章 方法设计..............................9",
        "第四章 实验评估............................13",
        "第五章 结论与局限..........................17",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对论文模板中目录页常被误识别为正文章节的问题，本文分析目录页对结构化解析与评审稳定性的影响。[1]",
                "研究目标是让系统在保留真实章节结构的同时，忽略目录页中的伪章节和页码信息。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案在解析阶段常直接将目录项视作正文章节，导致正文切分和后续 finding 锚点出现偏差。[1][3]",
                "本文将当前适配方案与 baseline、benchmark 文档样式进行比较，以验证目录页过滤策略的有效性。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过目录标题识别、目录项模式过滤和章节重建，提升真实论文模板下的正文识别稳定性。[2][4]",
                "实验分析同时关注目录误分段、章节重复和页码残留等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取含目录页的多种学校模板，指标包括正文章节识别准确率、误分段率和结构一致性。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过目录页，并保留真实章节内容。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明目录页适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括自动生成目录中的复杂制表符和多语言目录仍需后续支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


COMPLEX_CONTENTS_VARIATION_CASE = ReviewCaseSpec(
    case_id="complex_contents_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的复杂目录页模板适配分析",
    abstract=(
        "本文围绕本科毕业论文复杂目录页模板适配分析问题，分析解析链路对多级目录、无空格编号目录项和制表符页码布局的处理稳定性，"
        "并通过实验验证复杂目录过滤策略相较简单规则的结构保真优势。"
    ),
    post_abstract_front_matter=(
        "Contents",
        "1 Introduction\t1",
        "1.1Research Background\t2",
        "1.2 Research Goal\t3",
        "2 Method Design\t5",
        "3 Evaluation\t9",
        "4 Conclusion\t13",
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文模板中常见的多级目录和无空格编号目录项，本文分析复杂目录页对正文章节识别和评审稳定性的影响。[1]",
                "研究目标是让系统在复杂目录布局下仍能稳定跳过目录噪声，并保留真实章节结构与摘要边界。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖简单目录格式，而复杂目录中的多级编号、制表符页码和英文章节名更容易污染正文切分。[1][3]",
                "本文将当前复杂目录过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过复杂目录标题识别、目录项模式扩展和正文起点控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注目录误入正文、章节重复和页码噪声残留等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含复杂目录布局的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过复杂目录页，并减少多级目录对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明复杂目录页适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括自动生成目录中的超链接字段和更复杂附录目录仍需后续支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


CONTENTS_HEADER_FOOTER_VARIATION_CASE = ReviewCaseSpec(
    case_id="contents_header_footer_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的目录页页眉页脚模板适配分析",
    abstract=(
        "本文围绕本科毕业论文目录页页眉页脚模板适配分析问题，分析解析链路对学校名、论文类型和孤立页码等目录页残留噪声的处理稳定性，"
        "并通过实验验证目录页页眉页脚过滤策略相较仅按目录项识别规则的结构保真优势。"
    ),
    post_abstract_front_matter=(
        "Contents",
        "某某大学本科毕业论文",
        "- 1 -",
        "第一章 绪论................................1",
        "第二章 已有方法比较..........................5",
        "第三章 方法设计..............................9",
        "第四章 实验评估............................13",
        "第五章 结论与局限..........................17",
        "本科毕业论文",
        "2",
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对目录页中常见的学校名、论文类型和页码残留噪声，本文分析其对正文章节识别和评审稳定性的影响。[1]",
                "研究目标是让系统在目录页夹带页眉页脚噪声时仍能稳定跳过目录内容，并保留真实章节结构与摘要边界。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖目录项本身，而对学校名、页码和论文类型等目录页残留噪声支持不足。[1][3]",
                "本文将当前目录页页眉页脚过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过目录模式状态控制、目录项识别和非章节噪声过滤，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注页眉页脚误入正文、章节重复和正文起点漂移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含目录页页眉页脚残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过目录页页眉页脚噪声，并减少学校模板残留对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明目录页页眉页脚适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的页眉字段代码和目录分栏布局仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


CAPTION_VARIATION_CASE = ReviewCaseSpec(
    case_id="caption_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的图表标题模板适配分析",
    abstract=(
        "本文围绕本科毕业论文图表标题模板适配分析问题，分析解析链路对图表 caption 与正文章节边界识别的影响，"
        "并通过实验验证 caption 过滤策略相较短标题启发式的结构保真优势。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文正文中常插入图表标题的情况，本文分析图表 caption 对正文章节识别和评审稳定性的影响。[1]",
                "图 1-1 论文评审系统总体架构图",
                "研究目标是让系统在图表标题出现时仍能稳定保留章节结构，并避免 caption 被误判为新章节。[2]",
                "表 1-1 核心评审维度与指标说明",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖显式编号章节，而正文中的图表标题更容易触发错误分段。[1][3]",
                "Figure 2-1 Baseline parsing workflow",
                "本文将当前 caption 过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
                "Table 2-1 Error categories and examples",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过 caption 模式识别、章节状态控制和正文起点约束，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注图表标题误入章节、正文切分漂移和锚点偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含多处图表标题的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地保留图表标题为正文段落，并减少 caption 对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明图表标题适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨行 caption 和图片注释块仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


EQUATION_CAPTION_VARIATION_CASE = ReviewCaseSpec(
    case_id="equation_caption_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的公式说明块模板适配分析",
    abstract=(
        "本文围绕本科毕业论文公式说明块模板适配分析问题，分析解析链路对公式 caption 与正文章节边界识别的影响，"
        "并通过实验验证公式说明块过滤策略相较短标题启发式的结构保真优势。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文正文中常插入公式说明块的情况，本文分析公式 caption 对正文章节识别和评审稳定性的影响。[1]",
                "式 1-1 论文评审损失函数定义",
                "研究目标是让系统在公式说明块出现时仍能稳定保留章节结构，并避免短公式标题被误判为新章节。[2]",
                "公式 1-2 维度加权得分计算方式",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖图表标题，而正文中的公式说明块同样容易触发错误分段。[1][3]",
                "Equation 2-1 Review score aggregation",
                "本文将当前公式说明块过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
                "Equation (2-2) Evidence consistency score",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过公式 caption 模式识别、章节状态控制和正文起点约束，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注公式说明块误入章节、正文切分漂移和锚点偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含多处公式说明块的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地保留公式说明块为正文段落，并减少公式 caption 对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明公式说明块适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的图片注释块和跨行公式说明仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


ANNOTATION_BLOCK_VARIATION_CASE = ReviewCaseSpec(
    case_id="annotation_block_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的注释性说明块模板适配分析",
    abstract=(
        "本文围绕本科毕业论文注释性说明块模板适配分析问题，分析解析链路对图片注释块与说明性段落边界识别的影响，"
        "并通过实验验证 annotation 过滤策略相较短标题启发式的结构保真优势。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文正文中常插入图片注释块和说明性段落的情况，本文分析 annotation block 对正文章节识别和评审稳定性的影响。[1]",
                "注 1-1 图片仅用于展示系统流程",
                "研究目标是让系统在注释性说明块出现时仍能稳定保留章节结构，并避免短说明行被误判为新章节。[2]",
                "说明 1-2 指标结果采用三轮平均值",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖图表标题和公式说明，而图片注释块与说明性段落同样容易触发错误分段。[1][3]",
                "Note 2-1 Scores are normalized",
                "本文将当前 annotation 过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
                "Remark 2-2 Evidence anchors are sampled",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过 annotation 模式识别、章节状态控制和正文起点约束，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注注释块误入章节、正文切分漂移和锚点偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含多处注释性说明块的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地保留注释性说明块为正文段落，并减少 annotation 对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明注释性说明块适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括页脚注释和脚注编号仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


FOOTER_FOOTNOTE_NOISE_VARIATION_CASE = ReviewCaseSpec(
    case_id="footer_footnote_noise_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的页码与脚注残留噪声过滤方法研究",
    abstract=(
        "面向本科论文初审的页码与脚注残留噪声过滤方法研究聚焦结构化解析过程中孤立页码、罗马页码和脚注标记残留干扰正文识别的问题。"
        "本文分析解析链路对这类结构噪声短行的处理稳定性，并通过实验验证过滤策略相较短标题启发式的结构保真优势。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文转换与复制过程中常混入页码和脚注标记残留的情况，本文分析这些结构噪声对正文章节识别和评审稳定性的影响。[1]",
                "- 1 -",
                "研究目标是让系统在正文中出现孤立页码和脚注标记时仍能稳定保留章节结构，并避免噪声短行被误判为新章节或正文内容。[2]",
                "[1]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖目录和图表标题噪声，而页码残留与脚注标记行同样容易触发错误分段或正文污染。[1][3]",
                "ii",
                "本文将当前结构噪声过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
                "①",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过孤立页码识别、脚注标记过滤和章节状态控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注页码误入正文、脚注锚点污染和章节切分漂移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含多处页码与脚注残留噪声的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地过滤结构噪声短行，并减少页码和脚注标记对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明结构噪声短行过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括跨行脚注正文和真正的 docx footnote 对象仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


RUNNING_HEADER_FOOTER_METADATA_CASE = ReviewCaseSpec(
    case_id="running_header_footer_metadata_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的页眉页脚元数据残留过滤方法研究",
    abstract=(
        "面向本科论文初审的页眉页脚元数据残留过滤方法研究聚焦结构化解析过程中学校页眉、题名重复行和表格化元数据残留干扰正文识别的问题。"
        "本文分析解析链路对这类运行中页眉页脚噪声的处理稳定性，并通过实验验证过滤策略对正文结构保真的作用，创新点在于将题名重复行识别、页眉关键词过滤和表格化元数据跳过策略统一到同一解析状态机中。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文导出或复制过程中常将页眉页脚内容混入正文块序列的情况，本文分析学校页眉、题名重复行和元数据残留对正文识别的影响。[1]",
                "研究目标是让系统在正文章节中夹带页眉页脚表格化元数据时仍能稳定保留真实论证内容，并避免噪声行进入评审证据。[2]",
            ),
            tables=(
                (
                    ("某某大学本科毕业论文",),
                    ("面向本科论文初审的页眉页脚元数据残留过滤方法研究",),
                    ("学号", "2020123456"),
                    ("专业", "软件工程"),
                ),
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往重点处理目录、图表标题和脚注标记，而对正文中重复出现的页眉页脚元数据残留支持不足。[1][3]",
                "本文将当前运行中页眉页脚噪声过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
            tables=(
                (
                    ("本科毕业论文",),
                    ("指导教师", "张老师"),
                ),
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过题名重复行识别、页眉关键词过滤和表格化元数据跳过策略，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "方法的创新点在于把运行中页眉页脚噪声识别与正文状态控制统一建模，从而避免单独规则之间的冲突和顺序依赖。[5]",
                "实验分析同时关注页眉误入正文、元数据污染和章节切分漂移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含页眉页脚元数据残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地过滤正文中的页眉页脚元数据残留，并减少其对评审内容的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明页眉页脚元数据残留过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括真实页眉页脚对象和分节文档中的跨节重复内容仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


RUNNING_ENGLISH_HEADER_FOOTER_CASE = ReviewCaseSpec(
    case_id="running_english_header_footer_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的英文页眉页脚残留过滤方法研究",
    abstract=(
        "面向本科论文初审的英文页眉页脚残留过滤方法研究聚焦结构化解析过程中英文页眉、英文题名重复行和英文元数据短行干扰正文识别的问题。"
        "本文分析解析链路对这类运行中英文页眉页脚噪声的处理稳定性，并通过实验验证过滤策略对正文结构保真的作用，创新点在于把英文页眉提示词和英文元数据短行统一纳入同一噪声判定链路。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文导出或复制过程中常将英文页眉页脚内容混入正文块序列的情况，本文分析英文页眉、英文题名重复行和元数据短行对正文识别的影响。[1]",
                "研究目标是让系统在正文章节中夹带英文页眉页脚元数据时仍能稳定保留真实论证内容，并避免噪声短行进入评审证据。[2]",
                "Undergraduate Thesis",
                "面向本科论文初审的英文页眉页脚残留过滤方法研究",
            ),
            tables=(
                (
                    ("Student ID", "2020123456"),
                    ("Major", "Software Engineering"),
                ),
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往重点处理中文页眉页脚和目录噪声，而对正文中重复出现的英文页眉页脚元数据残留支持不足。[1][3]",
                "本文将当前英文运行中页眉页脚噪声过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
            tables=(
                (
                    ("Bachelor Thesis",),
                    ("Advisor", "Prof. Zhang"),
                ),
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过英文页眉提示词识别、英文元数据短行过滤和正文状态控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "方法的创新点在于把英文页眉页脚噪声识别与正文状态控制统一建模，从而避免中英文规则彼此割裂。[5]",
                "实验分析同时关注英文页眉误入正文、元数据污染和章节切分漂移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含英文页眉页脚元数据残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地过滤正文中的英文页眉页脚元数据残留，并减少其对评审内容的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明英文页眉页脚元数据残留过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的英文摘要页眉和跨页重复标题仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


ABSTRACT_RUNNING_HEADER_VARIATION_CASE = ReviewCaseSpec(
    case_id="abstract_running_header_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的英文摘要页眉残留过滤方法研究",
    abstract=(
        "面向本科论文初审的英文摘要页眉残留过滤方法研究聚焦结构化解析过程中正文跨页后再次出现 `Abstract` 页眉而干扰正文状态机的问题。"
        "本文分析解析链路对这类运行中英文摘要页眉噪声的处理稳定性，并通过实验验证过滤策略对正文结构保真的作用，创新点在于将正文阶段的摘要页眉残留统一纳入运行中噪声判定链路。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文跨页后常将英文摘要页眉残留混入正文块序列的情况，本文分析 `Abstract` 页眉对正文状态机和章节识别的影响。[1]",
                "Abstract",
                "研究目标是让系统在正文中再次遇到英文摘要页眉时仍能稳定保留后续论证内容，而不是错误回退到摘要模式。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖目录和普通页眉噪声，而跨页后的英文摘要页眉更容易直接触发错误状态切换。[1][3]",
                "本文将当前英文摘要页眉残留过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过运行中 `Abstract` 页眉识别、正文状态保护和章节边界控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "方法的创新点在于把摘要页眉残留视为运行中噪声而不是结构重启信号，从而避免状态机回退。[5]",
                "实验分析同时关注摘要页眉误入正文、正文章节漂移和后续段落丢失等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含英文摘要页眉残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地忽略运行中的英文摘要页眉残留，并减少其对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明英文摘要页眉残留过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的中英文混合页眉和分节文档中的重复摘要标题仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


REPEATED_SECTION_HEADER_NOISE_CASE = ReviewCaseSpec(
    case_id="repeated_section_header_noise_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的跨页重复章节标题过滤方法研究",
    abstract=(
        "面向本科论文初审的跨页重复章节标题过滤方法研究聚焦结构化解析过程中页眉将当前章节标题重复注入正文块序列而导致重复分段的问题。"
        "本文分析解析链路对这类跨页重复章节标题噪声的处理稳定性，并通过实验验证过滤策略对正文结构保真的作用，创新点在于将当前章节标题重复行统一纳入运行中噪声判定链路。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文跨页后页眉常重复显示当前章节标题的情况，本文分析重复章节标题对正文分段和评审稳定性的影响。[1]",
                "1 绪论",
                "研究目标是让系统在章节内部再次遇到当前章节标题时仍能稳定保留后续论证内容，而不是错误拆出重复章节。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖目录页标题和题名重复行，而跨页重复章节标题更容易直接触发新的章节切分。[1][3]",
                "2 已有方法比较",
                "本文将当前重复章节标题过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过当前章节标题重复行识别、正文状态保护和章节边界控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "3 方法设计",
                "方法的创新点在于把跨页重复章节标题视为运行中噪声而不是新的结构信号，从而避免重复分段。[5]",
                "实验分析同时关注重复章节误切分、正文漂移和证据锚点错位等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含跨页重复章节标题残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地忽略运行中的重复章节标题残留，并减少其对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明跨页重复章节标题过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨页子章节标题和页眉缩写标题仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


FOOTNOTE_BODY_VARIATION_CASE = ReviewCaseSpec(
    case_id="footnote_body_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的脚注正文块过滤方法研究",
    abstract=(
        "面向本科论文初审的脚注正文块过滤方法研究聚焦结构化解析过程中脚注正文说明块混入正文段落序列而污染评审证据的问题。"
        "本文分析解析链路对这类脚注正文块的处理稳定性，并通过实验验证过滤策略对正文结构保真的作用，创新点在于将脚注标记与说明性短段落统一纳入运行中噪声判定链路。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文转换后脚注正文说明块可能直接落入正文段落序列的情况，本文分析脚注正文块对正文证据和章节识别的影响。[1]",
                "[1] 注：实验平台为课程内部服务器，仅用于教学验证。",
                "研究目标是让系统在正文中遇到脚注正文块时仍能稳定保留后续论证内容，并避免脚注说明进入正文评审证据。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只处理脚注锚点标记，而脚注正文块本身同样容易污染正文证据和问题定位。[1][3]",
                "① Remark: baseline scores come from the prior semester report.",
                "本文将当前脚注正文块过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过脚注标记识别、说明性短段落过滤和正文状态保护，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "方法的创新点在于把脚注正文块视为运行中噪声而不是普通正文段落，从而避免证据污染。[5]",
                "实验分析同时关注脚注正文误入证据、段落漂移和评审结论失真等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含脚注正文块残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地忽略脚注正文块残留，并减少其对正文结构和评审证据的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明脚注正文块过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括真正的 docx footnote 对象和跨行脚注正文仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


DOCX_FOOTNOTE_OBJECT_VARIATION_CASE = ReviewCaseSpec(
    case_id="docx_footnote_object_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的 docx 脚注对象隔离方法研究",
    abstract=(
        "面向本科论文初审的 docx 脚注对象隔离方法研究聚焦结构化解析过程中真实脚注对象及其漂移正文块对评审证据的污染问题。"
        "本文分析解析链路对 docx 脚注 part、正文锚点和漂移脚注文本的处理稳定性，并通过实验验证对象级脚注隔离策略对正文结构保真的作用。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                ParagraphSpec(
                    text="针对真实论文中脚注对象与正文混排的情况，本文分析脚注对象和漂移脚注正文对正文证据识别的影响。[1]",
                    footnote="注：实验平台为课程内部服务器，仅用于教学验证。",
                ),
                "注：实验平台为课程内部服务器，仅用于教学验证。",
                "研究目标是让系统在存在真实 docx 脚注对象时仍能稳定保留后续论证内容，并避免脚注正文进入正文评审证据。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只处理转换后遗留的脚注正文块，而对真实 docx 脚注对象与正文漂移块的联动隔离支持不足。[1][3]",
                "本文将当前脚注对象隔离方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过 docx 脚注 part 提取、正文漂移块匹配和正文状态保护，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "方法的创新点在于把真实脚注对象文本作为排噪证据源，而不是只依赖段落模式规则，从而减少脚注正文污染。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含真实 docx 脚注对象和漂移脚注正文块的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在对象级脚注隔离增强后，系统能够更稳定地忽略漂移脚注正文块，并减少其对正文结构和评审证据的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明 docx 脚注对象隔离对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨行脚注和尾注对象仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


DOCX_ENDNOTE_OBJECT_VARIATION_CASE = ReviewCaseSpec(
    case_id="docx_endnote_object_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的 docx 尾注对象隔离方法研究",
    abstract=(
        "面向本科论文初审的 docx 尾注对象隔离方法研究聚焦结构化解析过程中真实尾注对象及其漂移正文块对评审证据的污染问题。"
        "本文分析解析链路对 docx 尾注 part、正文锚点和漂移尾注文本的处理稳定性，并通过实验验证对象级尾注隔离策略对正文结构保真的作用。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                ParagraphSpec(
                    text="针对真实论文中尾注对象与正文混排的情况，本文分析尾注对象和漂移尾注正文对正文证据识别的影响。[1]",
                    endnote="说明：附加实验参数记录在课程归档仓库中。",
                ),
                "说明：附加实验参数记录在课程归档仓库中。",
                "研究目标是让系统在存在真实 docx 尾注对象时仍能稳定保留后续论证内容，并避免尾注正文进入正文评审证据。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只处理转换后遗留的尾注正文块，而对真实 docx 尾注对象与正文漂移块的联动隔离支持不足。[1][3]",
                "本文将当前尾注对象隔离方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过 docx 尾注 part 提取、正文漂移块匹配和正文状态保护，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "方法的创新点在于把真实尾注对象文本作为排噪证据源，而不是只依赖段落模式规则，从而减少尾注正文污染。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含真实 docx 尾注对象和漂移尾注正文块的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在对象级尾注隔离增强后，系统能够更稳定地忽略漂移尾注正文块，并减少其对正文结构和评审证据的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明 docx 尾注对象隔离对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨行尾注和脚注尾注混排对象仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


MIXED_NOTE_OBJECT_VARIATION_CASE = ReviewCaseSpec(
    case_id="mixed_note_object_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的脚注尾注混排隔离方法研究",
    abstract=(
        "面向本科论文初审的脚注尾注混排隔离方法研究聚焦结构化解析过程中脚注对象、尾注对象和正文相似说明句共存时的排噪精度问题。"
        "本文分析解析链路对混排注释对象与正文相似短句的区分稳定性，并通过实验验证精确匹配策略对正文结构保真的作用。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                ParagraphSpec(
                    text="针对真实论文中脚注与尾注混排的情况，本文分析注释对象、漂移注释正文和相似说明句对正文证据识别的影响。[1]",
                    footnote="说明：课程内网服务器用于复现实验。",
                    endnote="说明：课程镜像服务器用于补充归档。",
                ),
                "说明：课程内网服务器用于复现实验。",
                "说明：课程镜像服务器用于补充归档。",
                "说明：课程内网服务器与课程镜像服务器共同支撑实验复现。",
                "研究目标是让系统在脚注尾注混排时仍能稳定过滤重复注释正文，并保留与注释文本相似但属于正文论证的说明句。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往分别处理脚注或尾注，而对混排对象与正文相似说明句的边界区分支持不足。[1][3]",
                "本文将当前混排注释对象隔离方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过脚注尾注 part 联合提取、精确文本匹配和正文状态保护，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "方法的创新点在于仅过滤与对象级注释文本完全一致的漂移正文块，而保留正文中的相似说明句，从而降低误杀率。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含脚注尾注混排对象和相似正文说明句的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在精确匹配策略增强后，系统能够稳定忽略重复注释正文块，同时保留正文中的相似说明句。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明脚注尾注混排隔离对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨行注释对象和图表注释混排仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


MULTILINE_NOTE_OBJECT_VARIATION_CASE = ReviewCaseSpec(
    case_id="multiline_note_object_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的跨行注释对象隔离方法研究",
    abstract=(
        "面向本科论文初审的跨行注释对象隔离方法研究聚焦结构化解析过程中跨行脚注、跨行尾注及其漂移正文块对评审证据的污染问题。"
        "本文分析解析链路对多段注释对象与正文相似总结句的区分稳定性，并通过实验验证分段级对象匹配策略对正文结构保真的作用。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                ParagraphSpec(
                    text="针对真实论文中跨行脚注与跨行尾注混排的情况，本文分析多段注释对象和漂移正文块对正文证据识别的影响。[1]",
                    footnote=(
                        "注：实验平台部署在课程内网服务器。",
                        "注：相关配置仅用于教学验证。",
                    ),
                    endnote=(
                        "说明：补充日志保存在课程归档仓库。",
                        "说明：归档信息用于结果复核。",
                    ),
                ),
                "注：实验平台部署在课程内网服务器。",
                "注：相关配置仅用于教学验证。",
                "说明：补充日志保存在课程归档仓库。",
                "说明：归档信息用于结果复核。",
                "实验平台、相关配置和归档信息共同支撑教学验证与结果复核。",
                "研究目标是让系统在跨行注释对象存在时仍能稳定过滤重复注释正文，并保留正文中的总结性说明句。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只处理单段注释正文，而对跨行脚注尾注对象与正文相似总结句的边界区分支持不足。[1][3]",
                "本文将当前跨行注释对象隔离方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过脚注尾注 part 联合提取、分段级对象匹配和正文状态保护，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "方法的创新点在于把注释对象中的分段文本也纳入精确匹配，而不是只依赖整条注释拼接结果，从而减少跨行漂移正文污染。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含跨行脚注尾注对象和相似正文总结句的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在分段级对象匹配增强后，系统能够稳定忽略跨行重复注释正文块，同时保留正文中的总结性说明句。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明跨行注释对象隔离对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括注释对象落在表格附近和更复杂的富文本注释仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


TABLE_ADJACENT_NOTE_OBJECT_VARIATION_CASE = ReviewCaseSpec(
    case_id="table_adjacent_note_object_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的表格邻接注释对象隔离方法研究",
    abstract=(
        "面向本科论文初审的表格邻接注释对象隔离方法研究聚焦结构化解析过程中脚注尾注对象出现在表格单元格附近时的排噪精度问题。"
        "本文分析解析链路对表格单元格注释对象、表格内重复注释正文和正文总结句的区分稳定性，并通过实验验证对象级精确匹配策略对正文结构保真的作用。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文中注释对象常出现在配置表、参数表附近的情况，本文分析表格邻接注释对象对正文证据识别的影响。[1]",
                "研究目标是让系统在表格单元格附近存在脚注尾注对象时仍能稳定过滤重复注释正文，并保留正文中的总结性说明句。[2]",
            ),
            tables=(
                TableSpec(
                    rows=(
                        (
                            "实验配置",
                            TableCellSpec(
                                text="课程内网服务器",
                                footnote="注：课程内网服务器用于复现实验。",
                            ),
                        ),
                        (
                            "归档说明",
                            TableCellSpec(
                                text="课程镜像服务器",
                                endnote="说明：课程镜像服务器用于补充归档。",
                            ),
                        ),
                        ("注：课程内网服务器用于复现实验。", ""),
                        ("说明：课程镜像服务器用于补充归档。", ""),
                    ),
                ),
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只处理普通段落中的注释正文，而对表格邻接注释对象与表格内重复注释正文的联动隔离支持不足。[1][3]",
                "本文将当前表格邻接注释对象隔离方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过脚注尾注 part 联合提取、表格行匹配和正文状态保护，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "方法的创新点在于将表格行文本也纳入对象级精确匹配，同时保留正文中的总结性说明句，从而降低误杀率。[5]",
                "课程内网服务器与课程镜像服务器共同支撑实验复现与结果归档。",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含表格邻接注释对象和表格内重复注释正文的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在对象级精确匹配增强后，系统能够稳定忽略表格中的重复注释正文，同时保留正文中的总结性说明句。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明表格邻接注释对象隔离对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括注释对象直接嵌入复杂表格结构和更复杂的富文本注释仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


REPEATED_PARENT_SECTION_HEADER_NOISE_CASE = ReviewCaseSpec(
    case_id="repeated_parent_section_header_noise_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的跨页上级章节标题过滤方法研究",
    abstract=(
        "面向本科论文初审的跨页上级章节标题过滤方法研究聚焦结构化解析过程中页眉将上级章节标题重复注入子章节正文块序列而导致重复分段的问题。"
        "本文分析解析链路对这类跨页上级章节标题噪声的处理稳定性，并通过实验验证过滤策略对正文结构保真的作用，创新点在于将已出现过的上级章节标题统一纳入运行中噪声判定链路。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文跨页后页眉常重复显示上级章节标题的情况，本文分析重复上级章节标题对正文分段和评审稳定性的影响。[1]",
                "研究目标是让系统在子章节内部再次遇到上级章节标题时仍能稳定保留后续论证内容，而不是错误拆出重复章节。[2]",
            ),
        ),
        SectionSpec(
            heading="2 相关工作与方法设计",
            paragraphs=(
                "本章先回顾相关工作中关于标题识别、页眉噪声过滤和结构化解析的已有方法，再概述本文解析链路与正文结构保护的总体设计。[1][3]",
                "本文将当前上级章节标题过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力，并明确与已有方法的差异。[4]",
            ),
        ),
        SectionSpec(
            heading="2.1 数据集构建",
            paragraphs=(
                "子章节重点说明评测样本如何覆盖真实学校模板差异与结构噪声场景。[2][4]",
                "2 相关工作与方法设计",
                "方法的创新点在于把跨页上级章节标题视为运行中噪声而不是新的结构信号，从而避免重复分段。[5]",
            ),
        ),
        SectionSpec(
            heading="3 实验评估",
            paragraphs=(
                "实验评估选取包含跨页上级章节标题残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地忽略运行中的上级章节标题残留，并减少其对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="4 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明跨页上级章节标题过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨页页眉缩写标题和附录上级标题残留仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


REPEATED_SUBSECTION_HEADER_NOISE_CASE = ReviewCaseSpec(
    case_id="repeated_subsection_header_noise_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的跨页子章节标题过滤方法研究",
    abstract=(
        "面向本科论文初审的跨页子章节标题过滤方法研究聚焦结构化解析过程中页眉将子章节标题重复注入更细一级正文块序列而导致重复分段的问题。"
        "本文分析解析链路对这类跨页子章节标题噪声的处理稳定性，并通过实验验证过滤策略对正文结构保真的作用，创新点在于将已出现过的子章节标题统一纳入运行中噪声判定链路。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文跨页后页眉常重复显示子章节标题的情况，本文分析重复子章节标题对正文分段和评审稳定性的影响。[1]",
                "研究目标是让系统在更细一级小节内部再次遇到子章节标题时仍能稳定保留后续论证内容，而不是错误拆出重复小节。[2]",
            ),
        ),
        SectionSpec(
            heading="2 相关工作与方法设计",
            paragraphs=(
                "本章先回顾相关工作中关于标题识别、页眉噪声过滤和结构化解析的已有方法，再概述解析链路、状态控制和正文结构保护的总体设计。[1][3]",
                "本文将当前子章节标题过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力，并明确与已有方法的差异。[4]",
            ),
        ),
        SectionSpec(
            heading="2.1 数据集构建",
            paragraphs=(
                "子章节重点说明评测样本如何覆盖真实学校模板差异与结构噪声场景。[2][4]",
                "本节同时说明样本构造如何服务于误报控制和回归验证。[5]。",
            ),
        ),
        SectionSpec(
            heading="2.1.1 标注原则",
            paragraphs=(
                "更细一级小节说明标注原则、锚点规范和问题标题 expectation 的整理方式。[2][4]",
                "2.1 数据集构建",
                "方法的创新点在于把跨页子章节标题视为运行中噪声而不是新的结构信号，从而避免重复分段。[5]",
            ),
        ),
        SectionSpec(
            heading="3 实验评估",
            paragraphs=(
                "实验评估选取包含跨页子章节标题残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地忽略运行中的子章节标题残留，并减少其对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="4 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明跨页子章节标题过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨页三级标题缩写和图表页眉标题残留仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


ABBREVIATED_SECTION_HEADER_NOISE_CASE = ReviewCaseSpec(
    case_id="abbreviated_section_header_noise_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的跨页缩写章节标题过滤方法研究",
    abstract=(
        "面向本科论文初审的跨页缩写章节标题过滤方法研究聚焦结构化解析过程中页眉将已出现章节标题以缩写形式重复注入正文块序列而导致重复分段的问题。"
        "本文分析解析链路对这类缩写章节标题噪声的处理稳定性，并通过实验验证过滤策略对正文结构保真的作用，创新点在于将编号一致且文本为已出现标题前缀的短行统一纳入运行中噪声判定链路。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文跨页后页眉常以缩写形式重复显示章节标题的情况，本文分析缩写章节标题对正文分段和评审稳定性的影响。[1]",
                "研究目标是让系统在更细一级正文中再次遇到已出现章节标题的缩写时仍能稳定保留后续论证内容，而不是错误拆出重复章节。[2]",
            ),
        ),
        SectionSpec(
            heading="2 相关工作与方法设计",
            paragraphs=(
                "本章先回顾相关工作中关于标题识别、页眉噪声过滤和结构化解析的已有方法，再概述解析链路、状态控制和正文结构保护的总体设计。[1][3]",
                "本文将当前缩写章节标题过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力，并明确与已有方法的差异。[4]",
            ),
        ),
        SectionSpec(
            heading="2.1 数据集构建与标注策略",
            paragraphs=(
                "子章节重点说明评测样本如何覆盖真实学校模板差异与结构噪声场景，并说明标注与解析验证如何配合进行。[2][4]",
                "本节同时说明样本构造如何服务于误报控制、结构回归和 benchmark 诊断闭环。[5]",
            ),
        ),
        SectionSpec(
            heading="2.1.1 标注原则",
            paragraphs=(
                "更细一级小节说明标注原则、锚点规范和问题标题 expectation 的整理方式。[2][4]",
                "2.1 数据集构建",
                "方法的创新点在于把缩写章节标题视为运行中噪声而不是新的结构信号，从而避免重复分段。[5]",
            ),
        ),
        SectionSpec(
            heading="3 实验评估",
            paragraphs=(
                "实验评估选取包含跨页缩写章节标题残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地忽略运行中的缩写章节标题残留，并减少其对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="4 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明跨页缩写章节标题过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括无编号缩写页眉和真正的页眉对象级提取仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


UNNUMBERED_ABBREVIATED_SECTION_HEADER_NOISE_CASE = ReviewCaseSpec(
    case_id="unnumbered_abbreviated_section_header_noise_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的无编号缩写页眉标题过滤方法研究",
    abstract=(
        "面向本科论文初审的无编号缩写页眉标题过滤方法研究聚焦结构化解析过程中页眉将已出现编号章节标题以无编号缩写形式重复注入正文块序列而导致重复分段的问题。"
        "本文分析解析链路对这类无编号缩写页眉标题噪声的处理稳定性，并通过实验验证过滤策略对正文结构保真的作用，创新点在于将无编号且文本为已出现标题前缀的短行纳入运行中噪声判定链路。"
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文跨页后页眉常以无编号缩写形式重复显示章节标题的情况，本文分析无编号缩写标题对正文分段和评审稳定性的影响。[1]",
                "研究目标是让系统在更细一级正文中再次遇到已出现编号章节标题的无编号缩写时仍能稳定保留后续论证内容，而不是错误拆出重复章节。[2]",
            ),
        ),
        SectionSpec(
            heading="2 相关工作与方法设计",
            paragraphs=(
                "本章先回顾相关工作中关于标题识别、页眉噪声过滤和结构化解析的已有方法，再概述解析链路、状态控制和正文结构保护的总体设计。[1][3]",
                "本文将当前无编号缩写页眉标题过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力，并明确与已有方法的差异。[4]",
            ),
        ),
        SectionSpec(
            heading="2.1 数据集构建与标注策略",
            paragraphs=(
                "子章节重点说明评测样本如何覆盖真实学校模板差异与结构噪声场景，并说明标注与解析验证如何配合进行。[2][4]",
                "本节同时说明样本构造如何服务于误报控制、结构回归和 benchmark 诊断闭环。[5]",
            ),
        ),
        SectionSpec(
            heading="2.1.1 标注原则",
            paragraphs=(
                "更细一级小节说明标注原则、锚点规范和问题标题 expectation 的整理方式。[2][4]",
                "数据集构建",
                "方法的创新点在于把无编号缩写页眉标题视为运行中噪声而不是新的结构信号，从而避免重复分段。[5]",
            ),
        ),
        SectionSpec(
            heading="3 实验评估",
            paragraphs=(
                "实验评估选取包含无编号缩写页眉标题残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地忽略运行中的无编号缩写页眉标题残留，并减少其对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="4 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明无编号缩写页眉标题过滤对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括真正的页眉对象级提取和更自由的英文缩写页眉仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


CONTENTS_FIELD_CODE_VARIATION_CASE = ReviewCaseSpec(
    case_id="contents_field_code_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的目录字段代码残留模板适配分析",
    abstract=(
        "本文围绕本科毕业论文目录字段代码残留模板适配分析问题，分析解析链路对 PAGEREF、HYPERLINK 和 _Toc 超链接残留的处理稳定性，"
        "并通过实验验证目录字段代码过滤策略相较仅按页码模式识别目录项的结构保真优势。"
    ),
    post_abstract_front_matter=(
        "Contents",
        "1 Introduction PAGEREF _Toc482011111 \\h 1",
        "PAGEREF _Toc482011111 \\h",
        'HYPERLINK \\l "_Toc482011112"',
        "2 Related Work PAGEREF _Toc482011112 \\h 5",
        "TOC \\o \"1-3\" \\h \\z \\u",
        "3 Method Design PAGEREF _Toc482011113 \\h 9",
        "_Toc482011113",
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对自动生成目录中常残留 PAGEREF 和 HYPERLINK 字段代码的问题，本文分析其对正文章节识别和评审稳定性的影响。[1]",
                "研究目标是让系统在目录页带字段代码残留时仍能稳定跳过目录噪声，并保留真实章节结构与摘要边界。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖带页码的普通目录项，而字段代码残留行更容易被误判为正文标题或未命名章节。[1][3]",
                "本文将当前目录字段代码过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过目录字段代码识别、目录项模式扩展和正文起点控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注字段代码误入正文、章节重复和正文起点漂移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含目录字段代码残留的多种学校模板，指标包括正文章节识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过目录字段代码残留，并减少超链接噪声对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明目录字段代码残留适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的 Word 域代码碎片和跨页目录残留仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


KEYWORD_VARIATION_CASE = ReviewCaseSpec(
    case_id="keyword_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的摘要关键词区模板适配分析",
    abstract=(
        "本文围绕本科毕业论文摘要关键词区模板适配分析问题，分析解析链路对中英文关键词区、摘要边界和正文起点识别的影响，"
        "并通过实验验证关键词区保留策略相较直接切段规则的结构稳定优势。"
    ),
    post_abstract_front_matter=(
        "关键词：本科论文初审；多智能体评审；docx 解析；benchmark",
        "Abstract",
        (
            "This paper studies keyword-area layouts in undergraduate thesis templates, "
            "and evaluates whether the parser can preserve abstract and keyword blocks "
            "without polluting the body structure."
        ),
        "Key words: thesis review; parser stability; benchmark; docx",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中摘要后常附带关键词区的情况，本文分析关键词区对正文起点识别和结构稳定性的影响。[1]",
                "研究目标是让系统在中英文关键词区共存时仍能稳定保留摘要块，并避免关键词误入正文结构。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只识别摘要标题，而忽略关键词区在模板中的位置变化，这会导致正文切分和锚点定位偏移。[1][3]",
                "本文将当前关键词区处理方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过关键词标题识别、关键词行保留和正文起点控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注关键词误入正文、摘要截断和英文摘要错位等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含中英文关键词区的多种学校模板，指标包括摘要保真度、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地处理关键词区布局，并减少摘要边界漂移。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明摘要关键词区适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂关键词格式和摘要后元数据区仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


METADATA_BLOCK_VARIATION_CASE = ReviewCaseSpec(
    case_id="metadata_block_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的摘要元数据区模板适配分析",
    abstract=(
        "本文围绕本科毕业论文摘要元数据区模板适配分析问题，分析解析链路对关键词区、分类号区和正文起点识别的影响，"
        "并通过实验验证元数据块过滤策略相较直接切段规则的结构稳定优势。"
    ),
    post_abstract_front_matter=(
        "关键词：本科论文初审；评审框架；docx 解析",
        "分类号：TP391.1",
        "学校代码：10487",
        "学号：2020123456",
        "UDC: 004.8",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中摘要后常附带分类号和学号等元数据区的情况，本文分析元数据块对正文起点识别和结构稳定性的影响。[1]",
                "研究目标是让系统在关键词区与元数据区共存时仍能稳定保留摘要块，并避免元数据误入正文结构。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只处理摘要标题和目录页，而忽略分类号、学校代码和学号等元数据区的模板差异，这会导致正文切分偏移。[1][3]",
                "本文将当前元数据块过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过关键词识别、元数据前缀识别和正文起点控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注元数据误入正文、摘要截断和章节顺序偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含摘要元数据区的多种学校模板，指标包括摘要保真度、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过摘要后的元数据块，并减少正文起点误判。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明摘要元数据区适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的保密级别与作者信息区仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


AUTHOR_INFO_VARIATION_CASE = ReviewCaseSpec(
    case_id="author_info_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的作者信息区模板适配分析",
    abstract=(
        "本文围绕本科毕业论文作者信息区模板适配分析问题，分析解析链路对关键词区、作者信息区和正文起点识别的影响，"
        "并通过实验验证作者信息块过滤策略相较直接切段规则的结构稳定优势。"
    ),
    post_abstract_front_matter=(
        "关键词：本科论文初审；评审框架；docx 解析",
        "保密级别：公开",
        "作者姓名：张三",
        "指导教师：李老师",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中摘要后常附带保密级别、作者姓名和指导教师等作者信息区的情况，本文分析作者信息块对正文起点识别和结构稳定性的影响。[1]",
                "研究目标是让系统在关键词区与作者信息区共存时仍能稳定保留摘要块，并避免作者信息误入正文结构。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只处理摘要标题和目录页，而忽略作者信息区的模板差异，这会导致正文切分偏移和锚点定位误差。[1][3]",
                "本文将当前作者信息块过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过关键词识别、作者信息前缀识别和正文起点控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注作者信息误入正文、摘要截断和章节顺序偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含作者信息区的多种学校模板，指标包括摘要保真度、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过摘要后的作者信息块，并减少正文起点误判。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明作者信息区适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的合作作者信息区和院系信息块仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


APPENDIX_VARIATION_CASE = ReviewCaseSpec(
    case_id="appendix_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的附录结构模板适配分析",
    abstract=(
        "本文围绕本科毕业论文附录结构模板适配分析问题，分析解析链路对目录附录项、附录正文和主正文边界识别的影响，"
        "并通过实验验证附录过滤策略相较直接拼接规则的结构稳定优势。"
    ),
    post_abstract_front_matter=(
        "目录",
        "第一章 绪论................................1",
        "第二章 已有方法比较..........................5",
        "第三章 方法设计..............................9",
        "第四章 实验评估............................13",
        "第五章 结论与局限..........................17",
        "附录 A 系统提示词样例......................21",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中目录页附录项和正文附录章节并存的情况，本文分析附录结构对主正文识别和评审稳定性的影响。[1]",
                "研究目标是让系统在存在附录章节时仍能稳定保留主正文结构，并避免附录内容误入五维评审正文。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只处理目录页和参考文献边界，而忽略附录内容对正文章节切分和 finding 锚点的干扰。[1][3]",
                "本文将当前附录过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过目录附录项识别、附录标题检测和正文起点控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注附录误入正文、章节重复和代码片段噪声残留等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含附录章节的多种学校模板，指标包括主正文识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过附录正文，并减少附录内容对正文评审的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明附录结构适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的多附录目录和附录表格仍需后续扩展支持。",
            ),
        ),
        SectionSpec(
            heading="附录 A",
            paragraphs=(
                "本附录给出系统提示词样例、补充实验截图和代码片段，用于辅助说明实现细节。",
                "附录中的提示词和截图不应被纳入主正文的五维评审结论。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


ENGLISH_APPENDIX_VARIATION_CASE = ReviewCaseSpec(
    case_id="english_appendix_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的英文附录结构模板适配分析",
    abstract=(
        "本文围绕本科毕业论文英文附录结构模板适配分析问题，分析解析链路对英文附录目录项、英文附录正文和主正文边界识别的影响，"
        "并通过实验验证附录过滤策略相较直接拼接规则的结构稳定优势。"
    ),
    post_abstract_front_matter=(
        "Contents",
        "1 Introduction................................1",
        "2 Related Work................................5",
        "3 Method Design...............................9",
        "4 Evaluation.................................13",
        "5 Conclusion and Limitations................17",
        "Appendix A Prompt Templates.................21",
        "Appendix B Supplementary Results............23",
    ),
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=(
                "针对真实论文模板中英文附录目录项和英文附录正文并存的情况，本文分析英文附录结构对主正文识别和评审稳定性的影响。[1]",
                "研究目标是让系统在存在英文附录章节时仍能稳定保留主正文结构，并避免附录内容误入五维评审正文。[2]",
            ),
        ),
        SectionSpec(
            heading="2 已有方法比较",
            paragraphs=(
                "现有方案通常只处理中文目录页和参考文献边界，而忽略英文附录内容对正文章节切分和 finding 锚点的干扰。[1][3]",
                "本文将当前英文附录过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="3 方法设计",
            paragraphs=(
                "本文通过英文附录目录项识别、英文附录标题检测和正文起点控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注英文附录误入正文、章节重复和补充材料噪声残留等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="4 实验评估",
            paragraphs=(
                "实验评估选取包含英文附录章节的多种学校模板，指标包括主正文识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过英文附录正文，并减少补充材料对正文评审的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="5 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明英文附录结构适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的多级英文附录和附录图表仍需后续扩展支持。",
            ),
        ),
        SectionSpec(
            heading="Appendix A Prompt Templates",
            paragraphs=(
                "This appendix lists prompt templates and supporting materials used for implementation details.",
                "Appendix prompt templates should not be included in the main five-dimension review body.",
            ),
        ),
        SectionSpec(
            heading="Appendix B Supplementary Results",
            paragraphs=(
                "This appendix provides supplementary figures and additional result tables for reference.",
                "Supplementary appendix results should not change the main body structure extracted for review.",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


DEPARTMENT_INFO_VARIATION_CASE = ReviewCaseSpec(
    case_id="department_info_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的院系信息区模板适配分析",
    abstract=(
        "本文围绕本科毕业论文院系信息区模板适配分析问题，分析解析链路对关键词区、院系信息区和正文起点识别的影响，"
        "并通过实验验证院系信息块过滤策略相较直接切段规则的结构稳定优势。"
    ),
    post_abstract_front_matter=(
        "关键词：本科论文初审；评审框架；docx 解析",
        "学院：计算机科学与技术学院",
        "专业：软件工程",
        "班级：2020级1班",
        "作者单位：某某大学信息学院",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中摘要后常附带学院、专业、班级和作者单位等院系信息区的情况，本文分析信息块对正文起点识别和结构稳定性的影响。[1]",
                "研究目标是让系统在关键词区与院系信息区共存时仍能稳定保留摘要块，并避免院系信息误入正文结构。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只处理摘要标题和目录页，而忽略院系信息区的模板差异，这会导致正文切分偏移和锚点定位误差。[1][3]",
                "本文将当前院系信息块过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过关键词识别、院系信息前缀识别和正文起点控制，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注院系信息误入正文、摘要截断和章节顺序偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含院系信息区的多种学校模板，指标包括摘要保真度、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过摘要后的院系信息块，并减少正文起点误判。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明院系信息区适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨学院联合培养信息块仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


BILINGUAL_ABSTRACT_CASE = ReviewCaseSpec(
    case_id="bilingual_abstract_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的双语摘要模板适配分析",
    abstract=(
        "本文围绕本科毕业论文双语摘要模板适配分析问题，分析解析链路在中英文摘要并存场景下的稳定性，"
        "并通过实验验证系统相较单摘要布局在双语摘要边界识别上的兼容能力与差异优势。"
    ),
    post_abstract_front_matter=(
        "Abstract",
        (
            "This paper studies bilingual abstract layouts in undergraduate thesis templates, "
            "and evaluates whether the parser can preserve abstract content and body structure "
            "when Chinese and English abstracts appear together."
        ),
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中常见的中英双语摘要布局，本文分析摘要切分和章节识别在双语场景下的稳定性。[1]",
                "研究目标是让系统在双语摘要共存时仍能稳定保留正文结构，并减少摘要边界识别误差。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案多默认单摘要结构，而真实学校模板中的双语摘要常改变章节起点和正文边界，需要更稳健的解析策略。[1][3]",
                "本文将当前方案与 baseline、benchmark 文档样式进行比较，以验证双语摘要模板的适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过摘要标题识别、正文起点控制和证据锚点约束，提升双语摘要模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注摘要串段、正文错位和参考文献边界漂移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含双语摘要的多种学校模板，指标包括摘要保留完整度、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地处理双语摘要布局，并减少摘要边界误差。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明双语摘要模板适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括复杂英文摘要格式和摘要关键词区域仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


DECLARATION_VARIATION_CASE = ReviewCaseSpec(
    case_id="declaration_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的声明页模板适配分析",
    abstract=(
        "本文围绕本科毕业论文声明页模板适配分析问题，分析解析链路对摘要边界和正文起点识别的影响，"
        "并通过实验验证声明页过滤策略相较未过滤基线在真实学校模板中的稳定性与结构保真优势。"
    ),
    post_abstract_front_matter=(
        "独创性声明",
        "本人声明所提交的毕业论文是在指导教师指导下独立完成的研究成果。",
        "学术诚信承诺书",
        "本人承诺遵守学校学术规范，保证论文内容真实、引用规范。",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中声明页常位于摘要后、正文前的情况，本文分析其对正文起点识别和章节切分的影响。[1]",
                "研究目标是让系统在保留摘要和正文结构的同时，稳定跳过声明页与承诺书内容。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只处理目录页和参考文献边界，较少考虑声明页对正文切分和 finding 锚点的干扰。[1][3]",
                "本文将当前方案与 baseline、benchmark 文档样式进行比较，以验证声明页过滤策略的有效性。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过前置声明标题识别、无关段落跳过和正文起点控制，提升真实论文模板下的解析稳定性。[2][4]",
                "实验分析同时关注声明页误入正文、摘要污染和章节顺序偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含声明页的多种学校模板，指标包括正文章节识别准确率、摘要保真度和结构一致性。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过声明页，并保留真实正文章节结构。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明声明页适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的授权书和跨学校声明样式仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


FRONT_MATTER_COMBO_VARIATION_CASE = ReviewCaseSpec(
    case_id="front_matter_combo_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的复杂前置区组合模板适配分析",
    abstract=(
        "本文围绕本科毕业论文复杂前置区组合模板适配分析问题，分析解析链路在关键词区、复合元数据块、英文目录和多附录并存场景下的稳定性，"
        "并通过实验验证组合前置区过滤策略相较单一规则在真实学校模板中的结构保真优势。"
    ),
    post_abstract_front_matter=(
        "关键词：本科论文初审；前置区组合；docx 解析；benchmark",
        "Key words: thesis review; front matter combination; parser stability",
        "分类号：TP391.1",
        "学校代码：10487",
        "学号：2020123456",
        "UDC: 004.8",
        "学院：计算机科学与技术学院",
        "专业：软件工程",
        "导师组：智能系统导师组",
        "学位类型：工学学士",
        "Contents",
        "1 Introduction\t1",
        "2 Related Work\t3",
        "3 Method Design\t6",
        "4 Evaluation\t10",
        "Appendix A Prompt Templates\t23",
        "Appendix B Supplementary Figures\t27",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实学校模板中关键词区、元数据块和英文目录叠加出现的情况，本文分析复杂前置区组合对正文章节识别和评审稳定性的影响。[1]",
                "研究目标是让系统在多块前置区混排时仍能稳定保留摘要信息，并准确定位正文起点与真实章节结构。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案往往只覆盖单一目录页或单一元数据区，而对关键词区、导师组信息和英文附录目录混排场景支持不足。[1][3]",
                "本文将当前组合前置区过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过关键词识别、复合元数据前缀识别、英文目录项过滤和正文起点控制，提升复杂学校模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注目录误入正文、前置信息串段和附录目录污染主正文评审等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含复合前置区和多附录目录的多种学校模板，指标包括摘要保真度、正文章节识别准确率和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过复合前置区组合，并减少英文目录与附录目录对正文结构的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明复杂前置区组合适配对后续论文评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的联合培养信息块和附录图表目录仍需后续扩展支持。",
            ),
        ),
        SectionSpec(
            heading="Appendix A Prompt Templates",
            paragraphs=(
                "Appendix prompt templates should not be included in the main five-dimension review body.",
                "The appendix contains supplementary prompts used for internal debugging only.",
            ),
        ),
        SectionSpec(
            heading="附录 B 补充图表",
            paragraphs=(
                "图 B-1 复杂前置区模板示意图",
                "表 B-1 学校模板元数据字段对照表",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


FRONT_MATTER_SPACING_VARIATION_CASE = ReviewCaseSpec(
    case_id="front_matter_spacing_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的前置区空格对齐模板适配分析",
    abstract=(
        "本文围绕本科毕业论文前置区空格对齐模板适配分析问题，分析解析链路对空格分隔关键词区、元数据区与院系信息区的处理稳定性，"
        "并通过实验验证空格对齐模板过滤策略相较仅支持冒号分隔规则的结构保真优势。"
    ),
    post_abstract_front_matter=(
        "关键词 本科论文初审；前置区空格对齐；docx 解析；benchmark",
        "Key words thesis review; metadata spacing; parser stability",
        "学校代码 10487",
        "学号 2020123456",
        "学院 计算机科学与技术学院",
        "专业 软件工程",
        "导师组 智能系统导师组",
        "学位类型 工学学士",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实学校模板中前置区字段常用空格对齐而非冒号分隔的情况，本文分析其对摘要边界识别和正文定位稳定性的影响。[1]",
                "研究目标是让系统在关键词区、元数据区和导师组信息都采用空格分隔时仍能稳定保留摘要并准确切入正文。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只覆盖带冒号的前置区字段，而对学校代码、学位类型等采用空格对齐的模板支持不足。[1][3]",
                "本文将当前空格对齐前置区过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过关键词标题识别、前置区字段前缀识别和正文起点控制，提升空格对齐学校模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注关键词误入正文、字段串段和摘要污染等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含空格对齐前置区的多种学校模板，指标包括摘要保真度、正文章节识别准确率和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过空格分隔前置区字段，并减少正文起点误判。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明前置区空格对齐模板适配对后续论文评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨行字段和值换行布局仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


FRONT_MATTER_MULTILINE_VARIATION_CASE = ReviewCaseSpec(
    case_id="front_matter_multiline_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的前置区跨行字段模板适配分析",
    abstract=(
        "本文围绕本科毕业论文前置区跨行字段模板适配分析问题，分析解析链路对跨行关键词区、元数据区和导师组信息区的处理稳定性，"
        "并通过实验验证跨行字段过滤策略相较单行规则在真实学校模板中的结构保真优势。"
    ),
    post_abstract_front_matter=(
        "关键词",
        "本科论文初审；跨行前置区；docx 解析；benchmark",
        "Key words",
        "thesis review; multiline metadata; parser stability",
        "学校代码",
        "10487",
        "学号",
        "2020123456",
        "导师组",
        "智能系统导师组",
        "学位类型",
        "工学学士",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实学校模板中前置区字段常跨行展示的情况，本文分析其对摘要边界识别和正文定位稳定性的影响。[1]",
                "研究目标是让系统在关键词、元数据和导师组字段值位于下一行时仍能稳定保留摘要并准确切入正文。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只覆盖单行前置区字段，而对跨行展示的学校代码、学位类型等模板支持不足。[1][3]",
                "本文将当前跨行前置区过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过前置区状态控制、字段前缀识别和正文起点约束，提升跨行学校模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注字段值误判为正文标题、摘要污染和章节顺序偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含跨行前置区字段的多种学校模板，指标包括摘要保真度、正文章节识别准确率和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过跨行字段值，并减少正文起点误判。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明前置区跨行字段模板适配对后续论文评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的表格化前置区字段仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


APPENDIX_CONTENTS_VARIATION_CASE = ReviewCaseSpec(
    case_id="appendix_contents_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的附录目录页模板适配分析",
    abstract=(
        "本文围绕本科毕业论文附录目录页模板适配分析问题，分析解析链路对附录目录页、附录正文和主正文边界识别的影响，"
        "并通过实验验证附录目录页过滤策略相较直接拼接规则的结构稳定优势。"
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中正文结束后会出现附录目录页的情况，本文分析附录目录页对主正文识别和评审稳定性的影响。[1]",
                "研究目标是让系统在附录目录页和附录正文并存时仍能稳定保留主正文结构，并避免目录页内容误入五维评审正文。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只处理正文前部目录页，而对正文后的附录目录页与附录图表目录支持不足。[1][3]",
                "本文将当前附录目录页过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过附录目录标题识别、附录目录项过滤和附录正文隔离，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注附录目录误入正文、图表目录残留和章节重复等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含附录目录页的多种学校模板，指标包括主正文识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过附录目录页与附录正文，并减少补充材料对正文评审的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明附录目录页适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的多级图表目录和附录索引页仍需后续扩展支持。",
            ),
        ),
        SectionSpec(
            heading="附录目录",
            paragraphs=(
                "附录 A 访谈提纲................................21",
                "附录 B 问卷样例................................25",
                "附录图目录....................................27",
            ),
        ),
        SectionSpec(
            heading="附录 A 访谈提纲",
            paragraphs=(
                "本附录给出访谈提纲和补充问题列表，用于说明研究实施过程。",
                "附录中的补充材料不应被纳入主正文的五维评审结论。",
            ),
        ),
        SectionSpec(
            heading="附录 B 问卷样例",
            paragraphs=(
                "本附录给出问卷样例和原始字段设计。",
                "附录问卷样例不应改变主正文结构抽取结果。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


FRONT_MATTER_TABLE_VARIATION_CASE = ReviewCaseSpec(
    case_id="front_matter_table_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的前置区表格化字段模板适配分析",
    abstract=(
        "本文围绕本科毕业论文前置区表格化字段模板适配分析问题，分析解析链路对制表符对齐关键词区、元数据区和导师组信息区的处理稳定性，"
        "并通过实验验证表格化字段过滤策略相较普通文本规则的结构保真优势。"
    ),
    post_abstract_front_matter=(
        "关键词\t本科论文初审；表格化前置区；docx 解析；benchmark",
        "Key words\tthesis review; tabular metadata; parser stability",
        "学校代码\t10487",
        "学号\t2020123456",
        "学院\t计算机科学与技术学院",
        "专业\t软件工程",
        "导师组\t智能系统导师组",
        "学位类型\t工学学士",
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实学校模板中前置区字段常采用制表符或表格化方式对齐的情况，本文分析其对摘要边界识别和正文定位稳定性的影响。[1]",
                "研究目标是让系统在关键词区、元数据区和导师组信息采用表格化字段布局时仍能稳定保留摘要并准确切入正文。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只覆盖普通段落形式的前置区字段，而对学校代码、学位类型等采用表格化对齐的模板支持不足。[1][3]",
                "本文将当前表格化前置区过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过关键词前缀识别、元数据字段前缀识别和正文起点控制，提升表格化学校模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注字段值误入正文、摘要污染和章节顺序偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含表格化前置区字段的多种学校模板，指标包括摘要保真度、正文章节识别准确率和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过表格化前置区字段，并减少正文起点误判。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明前置区表格化字段模板适配对后续论文评审质量具有基础性作用。",
                "本章也说明了局限性，包括真正嵌套表格单元格中的字段仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


APPENDIX_FIGURE_LIST_VARIATION_CASE = ReviewCaseSpec(
    case_id="appendix_figure_list_variation_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的附录图表目录页模板适配分析",
    abstract=(
        "本文围绕本科毕业论文附录图表目录页模板适配分析问题，分析解析链路对附录图目录、附录表目录和附录正文边界识别的影响，"
        "并通过实验验证附录图表目录页过滤策略相较直接拼接规则的结构稳定优势。"
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实论文模板中正文结束后会单独给出附录图目录和附录表目录的情况，本文分析附录图表目录页对主正文识别和评审稳定性的影响。[1]",
                "研究目标是让系统在附录图表目录页与附录正文并存时仍能稳定保留主正文结构，并避免目录页内容误入五维评审正文。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只处理普通附录目录页，而对附录图目录、附录表目录和英文图表目录支持不足。[1][3]",
                "本文将当前附录图表目录页过滤方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过附录图表目录标题识别、目录项过滤和附录正文隔离，提升真实论文模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注图表目录误入正文、附录页残留和章节重复等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含附录图目录和附录表目录的多种学校模板，指标包括主正文识别准确率、结构一致性和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过附录图表目录页与附录正文，并减少补充材料对正文评审的污染。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明附录图表目录页适配对后续评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的跨页图表目录索引仍需后续扩展支持。",
            ),
        ),
        SectionSpec(
            heading="附录图目录",
            paragraphs=(
                "图 A-1 访谈流程图................................21",
                "图 B-1 问卷字段结构图............................24",
            ),
        ),
        SectionSpec(
            heading="List of Appendix Tables",
            paragraphs=(
                "Table A-1 Interview Coding Scheme.................26",
                "Table B-1 Supplementary Questionnaire Fields......28",
            ),
        ),
        SectionSpec(
            heading="附录 A 访谈材料",
            paragraphs=(
                "本附录给出访谈流程图和访谈编码方案，用于说明研究实施细节。",
                "附录图表材料不应被纳入主正文的五维评审结论。",
            ),
        ),
        SectionSpec(
            heading="Appendix B Supplementary Questionnaire",
            paragraphs=(
                "This appendix provides supplementary questionnaire screenshots and field descriptions.",
                "Appendix figure and table materials should not change the main body structure extracted for review.",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


DOCX_TABLE_FRONT_MATTER_CASE = ReviewCaseSpec(
    case_id="docx_table_front_matter_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的表格前置区模板适配分析",
    abstract=(
        "本文围绕本科毕业论文表格前置区模板适配分析问题，分析解析链路对摘要后表格化元数据区和院系信息区的处理稳定性，"
        "并通过实验验证表格前置区提取策略相较仅解析段落规则的结构保真优势。"
    ),
    post_abstract_front_matter_tables=(
        (
            ("关键词", "本科论文初审；表格前置区；docx 解析；benchmark"),
            ("Key words", "thesis review; docx table metadata; parser stability"),
            ("学校代码", "10487"),
            ("学号", "2020123456"),
            ("学院", "计算机科学与技术学院"),
            ("专业", "软件工程"),
            ("导师组", "智能系统导师组"),
            ("学位类型", "工学学士"),
        ),
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实学校模板中摘要后元数据常放入表格单元格的情况，本文分析表格前置区对摘要边界识别和正文定位稳定性的影响。[1]",
                "研究目标是让系统在表格化关键词区、元数据区和导师组信息共存时仍能稳定保留摘要并准确切入正文。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只覆盖普通段落形式的前置区字段，而对学校代码、学位类型等位于表格单元格中的模板支持不足。[1][3]",
                "本文将当前表格前置区提取方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过按文档块顺序提取段落和表格行、关键词前缀识别和正文起点控制，提升真实学校模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注表格字段误入正文、摘要污染和章节顺序偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含表格前置区的多种学校模板，指标包括摘要保真度、正文章节识别准确率和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过表格前置区字段，并减少正文起点误判。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明表格前置区模板适配对后续论文评审质量具有基础性作用。",
                "本章也说明了局限性，包括更复杂的合并单元格与嵌套表格仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


COMPLEX_TABLE_FRONT_MATTER_CASE = ReviewCaseSpec(
    case_id="complex_table_front_matter_case",
    tags=("template_variation", "evaluation_fixture", "parser_precision"),
    title="面向本科论文初审的复杂表格前置区模板适配分析",
    abstract=(
        "本文围绕本科毕业论文复杂表格前置区模板适配分析问题，分析解析链路对合并单元格与嵌套表格元数据区的处理稳定性，"
        "并通过实验验证递归表格提取与重复单元格去重策略对真实学校模板的兼容性。"
    ),
    post_abstract_front_matter_tables=(
        TableSpec(
            rows=(
                ("关键词", "", "本科论文初审；复杂表格模板；docx 解析；benchmark"),
                ("Key words", "", "thesis review; merged cells; nested table metadata"),
                ("学校代码", "", "10487"),
                ("学号", "", "2020123456"),
                (
                    TableCellSpec(
                        nested_table_rows=(
                            ("导师组", "智能系统导师组"),
                            ("学位类型", "工学学士"),
                            ("学位授予单位", "某某大学"),
                        )
                    ),
                    "",
                    "",
                ),
            ),
            merges=(
                (0, 0, 0, 1),
                (1, 0, 1, 1),
                (2, 0, 2, 1),
                (3, 0, 3, 1),
            ),
        ),
    ),
    sections=(
        SectionSpec(
            heading="第一章 绪论",
            paragraphs=(
                "针对真实学校模板中摘要后元数据常以合并单元格和嵌套表格混排的情况，本文分析其对摘要边界识别和正文定位稳定性的影响。[1]",
                "研究目标是让系统在复杂表格化关键词区、元数据区和导师信息区共存时仍能稳定保留摘要并准确切入正文。[2]",
            ),
        ),
        SectionSpec(
            heading="第二章 已有方法比较",
            paragraphs=(
                "现有方案通常只覆盖普通段落或简单表格形式的前置区字段，而对合并单元格和嵌套表格中的学校代码、学位授予单位等模板支持不足。[1][3]",
                "本文将当前复杂表格前置区提取方案与 baseline、benchmark 文档样式进行比较，以验证适配能力。[4]",
            ),
        ),
        SectionSpec(
            heading="第三章 方法设计",
            paragraphs=(
                "本文通过按文档块顺序递归提取表格单元格内容、合并单元格重复文本去重和正文起点控制，提升真实学校模板下的结构化解析稳定性。[2][4]",
                "实验分析同时关注表格字段误入正文、摘要污染和章节顺序偏移等风险点。[5]",
            ),
        ),
        SectionSpec(
            heading="第四章 实验评估",
            paragraphs=(
                "实验评估选取包含合并单元格与嵌套表格前置区的多种学校模板，指标包括摘要保真度、正文章节识别准确率和解析成功率。[3][5]",
                "结果表明，在适当规则增强后，系统能够更稳定地跳过复杂表格前置区字段，并减少正文起点误判。[4][6]",
            ),
        ),
        SectionSpec(
            heading="第五章 结论与局限",
            paragraphs=(
                "结论部分回收研究问题、方法和实验结果，说明复杂表格前置区模板适配对后续论文评审质量具有基础性作用。",
                "本章也说明了局限性，包括页眉页脚中的表格化元数据仍需后续扩展支持。",
            ),
        ),
    ),
    references=(
        "[1] Zhang. Academic Writing Review Workflow. 2022.",
        "[2] Liu. Evidence-based Assessment for Student Papers. 2023.",
        "[3] Chen. Benchmarking Review Assistants in Education. 2024.",
        "[4] Wang. Structured Feedback for Thesis Drafts. 2023.",
        "[5] Zhao. Multi-Agent Evaluation Pipeline Design. 2024.",
        "[6] Sun. Consistency Analysis of LLM-based Review Systems. 2024.",
    ),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
)


WEAK_REVIEW_CASE = ReviewCaseSpec(
    case_id="weak_review_case",
    tags=("weak_sample", "evaluation_fixture", "research_first"),
    title="某系统设计与实现研究",
    abstract="该稿主要介绍平台页面和接口流程。",
    sections=(
        SectionSpec(
            heading="1 功能说明",
            paragraphs=(
                "系统包含上传、展示和导出按钮，界面较完整，并显著提升处理效率。",
                "目前主要完成页面和接口联调，具体细节按模块分别展示。",
            ),
        ),
        SectionSpec(
            heading="2 页面展示",
            paragraphs=(
                "本章继续展示系统截图和页面跳转效果，整体运行稳定。",
                "最后给出简单运行结果，说明系统已经可以使用。",
            ),
        ),
    ),
    references=(),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
    expected_high_severity_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
    expected_priority_first_dimension=Dimension.TOPIC_SCOPE,
    expected_issue_titles=(
        "摘要没有明确点出研究问题",
        "摘要缺少方法或结果闭环",
        "标题与摘要的一致性偏弱",
        "标题偏泛，范围边界不够具体",
        "正文前部未快速建立研究问题",
        "论证链缺少明确的验证环节",
        "缺少显式结论章节，论证收束不足",
        "参考文献数量偏少，难以支撑毕业论文评审",
        "缺少显式相关工作或文献综述部分",
        "缺少与已有方法或基线的比较意识",
        "论文没有明确交代创新点或研究贡献",
        "论文更像系统实现说明，研究深度不足",
        "章节结构不足以支撑毕业论文草稿",
        "摘要信息量不足",
        "缺少参考文献列表",
    ),
)


BOUNDARY_REVIEW_CASE = ReviewCaseSpec(
    case_id="boundary_review_case",
    tags=("debate_candidate", "boundary_sample", "weak_sample", "evaluation_fixture"),
    title="某系统设计与实现",
    abstract="本文设计了一个论文辅助系统。",
    sections=(
        SectionSpec(
            heading="1 绪论",
            paragraphs=("本文面向教学场景开发一个系统，希望改进论文初审。",),
        ),
        SectionSpec(
            heading="2 系统实现",
            paragraphs=("系统完成了上传、解析与报告输出功能，效果较好。",),
        ),
        SectionSpec(
            heading="3 总结",
            paragraphs=("本文完成了系统开发工作。",),
        ),
    ),
    references=(),
    expected_dimensions=(
        Dimension.TOPIC_SCOPE,
        Dimension.LOGIC_CHAIN,
        Dimension.LITERATURE_SUPPORT,
        Dimension.NOVELTY_DEPTH,
        Dimension.WRITING_FORMAT,
    ),
    expected_debate_dimensions=(
        Dimension.LOGIC_CHAIN,
        Dimension.NOVELTY_DEPTH,
    ),
    expected_issue_titles=(
        "摘要缺少方法或结果闭环",
        "标题与摘要的一致性偏弱",
        "标题偏泛，范围边界不够具体",
        "论证链缺少明确的验证环节",
        "参考文献数量偏少，难以支撑毕业论文评审",
        "缺少显式相关工作或文献综述部分",
        "缺少与已有方法或基线的比较意识",
        "论文更像系统实现说明，研究深度不足",
        "摘要信息量不足",
        "缺少参考文献列表",
    ),
)


DEBATE_CANDIDATE_CASE = BOUNDARY_REVIEW_CASE


REVIEW_CASE_CATALOG = (
    MINIMAL_REVIEW_CASE,
    STRONG_REVIEW_CASE,
    TOPIC_PRECISION_CASE,
    LOGIC_PRECISION_CASE,
    LITERATURE_PRECISION_CASE,
    NOVELTY_PRECISION_CASE,
    WRITING_PRECISION_CASE,
    TEMPLATE_VARIATION_CASE,
    COVER_PAGE_VARIATION_CASE,
    COVER_PAGE_TABLE_VARIATION_CASE,
    BACK_MATTER_VARIATION_CASE,
    POST_REFERENCE_BIO_VARIATION_CASE,
    CONTENTS_VARIATION_CASE,
    COMPLEX_CONTENTS_VARIATION_CASE,
    CONTENTS_HEADER_FOOTER_VARIATION_CASE,
    CAPTION_VARIATION_CASE,
    EQUATION_CAPTION_VARIATION_CASE,
    ANNOTATION_BLOCK_VARIATION_CASE,
    FOOTER_FOOTNOTE_NOISE_VARIATION_CASE,
    RUNNING_HEADER_FOOTER_METADATA_CASE,
    RUNNING_ENGLISH_HEADER_FOOTER_CASE,
    ABSTRACT_RUNNING_HEADER_VARIATION_CASE,
    REPEATED_SECTION_HEADER_NOISE_CASE,
    FOOTNOTE_BODY_VARIATION_CASE,
    DOCX_FOOTNOTE_OBJECT_VARIATION_CASE,
    DOCX_ENDNOTE_OBJECT_VARIATION_CASE,
    MIXED_NOTE_OBJECT_VARIATION_CASE,
    MULTILINE_NOTE_OBJECT_VARIATION_CASE,
    TABLE_ADJACENT_NOTE_OBJECT_VARIATION_CASE,
    REPEATED_PARENT_SECTION_HEADER_NOISE_CASE,
    REPEATED_SUBSECTION_HEADER_NOISE_CASE,
    ABBREVIATED_SECTION_HEADER_NOISE_CASE,
    UNNUMBERED_ABBREVIATED_SECTION_HEADER_NOISE_CASE,
    CONTENTS_FIELD_CODE_VARIATION_CASE,
    KEYWORD_VARIATION_CASE,
    METADATA_BLOCK_VARIATION_CASE,
    AUTHOR_INFO_VARIATION_CASE,
    APPENDIX_VARIATION_CASE,
    ENGLISH_APPENDIX_VARIATION_CASE,
    DEPARTMENT_INFO_VARIATION_CASE,
    BILINGUAL_ABSTRACT_CASE,
    DECLARATION_VARIATION_CASE,
    FRONT_MATTER_COMBO_VARIATION_CASE,
    FRONT_MATTER_MULTILINE_VARIATION_CASE,
    FRONT_MATTER_SPACING_VARIATION_CASE,
    FRONT_MATTER_TABLE_VARIATION_CASE,
    APPENDIX_CONTENTS_VARIATION_CASE,
    APPENDIX_FIGURE_LIST_VARIATION_CASE,
    DOCX_TABLE_FRONT_MATTER_CASE,
    COMPLEX_TABLE_FRONT_MATTER_CASE,
    WEAK_REVIEW_CASE,
    BOUNDARY_REVIEW_CASE,
)


def get_review_cases_by_tag(tag: str) -> tuple[ReviewCaseSpec, ...]:
    return tuple(case for case in REVIEW_CASE_CATALOG if tag in case.tags)
