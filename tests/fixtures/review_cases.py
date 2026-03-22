from __future__ import annotations

from dataclasses import dataclass

from papermentor_os.schemas.types import Dimension


@dataclass(frozen=True)
class SectionSpec:
    heading: str
    paragraphs: tuple[str, ...]


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
    post_abstract_front_matter: tuple[str, ...] = ()
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
    CONTENTS_VARIATION_CASE,
    WEAK_REVIEW_CASE,
    BOUNDARY_REVIEW_CASE,
)


def get_review_cases_by_tag(tag: str) -> tuple[ReviewCaseSpec, ...]:
    return tuple(case for case in REVIEW_CASE_CATALOG if tag in case.tags)
