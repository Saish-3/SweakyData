from dataclasses import dataclass, field, asdict
import json
from typing import Any, List, Dict, Optional


@dataclass
class Evidence:
    id: str  # e.g., 'E1', 'E2'
    type: str  # 'leakage', 'duplicates', 'label_noise', 'correlation'
    columns: List[str]
    metric: Dict[str, Any]  # e.g., {"auc": 0.99, "correlation_diff": 0.85}
    status: str  # 'PROVEN' or 'NO_EVIDENCE'
    summary: str  # Short machine-written factual summary
    sample_rows: Optional[List[Dict[str, Any]]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Cap sample rows to max 20 rows
        if data.get("sample_rows") and len(data["sample_rows"]) > 20:
            data["sample_rows"] = data["sample_rows"][:20]
        return data

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            columns=data.get("columns", []),
            metric=data.get("metric", {}),
            status=data.get("status", "NO_EVIDENCE"),
            summary=data.get("summary", ""),
            sample_rows=data.get("sample_rows", [])[:20] if data.get("sample_rows") else [],
        )


@dataclass
class Explanation:
    evidence_id: str
    explanation: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    hypothesis: str  # Clearly labelled hypothesis
    suggested_fix: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
