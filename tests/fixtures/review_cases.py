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
    title: str
    abstract: str
    sections: tuple[SectionSpec, ...]
    references: tuple[str, ...]
    expected_dimensions: tuple[Dimension, ...]
    expected_debate_dimensions: tuple[Dimension, ...] = ()


MINIMAL_REVIEW_CASE = ReviewCaseSpec(
    case_id="minimal_review_case",
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


DEBATE_CANDIDATE_CASE = ReviewCaseSpec(
    case_id="debate_candidate_case",
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
)

