from __future__ import annotations

from abc import ABC, abstractmethod

from papermentor_os.schemas.paper import PaperPackage
from papermentor_os.schemas.report import DimensionReport
from papermentor_os.skills.loader import SkillBundle


class BaseReviewAgent(ABC):
    agent_name: str
    skill_version: str

    @abstractmethod
    def review(self, paper: PaperPackage, skill_bundle: SkillBundle | None = None) -> DimensionReport:
        raise NotImplementedError

    def resolve_skill_version(self, skill_bundle: SkillBundle | None) -> str:
        if skill_bundle is None:
            return self.skill_version
        return skill_bundle.primary_rubric_version(self.skill_version)
