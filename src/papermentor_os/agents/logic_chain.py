from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.llm import (
    LLMClient,
    LLMConfigurationError,
    LLMError,
    LLMMessage,
    MessageRole,
    ProviderConfig,
    ReviewBackend,
)
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.trace import WorkerExecutionMetadata
from papermentor_os.schemas.types import Dimension, Severity
from papermentor_os.skills.loader import SkillBundle


EXPERIMENT_HINTS = ("实验", "评估", "测试", "evaluation", "experiment", "结果分析")
CONCLUSION_HINTS = ("结论", "总结", "conclusion", "展望", "结语", "讨论")
CLAIM_HINTS = ("提升", "优化", "有效", "显著", "优于", "改善")
EVIDENCE_HINTS = ("实验", "数据", "结果", "表", "图", "[")
CLOSING_SUMMARY_HINTS = ("综上", "本文工作表明", "局限性", "后续工作", "未来工作")
MODEL_ABSTRACT_LIMIT = 260
MODEL_SECTION_COUNT = 3
MODEL_SECTION_PARAGRAPH_COUNT = 1
MODEL_PARAGRAPH_LIMIT = 130
MODEL_ANCHOR_QUOTE_LIMIT = 90
MODEL_RUBRIC_LIMIT = 650
MODEL_POLICY_LIMIT = 450
MODEL_DOMAIN_LIMIT = 350


class LogicChainLLMFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_title: str = Field(min_length=1)
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    diagnosis: str = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    evidence_anchor_id: str = Field(min_length=1)


class LogicChainLLMOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=10.0)
    findings: list[LogicChainLLMFinding] = Field(default_factory=list)


class LogicChainAgent(BaseReviewAgent):
    agent_name = "LogicChainAgent"
    skill_version = "logic-chain-rubric@0.1.0"

    def __init__(
        self,
        *,
        llm_client: LLMClient | None = None,
        llm_config: ProviderConfig | None = None,
        review_backend: ReviewBackend = ReviewBackend.RULE_ONLY,
    ) -> None:
        self.llm_client = llm_client
        self.llm_config = llm_config
        self.review_backend = review_backend
        self.last_rule_based_report: DimensionReport | None = None
        self.last_model_based_report: DimensionReport | None = None
        self.last_effective_backend = ReviewBackend.RULE_ONLY.value
        self.last_structured_output_status = "not_requested"
        self.last_fallback_used = False
        self.last_llm_provider_id: str | None = None
        self.last_llm_model_name: str | None = None
        self.last_llm_finish_reason: str | None = None
        self.last_llm_error_category: str | None = None
        self.last_llm_runtime_stats = None

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        rule_report = self._review_rule_based(paper, skill_bundle)
        self.last_rule_based_report = rule_report
        self.last_model_based_report = None
        self.last_effective_backend = self.review_backend.value
        self.last_structured_output_status = "not_requested"
        self.last_fallback_used = False
        self.last_llm_provider_id = self.llm_config.provider_id if self.llm_config is not None else None
        self.last_llm_model_name = self.llm_config.model_name if self.llm_config is not None else None
        self.last_llm_finish_reason = None
        self.last_llm_error_category = None
        self.last_llm_runtime_stats = None

        if self.review_backend == ReviewBackend.RULE_ONLY:
            return rule_report

        if self.llm_client is None or self.llm_config is None:
            self.last_structured_output_status = "configuration_error"
            raise LLMConfigurationError(
                "LogicChainAgent model review requires llm_client and llm_config."
            )

        try:
            model_report = self._review_with_llm(paper, skill_bundle)
        except LLMError as error:
            self.capture_llm_runtime_stats(error.runtime_stats)
            self.last_structured_output_status = self.classify_llm_error(error)
            self.last_llm_error_category = self.categorize_llm_error(error)
            if self.review_backend == ReviewBackend.MODEL_WITH_FALLBACK:
                self.last_fallback_used = True
                return rule_report
            raise

        self.last_model_based_report = model_report
        return model_report

    def _review_rule_based(
        self,
        paper: PaperPackage,
        skill_bundle: SkillBundle | None = None,
    ) -> DimensionReport:
        findings: list[ReviewFinding] = []
        skill_version = self.resolve_skill_version(skill_bundle)
        section_headings = [section.heading for section in paper.sections]
        heading_text = " ".join(section_headings)
        body_text = paper.body_text

        has_experiment = self._contains_any(heading_text, EXPERIMENT_HINTS) or self._contains_any(
            body_text,
            EXPERIMENT_HINTS,
        )
        has_conclusion = self._contains_any(heading_text, CONCLUSION_HINTS) or self._contains_any(
            body_text[-600:],
            CLOSING_SUMMARY_HINTS,
        )
        has_claim = self._contains_any(body_text, CLAIM_HINTS)
        has_evidence = self._contains_any(body_text, EVIDENCE_HINTS)

        if not has_experiment:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="论证链缺少明确的验证环节",
                    diagnosis="当前章节或正文里没有清晰的实验、评估或结果分析段落，论证停留在方案描述层。",
                    why_it_matters="没有验证环节，评审者无法判断方法是否真的解决了前文提出的问题。",
                    next_action="补一章或一节专门说明实验设计、评价指标、对比方式和关键结果。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[-1].section_id if paper.sections else "title",
                        location_label="章节结构",
                        quote="未识别到实验/评估/结果分析类章节标题。",
                    ),
                )
            )

        if has_claim and not has_evidence:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="正文存在结论性表述，但证据支撑不足",
                    diagnosis="正文出现了效果判断或价值判断，但缺少与之配套的数据、图表、实验或引用支撑。",
                    why_it_matters="claim 和 evidence 失配会直接削弱论文说服力，也是导师初审最敏感的问题之一。",
                    next_action="把关键结论逐条绑定到实验结果、数据指标、图表或明确引用，不要只保留主观判断句。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].paragraphs[0].anchor_id if paper.sections and paper.sections[0].paragraphs else "title",
                        location_label="正文论断",
                        quote=body_text[:120] or paper.title,
                    ),
                )
            )

        if not has_conclusion:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="缺少显式结论章节，论证收束不足",
                    diagnosis="章节结构中未识别到结论或总结部分，整体论证缺少回收研究问题与结果的闭环。",
                    why_it_matters="没有结论章节，前文的分析与结果就难以被整理成明确结论，也不利于回答研究问题。",
                    next_action="增加结论章节，集中回收研究问题、核心结果、局限性和后续工作。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[-1].section_id if paper.sections else "title",
                        location_label="章节尾部",
                        quote=section_headings[-1] if section_headings else paper.title,
                    ),
                )
            )

        score = 8.5
        for finding in findings:
            if finding.severity == Severity.HIGH:
                score -= 2.0
            elif finding.severity == Severity.MEDIUM:
                score -= 1.0
            else:
                score -= 0.5
        score = max(score, 1.0)

        summary = "论证链条有基础结构，但验证和结论闭环仍需补强。"
        if not findings:
            summary = "逻辑与论证链路维度未发现明显高优先级问题。"

        return DimensionReport(
            dimension=Dimension.LOGIC_CHAIN,
            score=score,
            summary=summary,
            findings=findings,
            debate_used=False,
        )

    def _review_with_llm(
        self,
        paper: PaperPackage,
        skill_bundle: SkillBundle | None = None,
    ) -> DimensionReport:
        if self.llm_client is None or self.llm_config is None:
            raise LLMConfigurationError(
                "LogicChainAgent model review requires llm_client and llm_config."
            )

        skill_version = self.resolve_skill_version(skill_bundle)
        anchor_map = self._build_anchor_map(paper)
        structured_response = self.llm_client.generate_structured(
            self._build_model_messages(paper, skill_bundle, anchor_map),
            LogicChainLLMOutput,
            self.llm_config,
        )
        self.last_structured_output_status = "parsed"
        self.last_llm_provider_id = structured_response.raw.provider_id
        self.last_llm_model_name = structured_response.raw.model_name
        self.last_llm_finish_reason = structured_response.raw.finish_reason
        self.last_llm_error_category = None
        self.capture_llm_runtime_stats(structured_response.raw.runtime_stats)

        findings: list[ReviewFinding] = []
        for finding in structured_response.parsed.findings:
            anchor = anchor_map.get(finding.evidence_anchor_id)
            if anchor is None:
                raise LLMConfigurationError(
                    f"LogicChainAgent received unknown evidence anchor '{finding.evidence_anchor_id}'."
                )
            findings.append(
                ReviewFinding(
                    dimension=Dimension.LOGIC_CHAIN,
                    issue_title=finding.issue_title,
                    severity=finding.severity,
                    confidence=finding.confidence,
                    evidence_anchor=anchor,
                    diagnosis=finding.diagnosis,
                    why_it_matters=finding.why_it_matters,
                    next_action=finding.next_action,
                    source_agent=self.agent_name,
                    source_skill_version=skill_version,
                )
            )

        return DimensionReport(
            dimension=Dimension.LOGIC_CHAIN,
            score=structured_response.parsed.score,
            summary=structured_response.parsed.summary,
            findings=findings,
            debate_used=False,
        )

    def _build_model_messages(
        self,
        paper: PaperPackage,
        skill_bundle: SkillBundle | None,
        anchor_map: dict[str, EvidenceAnchor],
    ) -> list[LLMMessage]:
        rubric_text = self._truncate_text(
            "\n".join(
                skill.body for skill in (skill_bundle.rubric_skills if skill_bundle else []) if skill.body
            ),
            MODEL_RUBRIC_LIMIT,
        )
        policy_text = self._truncate_text(
            "\n".join(
                skill.body for skill in (skill_bundle.policy_skills if skill_bundle else []) if skill.body
            ),
            MODEL_POLICY_LIMIT,
        )
        domain_text = self._truncate_text(
            "\n".join(
                skill.body for skill in (skill_bundle.domain_skills if skill_bundle else []) if skill.body
            ),
            MODEL_DOMAIN_LIMIT,
        )

        prompt_payload = {
            "paper": {
                "title": paper.title,
                "abstract": self._truncate_text(
                    paper.abstract or "未识别到摘要内容。",
                    MODEL_ABSTRACT_LIMIT,
                ),
                "sections": [
                    {
                        "heading": section.heading,
                        "paragraphs": [
                            {
                                "anchor_id": paragraph.anchor_id,
                                "text": self._truncate_text(paragraph.text, MODEL_PARAGRAPH_LIMIT),
                            }
                            for paragraph in section.paragraphs[:MODEL_SECTION_PARAGRAPH_COUNT]
                        ],
                    }
                    for section in paper.sections[:MODEL_SECTION_COUNT]
                ],
            },
            "allowed_anchors": [
                {
                    "anchor_id": anchor.anchor_id,
                    "location_label": anchor.location_label,
                    "quote": self._truncate_text(anchor.quote, MODEL_ANCHOR_QUOTE_LIMIT),
                }
                for anchor in anchor_map.values()
            ],
        }
        if rubric_text:
            prompt_payload["rubric"] = rubric_text
        if policy_text:
            prompt_payload["policies"] = policy_text
        if domain_text:
            prompt_payload["domain_rules"] = domain_text
        return [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "你是 PaperMentor OS 的 LogicChainAgent。"
                    "只评估“逻辑与论证链路”维度，不要扩展到其他维度。"
                    "优先检查研究问题、方法、验证和结论是否构成闭环。"
                    "不要输出代写内容，所有 finding 都必须引用给定的 evidence_anchor_id。"
                    "保持输出精炼，只根据标题、摘要和关键章节判断主论证链。"
                ),
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=(
                    "请基于以下论文上下文输出结构化评审结果。"
                    "如果没有明显问题，findings 可为空，但 summary 和 score 仍必须给出。\n"
                    f"{json.dumps(prompt_payload, ensure_ascii=False, separators=(',', ':'))}"
                ),
            ),
        ]

    def _build_anchor_map(self, paper: PaperPackage) -> dict[str, EvidenceAnchor]:
        anchors: dict[str, EvidenceAnchor] = {
            "title": EvidenceAnchor(
                anchor_id="title",
                location_label="标题",
                quote=paper.title,
            ),
            "abstract": EvidenceAnchor(
                anchor_id="abstract",
                location_label="摘要",
                quote=paper.abstract or "未识别到摘要内容。",
            ),
        }

        for section in paper.sections[:MODEL_SECTION_COUNT]:
            anchors[section.section_id] = EvidenceAnchor(
                anchor_id=section.section_id,
                location_label="章节结构",
                quote=section.heading,
            )
            for paragraph in section.paragraphs[:MODEL_SECTION_PARAGRAPH_COUNT]:
                anchors[paragraph.anchor_id] = EvidenceAnchor(
                    anchor_id=paragraph.anchor_id,
                    location_label=section.heading,
                    quote=paragraph.text[:160],
                )
        return anchors

    def _truncate_text(self, text: str, limit: int) -> str:
        normalized = " ".join(text.split())
        if limit <= 0 or len(normalized) <= limit:
            return normalized
        return normalized[: max(limit - 1, 0)].rstrip() + "…"

    def build_execution_metadata(self) -> WorkerExecutionMetadata:
        return self.build_llm_execution_metadata()

    def _contains_any(self, text: str, hints: tuple[str, ...]) -> bool:
        lowered = text.lower()
        return any(hint.lower() in lowered for hint in hints)

    def _finding(
        self,
        *,
        skill_version: str,
        severity: Severity,
        issue_title: str,
        diagnosis: str,
        why_it_matters: str,
        next_action: str,
        evidence_anchor: EvidenceAnchor,
    ) -> ReviewFinding:
        return ReviewFinding(
            dimension=Dimension.LOGIC_CHAIN,
            issue_title=issue_title,
            severity=severity,
            confidence=0.8 if severity == Severity.HIGH else 0.72,
            evidence_anchor=evidence_anchor,
            diagnosis=diagnosis,
            why_it_matters=why_it_matters,
            next_action=next_action,
            source_agent=self.agent_name,
            source_skill_version=skill_version,
        )
