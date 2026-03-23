import json

from papermentor_os.agents.topic_scope import TopicScopeAgent
from papermentor_os.llm import FakeLLMProvider, LLMClient, ProviderConfig, ReviewBackend
from papermentor_os.schemas.paper import PaperPackage, Paragraph, PaperReference, Section
from papermentor_os.schemas.types import Dimension, Discipline, PaperStage


def _build_paper(*, abstract: str) -> PaperPackage:
    return PaperPackage(
        paper_id="paper-001",
        title="面向本科论文初审的多智能体评审系统设计与实现",
        discipline=Discipline.COMPUTER_SCIENCE,
        stage=PaperStage.DRAFT,
        abstract=abstract,
        sections=[
            Section(
                section_id="sec-1",
                heading="1 绪论",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-1",
                        anchor_id="sec-1-p-1",
                        text="本文针对本科论文初审反馈滞后的问题，提出一套结构化评审系统。",
                    ),
                    Paragraph(
                        paragraph_id="p-2",
                        anchor_id="sec-1-p-2",
                        text="研究目标是提高高优先级问题定位效率，并验证系统化评审流程是否有效。",
                    ),
                ],
            ),
            Section(
                section_id="sec-2",
                heading="2 方法设计",
                level=1,
                paragraphs=[
                    Paragraph(
                        paragraph_id="p-3",
                        anchor_id="sec-2-p-1",
                        text="系统由 ChiefReviewer、五个维度 worker、evidence ledger 和 debate judge 构成。",
                    ),
                ],
            ),
        ],
        references=[
            PaperReference(
                reference_id="ref-1",
                anchor_id="ref-1",
                raw_text="[1] Zhang. Structured Review Workflow. 2024.",
            )
        ],
    )


def _llm_config() -> ProviderConfig:
    return ProviderConfig(
        provider_id="fake",
        model_name="topic-scope-poc",
        prompt_char_budget=4000,
    )


def test_topic_scope_agent_can_use_model_backend() -> None:
    provider = FakeLLMProvider(
        responses=[
            json.dumps(
                {
                    "summary": "选题对象明确，但摘要中的研究问题还可以更直接。",
                    "score": 7.6,
                    "findings": [
                        {
                            "issue_title": "摘要中的研究问题表述还不够直接",
                            "severity": "medium",
                            "confidence": 0.86,
                            "diagnosis": "摘要提到了系统目标，但对核心研究问题的句式还不够集中。",
                            "why_it_matters": "研究问题表达不够直接，会削弱题目、摘要和正文前部之间的对齐度。",
                            "next_action": "在摘要前半段单独用一句话明确写出要解决的教学反馈效率问题。",
                            "evidence_anchor_id": "abstract",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        ]
    )
    agent = TopicScopeAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_ONLY,
    )

    report = agent.review(
        _build_paper(
            abstract=(
                "本文提出一套面向本科论文初审的多智能体评审系统，"
                "用于提升导师在草稿阶段的问题定位效率，并通过实验评估验证系统效果。"
            )
        )
    )

    assert report.dimension == Dimension.TOPIC_SCOPE
    assert report.summary == "选题对象明确，但摘要中的研究问题还可以更直接。"
    assert report.findings[0].issue_title == "摘要中的研究问题表述还不够直接"
    assert report.findings[0].evidence_anchor.anchor_id == "abstract"
    assert report.findings[0].source_skill_version == "topic-clarity-rubric@0.1.0"
    assert agent.last_model_based_report is not None


def test_topic_scope_agent_falls_back_to_rule_backend_on_invalid_model_output() -> None:
    provider = FakeLLMProvider(responses=["not valid json"])
    agent = TopicScopeAgent(
        llm_client=LLMClient(provider),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_WITH_FALLBACK,
    )

    report = agent.review(_build_paper(abstract=""))
    issue_titles = {finding.issue_title for finding in report.findings}

    assert "摘要缺失，研究问题无法快速定位" in issue_titles
    assert agent.last_rule_based_report is not None
    assert agent.last_model_based_report is None


def test_topic_scope_agent_builds_compact_model_messages() -> None:
    agent = TopicScopeAgent(
        llm_client=LLMClient(FakeLLMProvider()),
        llm_config=_llm_config(),
        review_backend=ReviewBackend.MODEL_ONLY,
    )
    paper = _build_paper(
        abstract=(
            "本文提出一套面向本科论文初审的多智能体评审系统，"
            + "用于提升导师在草稿阶段的问题定位效率，并通过实验评估验证系统效果。" * 20
        )
    )

    messages = agent._build_model_messages(paper, None, agent._build_anchor_map(paper))

    assert len(messages) == 2
    assert len(messages[0].content) < 180
    assert "绪论" in messages[1].content
    assert messages[1].content.count('"heading"') == 1
    assert len(messages[1].content) < 1200
