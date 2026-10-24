from typing import List, Optional
import pandas as pd
from models import Evidence


def check_duplicates(
    df: pd.DataFrame,
    split_col: Optional[str] = None,
    id_prefix: str = "E",
    start_index: int = 1,
) -> List[Evidence]:
    """
    Checks for exact duplicate rows across features, and duplicates crossing train/test split.
    """
    evidence_list: List[Evidence] = []
    n_rows = len(df)
    if n_rows == 0:
        return evidence_list

    curr_idx = start_index

    # Identify ID-like columns to avoid masking duplicates when IDs are auto-generated
    id_cols = [
        c for c in df.columns
        if c != split_col and (
            any(k in c.lower() for k in ["_id", "id", "uuid", "guid"]) or
            (df[c].nunique() >= 0.98 * n_rows and df[c].dtype == "object")
        )
    ]
    # Check on all columns (except split) first
    feature_cols = [c for c in df.columns if c != split_col]
    if not feature_cols:
        feature_cols = list(df.columns)

    # If ID columns exist, feature_cols_no_id is useful to detect identical observation records
    feature_cols_no_id = [c for c in feature_cols if c not in id_cols]
    eval_cols = feature_cols_no_id if len(feature_cols_no_id) >= 2 else feature_cols

    dup_mask = df.duplicated(subset=eval_cols, keep="first")
    dup_count = int(dup_mask.sum())
    dup_pct = round((dup_count / n_rows) * 100, 2)

    sample_dups = []
    if dup_count > 0:
        # Get up to 10 sample duplicate rows
        sample_dups = df[dup_mask].head(10).to_dict(orient="records")
        evidence_list.append(
            Evidence(
                id=f"{id_prefix}{curr_idx}",
                type="duplicates",
                columns=feature_cols if len(feature_cols) <= 5 else [f"{len(feature_cols)} feature columns"],
                metric={"duplicate_count": dup_count, "duplicate_pct": dup_pct, "total_rows": n_rows},
                status="PROVEN",
                summary=f"Found {dup_count} duplicate rows ({dup_pct}% of {n_rows} rows).",
                sample_rows=sample_dups,
            )
        )
    else:
        evidence_list.append(
            Evidence(
                id=f"{id_prefix}{curr_idx}",
                type="duplicates",
                columns=feature_cols if len(feature_cols) <= 5 else [f"{len(feature_cols)} feature columns"],
                metric={"duplicate_count": 0, "duplicate_pct": 0.0, "total_rows": n_rows},
                status="NO_EVIDENCE",
                summary="No duplicate rows detected in dataset.",
                sample_rows=[],
            )
        )
    curr_idx += 1

    # 2. Cross-split duplicate check (if split_col provided)
    if split_col and split_col in df.columns:
        # Check rows that have identical features but different split values
        grouped = df.groupby(eval_cols)[split_col].nunique()
        cross_split_mask = grouped > 1
        cross_split_count = int(cross_split_mask.sum())
        cross_split_pct = round((cross_split_count / n_rows) * 100, 2)

        if cross_split_count > 0:
            # Find sample rows
            cross_keys = grouped[cross_split_mask].head(5).index
            sample_rows = []
            for k in cross_keys:
                if isinstance(k, tuple):
                    filter_mask = pd.Series(True, index=df.index)
                    for col, val in zip(eval_cols, k):
                        filter_mask &= (df[col] == val)
                    matched = df[filter_mask].head(2)
                else:
                    matched = df[df[eval_cols[0]] == k].head(2)
                sample_rows.extend(matched.to_dict(orient="records"))

            evidence_list.append(
                Evidence(
                    id=f"{id_prefix}{curr_idx}",
                    type="duplicates",
                    columns=[split_col, "features"],
                    metric={
                        "cross_split_duplicates": cross_split_count,
                        "cross_split_pct": cross_split_pct,
                        "split_column": split_col,
                    },
                    status="PROVEN",
                    summary=f"Found {cross_split_count} identical feature instances ({cross_split_pct}%) leaked across '{split_col}' split values.",
                    sample_rows=sample_rows[:10],
                )
            )
        else:
            evidence_list.append(
                Evidence(
                    id=f"{id_prefix}{curr_idx}",
                    type="duplicates",
                    columns=[split_col, "features"],
                    metric={
                        "cross_split_duplicates": 0,
                        "cross_split_pct": 0.0,
                        "split_column": split_col,
                    },
                    status="NO_EVIDENCE",
                    summary=f"No feature overlap detected between splits in '{split_col}'.",
                    sample_rows=[],
                )
            )
        curr_idx += 1

    return evidence_list
