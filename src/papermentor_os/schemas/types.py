from __future__ import annotations

from enum import Enum


class Discipline(str, Enum):
    COMPUTER_SCIENCE = "computer_science"


class PaperStage(str, Enum):
    PROPOSAL = "proposal"
    DRAFT = "draft"
    FINAL_DRAFT = "final_draft"


class Dimension(str, Enum):
    TOPIC_SCOPE = "topic_scope"
    LOGIC_CHAIN = "logic_chain"
    LITERATURE_SUPPORT = "literature_support"
    NOVELTY_DEPTH = "novelty_depth"
    WRITING_FORMAT = "writing_format"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

