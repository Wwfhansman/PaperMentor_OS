from __future__ import annotations

import json
import sys
from pathlib import Path

from papermentor_os.orchestrator.chief_reviewer import ChiefReviewer


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_review.py <path-to-docx>")
        return 1

    reviewer = ChiefReviewer()
    report = reviewer.review_docx(Path(sys.argv[1]))
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

