from __future__ import annotations

from papermentor_os.agents.base import BaseReviewAgent
from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport, EvidenceAnchor, ReviewFinding
from papermentor_os.schemas.types import Dimension, Severity
from papermentor_os.skills.loader import SkillBundle


NOVELTY_HINTS = ("创新", "novel", "new", "改进", "提出", "贡献")
LIMITATION_HINTS = ("局限", "不足", "future work", "后续工作")
DEPTH_HINTS = ("实验", "评估", "分析", "对比", "消融", "ablation")
SYSTEM_ONLY_HINTS = ("设计与实现", "系统实现", "系统设计", "平台搭建")
CONTRIBUTION_COMPARISON_HINTS = ("相较", "相对于", "优于", "区别于", "差异", "定位", "相比")


class NoveltyDepthAgent(BaseReviewAgent):
    agent_name = "NoveltyDepthAgent"
    skill_version = "novelty-depth-rubric@0.1.0"

    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        findings: list[ReviewFinding] = []
        skill_version = self.resolve_skill_version(skill_bundle)
        abstract = paper.abstract or ""
        body_text = paper.body_text
        heading_text = " ".join(section.heading for section in paper.sections)
        combined_text = " ".join((paper.title, abstract, body_text[:2000]))

        mentions_novelty = self._contains_any(combined_text, NOVELTY_HINTS)
        has_depth_signals = self._contains_any(combined_text, DEPTH_HINTS)
        has_limitations = self._contains_any(combined_text, LIMITATION_HINTS)
        system_only_title = self._contains_any(paper.title, SYSTEM_ONLY_HINTS)
        expresses_comparative_contribution = self._contains_any(combined_text, CONTRIBUTION_COMPARISON_HINTS)
        has_contribution_expression = mentions_novelty or (
            expresses_comparative_contribution and has_depth_signals
        )

        if not has_contribution_expression:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="论文没有明确交代创新点或研究贡献",
                    diagnosis="当前标题、摘要和正文前部没有清楚说明论文相对已有工作的新增价值或研究贡献。",
                    why_it_matters="如果创新点不明确，评审者会更倾向于把论文理解为普通项目总结，而不是研究型毕业论文。",
                    next_action="单独增加“创新点/贡献”表述，明确说明本文相对已有方法新增了什么、改善了什么、解决了什么限制。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="abstract" if abstract else "title",
                        location_label="标题与摘要",
                        quote=abstract[:120] if abstract else paper.title,
                    ),
                )
            )

        if system_only_title and not has_depth_signals:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.HIGH,
                    issue_title="论文更像系统实现说明，研究深度不足",
                    diagnosis="题目和正文更强调系统设计与实现，但缺少方法比较、机制分析或深入验证，研究深度偏弱。",
                    why_it_matters="V1 目标是本科毕业论文评审，不是单纯验收功能实现；没有研究深度会直接影响创新性判断。",
                    next_action="补充方法选择依据、关键设计权衡、实验比较或误差分析，把工作从“做出来”推进到“论证清楚为什么这样做”。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id="title",
                        location_label="标题",
                        quote=paper.title,
                    ),
                )
            )

        if has_contribution_expression and not has_depth_signals:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.MEDIUM,
                    issue_title="宣称有创新，但缺少足够研究深度支撑",
                    diagnosis="论文中存在创新或改进表述，但缺少实验、分析或对比来支撑这些主张。",
                    why_it_matters="创新性判断不能只靠口头声明，必须通过方法分析和验证过程建立可信度。",
                    next_action="把创新点逐条对应到实验结果、对比分析或机制解释，避免只在摘要里声明“有创新”。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[0].paragraphs[0].anchor_id if paper.sections and paper.sections[0].paragraphs else "title",
                        location_label="正文前部",
                        quote=body_text[:120] or paper.title,
                    ),
                )
            )

        if not has_limitations:
            findings.append(
                self._finding(
                    skill_version=skill_version,
                    severity=Severity.LOW,
                    issue_title="缺少局限性或后续工作反思",
                    diagnosis="正文中没有明显讨论当前方案的局限、适用边界或后续工作方向。",
                    why_it_matters="对局限性的主动说明能提高研究表达的成熟度，也有助于导师判断作者是否真正理解自己的工作边界。",
                    next_action="在结论中补充局限性和后续工作，说明当前方案在哪些条件下仍然不足。",
                    evidence_anchor=EvidenceAnchor(
                        anchor_id=paper.sections[-1].section_id if paper.sections else "title",
                        location_label="结尾部分",
                        quote=heading_text.split()[-1] if heading_text else paper.title,
                    ),
                )
            )

        score = 8.0
        for finding in findings:
            if finding.severity == Severity.HIGH:
                score -= 2.0
            elif finding.severity == Severity.MEDIUM:
                score -= 1.0
            else:
                score -= 0.5
        score = max(score, 1.0)

        summary = "创新性与研究深度已有初步表达，但还需要更清晰的贡献界定和深度支撑。"
        if not findings:
            summary = "创新性与研究深度维度未发现明显高优先级问题。"

        return DimensionReport(
            dimension=Dimension.NOVELTY_DEPTH,
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
            dimension=Dimension.NOVELTY_DEPTH,
            issue_title=issue_title,
            severity=severity,
            confidence=0.76 if severity == Severity.HIGH else 0.7,
            evidence_anchor=evidence_anchor,
            diagnosis=diagnosis,
            why_it_matters=why_it_matters,
            next_action=next_action,
            source_agent=self.agent_name,
            source_skill_version=skill_version,
        )
