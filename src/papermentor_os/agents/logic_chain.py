from __future__ import annotations

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.types import Dimension, Severity
from papermentor_os.skills.loader import SkillBundle


EXPERIMENT_HINTS = ("实验", "评估", "测试", "evaluation", "experiment", "结果分析")
CONCLUSION_HINTS = ("结论", "总结", "conclusion")
CLAIM_HINTS = ("提升", "优化", "有效", "显著", "优于", "改善")
EVIDENCE_HINTS = ("实验", "数据", "结果", "表", "图", "[")


class LogicChainAgent(BaseReviewAgent):
    agent_name = "LogicChainAgent"
    skill_version = "logic-chain-rubric@0.1.0"

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        findings: list[ReviewFinding] = []
        skill_version = self.resolve_skill_version(skill_bundle)
        section_headings = [section.heading for section in paper.sections]
        heading_text = " ".join(section_headings)
        body_text = paper.body_text

        has_experiment = self._contains_any(heading_text, EXPERIMENT_HINTS) or self._contains_any(
            body_text,
            EXPERIMENT_HINTS,
        )
        has_conclusion = self._contains_any(heading_text, CONCLUSION_HINTS)
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
