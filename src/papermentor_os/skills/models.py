from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SkillCategory(str, Enum):
    RUBRIC = "rubric"
    POLICY = "policy"
    OUTPUT_SCHEMA = "output_schema"
    DOMAIN_ADAPTATION = "domain_adaptation"
    EVALUATION = "evaluation"


class SkillMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    category: SkillCategory
    owner_agent: list[str] = Field(default_factory=list)
    applicable_disciplines: list[str] = Field(default_factory=list)
    applicable_stages: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    optional_inputs: list[str] = Field(default_factory=list)
    output_schema: str | None = None
    policies: list[str] = Field(default_factory=list)
    quality_gates: list[str] = Field(default_factory=list)
    status: str = "active"

    @property
    def versioned_id(self) -> str:
        return f"{self.id}@{self.version}"


class SkillDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: SkillMetadata
    body: str = ""
    body_path: str | None = None

