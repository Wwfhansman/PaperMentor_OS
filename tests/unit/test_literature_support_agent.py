import json

from papermentor_os.agents.literature_support import LiteratureSupportAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _build_paper(*, references: list[PaperReference] | None = None) -> PaperPackage:
    return PaperPackage(
        paper_id="literature-paper-001",
        title="面向本科论文初审的文献支撑审查框架设计",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
        abstract=(
            "本文提出一套面向本科论文初审的文献支撑审查框架，"
            "用于分析相关工作覆盖、正文引用和方法比较是否充分。"
        ),
        sections=[
            Section(
                section_id="sec-1",
                heading="1 绪论",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-1",
                        anchor_id="sec-1-p-1",
                        text="现有研究主要关注写作辅助和自动评分，但对证据约束和结构化评审讨论不足。[1]",
                    ),
                    Paragraph(
                        paragraph_id="p-2",
                        anchor_id="sec-1-p-2",
                        text="本文目标是分析文献支撑是否真正进入问题定义、方法选择和结果比较链路。[2]",
                    ),
                ],
            ),
            Section(
                section_id="sec-2",
                heading="2 相关工作",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-3",
                        anchor_id="sec-2-p-1",
                        text="本文对比已有多智能体评审方案、写作辅助工具和 benchmark 体系，并分析各自局限。[1][3]",
                    ),
                ],
            ),
            Section(
                section_id="sec-3",
                heading="3 方法设计",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-4",
                        anchor_id="sec-3-p-1",
                        text="系统结合 evidence ledger 与 benchmark，对已有方案做差异化比较和定位。",
                    ),
                ],
            ),
        ],
        references=references
        or [
            PaperReference(
                reference_id=f"ref-{index}",
                anchor_id=f"ref-{index}",
                raw_text=f"[{index}] Ref {index}.",
            )
            for index in range(1, 6)
        ],
    )


def _llm_config() -> ProviderConfig:
    return ProviderConfig(
        provider_id="fake",
        model_name="literature-support-poc",
        prompt_char_budget=5000,
    )


def test_literature_support_agent_can_use_model_backend() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "文献基础存在，但相关工作的比较分析还可以更集中。",
                    "score": 7.5,
                    "findings": [
                        {
                            "issue_title": "相关工作对基线差异的比较还不够集中",
                            "severity": "medium",
                            "confidence": 0.85,
                            "diagnosis": "当前已经出现相关工作和对比意识，但对已有方案差异的归纳还不够集中。",
                            "why_it_matters": "如果文献只是罗列而没有比较，读者很难判断本文方案的定位。",
                            "next_action": "把已有方案按方法类别整理，并单独总结本文与主要基线的差异。",
                            "evidence_anchor_id": "sec-2-p-1",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    agent = LiteratureSupportAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_ONLY,
    )

    report = agent.review(_build_paper())

    assert report.dimension == Dimension.LITERATURE_SUPPORT
    assert report.summary == "文献基础存在，但相关工作的比较分析还可以更集中。"
    assert report.findings[0].issue_title == "相关工作对基线差异的比较还不够集中"
    assert report.findings[0].evidence_anchor.anchor_id == "sec-2-p-1"
    assert report.findings[0].source_skill_version == "literature-support-rubric@0.1.0"
    assert agent.last_model_based_report is not None


def test_literature_support_agent_falls_back_to_rule_backend_on_invalid_model_output() -> None:
    provider = FakeLLMProvider(responses=["not valid json"])
    agent = LiteratureSupportAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )
    paper = _build_paper(
        references=[
            PaperReference(
                reference_id="ref-1",
                anchor_id="ref-1",
                raw_text="[1] Only one reference.",
            )
        ]
    ).model_copy(
        update={
            "sections": [
                Section(
                    section_id="sec-1",
                    heading="1 绪论",
                    level=1,
                    paragraphs=[
                        Paragraph(
                            paragraph_id="p-1",
                            anchor_id="sec-1-p-1",
                            text="本文提出一套评审框架，用于提升反馈效率。",
                        )
                    ],
                )
            ]
        }
    )

    report = agent.review(paper)
    issue_titles = {finding.issue_title for finding in report.findings}

    assert "参考文献数量偏少，难以支撑毕业论文评审" in issue_titles
    assert agent.last_rule_based_report is not None
    assert agent.last_model_based_report is None


def test_literature_support_agent_builds_compact_model_messages() -> None:
    agent = LiteratureSupportAgent(
        llm_client=LLMClient(FakeLLMProvider()),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_ONLY,
    )
    paper = _build_paper(
        references=[
            PaperReference(
                reference_id=f"ref-{index}",
                anchor_id=f"ref-{index}",
                raw_text=(f"[{index}] Reference {index}. " * 12).strip(),
            )
            for index in range(1, 8)
        ]
    ).model_copy(
        update={
            "abstract": _build_paper().abstract * 12,
        }
    )

    messages = agent._build_model_messages(paper, None, agent._build_anchor_map(paper))

    assert len(messages) == 2
    assert len(messages[0].content) < 210
    assert messages[1].content.count('"heading"') == 2
    assert messages[1].content.count("Reference") <= 6
    assert len(messages[1].content) < 1800
