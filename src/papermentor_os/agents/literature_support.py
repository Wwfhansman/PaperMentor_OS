from __future__ import annotations

import re

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.types import Dimension, Severity
from papermentor_os.skills.loader import SkillBundle


CITATION_PATTERN = re.compile(r"\[(\d+)\]|（[^）]*\d{4}[^）]*）|\([^)]*\d{4}[^)]*\)")
RELATED_WORK_HINTS = ("相关工作", "文献综述", "研究现状", "related work", "literature review")
BASELINE_HINTS = ("baseline", "对比", "比较", "benchmark", "sota")


class LiteratureSupportAgent(BaseReviewAgent):
    agent_name = "LiteratureSupportAgent"
    skill_version = "literature-support-rubric@0.1.0"

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        findings: list[ReviewFinding] = []
        skill_version = self.resolve_skill_version(skill_bundle)
        body_text = paper.body_text
        section_headings = [section.heading for section in paper.sections]
        has_related_work = self._contains_any(" ".join(section_headings), RELATED_WORK_HINTS)
        citation_count = len(CITATION_PATTERN.findall(body_text))
        reference_count = len(paper.references)
        has_baseline_discussion = self._contains_any(body_text, BASELINE_HINTS)

        if reference_count < 5:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="参考文献数量偏少，难以支撑毕业论文评审",
                    diagnosis="当前识别到的参考文献数量较少，文献基础看起来还不足以支撑完整的相关工作分析。",
                    why_it_matters="文献支撑不足会直接影响选题价值判断、方法对比和创新性论证。",
                    next_action="优先补充与研究问题直接相关的核心论文、方法对比文献和近年代表性工作，再重写相关工作部分。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="references",
                        location_label="参考文献",
                        quote=f"当前仅识别到 {reference_count} 条参考文献。",
                    ),
                )
            )

        if not has_related_work:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="缺少显式相关工作或文献综述部分",
                    diagnosis="章节结构中没有清晰的相关工作、文献综述或研究现状部分，文献梳理不够显式。",
                    why_it_matters="没有专门的文献支撑章节，会让评审者难以判断论文是否完成了必要的领域定位。",
                    next_action="增加“相关工作”或“研究现状”小节，按研究方向或方法类别梳理已有工作与论文定位。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].section_id if paper.sections else "title",
                        location_label="章节结构",
                        quote="未识别到相关工作/文献综述类章节标题。",
                    ),
                )
            )

        if reference_count > 0 and citation_count == 0:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="正文缺少显式引用，文献没有进入论证链路",
                    diagnosis="虽然存在参考文献列表，但正文中没有识别到稳定的引用痕迹，文献未真正参与论证。",
                    why_it_matters="文献如果只出现在文末而不进入正文论证，就无法支撑问题定义、方法选择和结果比较。",
                    next_action="在问题背景、方法选择和结果比较处补充明确引用，让关键论断都能回到文献来源。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="references",
                        location_label="正文与参考文献关系",
                        quote="识别到参考文献列表，但正文未识别到引用标记。",
                    ),
                )
            )

        if not has_baseline_discussion:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="缺少与已有方法或基线的比较意识",
                    diagnosis="正文没有明显讨论已有方法、对比对象或 benchmark，文献支撑更像罗列而不是比较分析。",
                    why_it_matters="计算机专业本科毕业论文通常需要说明自己的方法相对已有方案的定位和差异。",
                    next_action="在相关工作或实验分析中补充对比基线，说明已有方法做法、局限以及本文方案的差异点。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].paragraphs[0].anchor_id if paper.sections and paper.sections[0].paragraphs else "title",
                        location_label="正文分析",
                        quote=body_text[:120] or paper.title,
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

        summary = "文献支撑有基础框架，但相关工作梳理和引用进入论证链的程度仍然不足。"
        if not findings:
            summary = "文献支撑维度未发现明显高优先级问题。"

        return DimensionReport(
            dimension=Dimension.LITERATURE_SUPPORT,
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
            dimension=Dimension.LITERATURE_SUPPORT,
            issue_title=issue_title,
            severity=severity,
            confidence=0.82 if severity == Severity.HIGH else 0.74,
            evidence_anchor=evidence_anchor,
            diagnosis=diagnosis,
            why_it_matters=why_it_matters,
            next_action=next_action,
            source_agent=self.agent_name,
            source_skill_version=skill_version,
        )
