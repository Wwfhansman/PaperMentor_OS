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
from papermentor_os.schemas.paper import PaperPackage, Paragraph
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.trace import WorkerExecutionMetadata
from papermentor_os.schemas.types import Dimension, Severity
from papermentor_os.skills.loader import SkillBundle

PROBLEM_HINTS = ("问题", "目标", "本文", "提出", "研究")
METHOD_HINTS = ("设计", "实现", "算法", "模型", "框架", "构建", "分析")
RESULT_HINTS = ("结果", "验证", "评估", "性能", "效果", "稳定性")
MODEL_ABSTRACT_LIMIT = 260
MODEL_SECTION_COUNT = 3
MODEL_SECTION_PARAGRAPH_COUNT = 1
MODEL_PARAGRAPH_LIMIT = 130
MODEL_ANCHOR_QUOTE_LIMIT = 90
MODEL_RUBRIC_LIMIT = 650
MODEL_POLICY_LIMIT = 450
MODEL_DOMAIN_LIMIT = 350


class WritingFormatLLMFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_title: str = Field(min_length=1)
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    diagnosis: str = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    evidence_anchor_id: str = Field(min_length=1)


class WritingFormatLLMOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=10.0)
    findings: list[WritingFormatLLMFinding] = Field(default_factory=list)


class WritingFormatAgent(BaseReviewAgent):
    agent_name = "WritingFormatAgent"
    skill_version = "writing-format-rubric@0.1.0"

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
                "WritingFormatAgent model review requires llm_client and llm_config."
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

        if len(paper.sections) < 3:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="章节结构不足以支撑毕业论文草稿",
                    diagnosis="当前正文章节数量偏少，结构看起来还不像一篇已进入草稿阶段的完整毕业论文。",
                    why_it_matters="章节骨架不完整会直接影响导师对研究设计、实验安排和结论完整性的判断。",
                    next_action="先补齐至少“问题背景/方法设计/实验或实现/结论”这类核心章节，再进入细节润色。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].section_id if paper.sections else "title",
                        location_label="论文整体结构",
                        quote=f"当前仅识别到 {len(paper.sections)} 个正文章节。",
                    ),
                )
            )

        abstract_length = len(paper.abstract.replace(" ", ""))
        has_problem_signal = self._contains_any(paper.abstract, PROBLEM_HINTS)
        has_method_signal = self._contains_any(paper.abstract, METHOD_HINTS)
        has_result_signal = self._contains_any(paper.abstract, RESULT_HINTS)
        abstract_is_compact_but_complete = (
            abstract_length >= 50 and has_problem_signal and has_method_signal and has_result_signal
        )
        if abstract_length < 120 and not abstract_is_compact_but_complete:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="摘要信息量不足",
                    diagnosis="摘要篇幅较短，难以同时交代研究问题、方法与结果。",
                    why_it_matters="摘要是导师和评审快速判断论文成熟度的入口，信息不完整会削弱整体可信度。",
                    next_action="把摘要补成“问题背景-方法-结果/结论”的三段式或紧凑四句式表达。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="abstract",
                        location_label="摘要",
                        quote=paper.abstract or "摘要内容缺失",
                    ),
                )
            )

        if not paper.references:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="缺少参考文献列表",
                    diagnosis="解析结果中未识别到参考文献部分。",
                    why_it_matters="没有参考文献会让论文在学术规范和文献支撑两方面同时失分。",
                    next_action="补充规范的参考文献章节，并确保正文中的关键论断可以追溯到文献来源。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="references",
                        location_label="参考文献",
                        quote="未识别到参考文献条目。",
                    ),
                )
            )

        longest_paragraph = self._find_longest_paragraph(paper)
        if longest_paragraph and len(longest_paragraph.text) > 240:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.LOW,
                    issue_title="存在过长段落，影响可读性",
                    diagnosis="部分段落信息密度高且缺少拆分，阅读时不易快速定位主句与支撑句。",
                    why_it_matters="过长段落会增加阅读负担，也会掩盖真正重要的论证节点。",
                    next_action="将长段落拆成“结论句 + 解释句 + 证据句”结构，并给关键论点单独成段。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=longest_paragraph.anchor_id,
                        location_label="正文段落",
                        quote=longest_paragraph.text[:120],
                    ),
                )
            )

        score = 9.0
        for finding in findings:
            if finding.severity == Severity.HIGH:
                score -= 2.0
            elif finding.severity == Severity.MEDIUM:
                score -= 1.0
            else:
                score -= 0.5
        score = max(score, 1.0)

        summary = "写作与格式总体可读，但仍存在影响评审效率的规范性问题。"
        if not findings:
            summary = "写作与格式维度未发现明显的高优先级问题，结构基础较完整。"

        return DimensionReport(
            dimension=Dimension.WRITING_FORMAT,
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
                "WritingFormatAgent model review requires llm_client and llm_config."
            )

        skill_version = self.resolve_skill_version(skill_bundle)
        anchor_map = self._build_anchor_map(paper)
        structured_response = self.llm_client.generate_structured(
            self._build_model_messages(paper, skill_bundle, anchor_map),
            WritingFormatLLMOutput,
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
                    f"WritingFormatAgent received unknown evidence anchor '{finding.evidence_anchor_id}'."
                )
            findings.append(
                ReviewFinding(
                    dimension=Dimension.WRITING_FORMAT,
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
            dimension=Dimension.WRITING_FORMAT,
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
                    paper.abstract or "摘要内容缺失",
                    MODEL_ABSTRACT_LIMIT,
                ),
                "section_count": len(paper.sections),
                "reference_count": len(paper.references),
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
                    "你是 PaperMentor OS 的 WritingFormatAgent。"
                    "只评估“写作与格式规范”维度，不要扩展到其他维度。"
                    "优先检查摘要完整性、结构规范、参考文献和可读性问题。"
                    "不要输出代写内容，所有 finding 都必须引用给定的 evidence_anchor_id。"
                    "保持输出精炼，只根据摘要、章节结构和关键段落判断格式与写作质量。"
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
                quote=paper.abstract or "摘要内容缺失",
            ),
            "references": EvidenceAnchor(
                anchor_id="references",
                location_label="参考文献",
                quote=f"当前识别到 {len(paper.references)} 条参考文献。",
            ),
        }
        for section in paper.sections[:MODEL_SECTION_COUNT]:
            anchors[section.section_id] = EvidenceAnchor(
                anchor_id=section.section_id,
                location_label="论文整体结构",
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

    def _find_longest_paragraph(self, paper: PaperPackage) -> Paragraph | None:
        paragraphs = list(paper.iter_body_paragraphs())
        if not paragraphs:
            return None
        return max(paragraphs, key=lambda paragraph: len(paragraph.text))

    def _contains_any(self, text: str, hints: tuple[str, ...]) -> bool:
        return any(hint in text for hint in hints)

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
            dimension=Dimension.WRITING_FORMAT,
            issue_title=issue_title,
            severity=severity,
            confidence=0.8 if severity != Severity.LOW else 0.7,
            evidence_anchor=evidence_anchor,
            diagnosis=diagnosis,
            why_it_matters=why_it_matters,
            next_action=next_action,
            source_agent=self.agent_name,
            source_skill_version=skill_version,
        )
