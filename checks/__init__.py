from typing import List, Optional
import pandas as pd
from models import Evidence
from checks.duplicates import check_duplicates
from checks.leakage import check_leakage
from checks.labels import check_labels
from checks.correlation import check_correlation


def run_all_checks(
    df: pd.DataFrame,
    target: Optional[str] = None,
    split_col: Optional[str] = None,
) -> List[Evidence]:
    """
    Executes all deterministic checks and returns an ordered list of Evidence.
    Ensures sequential IDs: E1, E2, E3...
    """
    all_evidence: List[Evidence] = []
    current_index = 1

    # 1. Duplicate checks (exact duplicates and split contamination)
    dup_evidence = check_duplicates(df, split_col=split_col, id_prefix="E", start_index=current_index)
    all_evidence.extend(dup_evidence)
    current_index = len(all_evidence) + 1

    # 2. Leakage checks (constant columns, ID leakage, target predictive power)
    leakage_evidence = check_leakage(df, target_col=target, id_prefix="E", start_index=current_index)
    all_evidence.extend(leakage_evidence)
    current_index = len(all_evidence) + 1

    # 3. Label noise checks (contradictory labels on identical features, model disagreement)
    if target and target in df.columns:
        label_evidence = check_labels(df, target_col=target, split_col=split_col, id_prefix="E", start_index=current_index)
        all_evidence.extend(label_evidence)
        current_index = len(all_evidence) + 1

    # 4. Misleading correlation / Simpson's paradox
    corr_evidence = check_correlation(df, id_prefix="E", start_index=current_index)
    all_evidence.extend(corr_evidence)

    # Renumber strictly to ensure E1..En consistency
    for i, ev in enumerate(all_evidence, start=1):
        ev.id = f"E{i}"

    return all_evidence
