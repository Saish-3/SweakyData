from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from models import Evidence


def check_correlation(
    df: pd.DataFrame,
    id_prefix: str = "E",
    start_index: int = 1,
) -> List[Evidence]:
    """
    Checks for Simpson's Paradox:
    Correlation between two numeric columns flips sign when conditioned/grouped
    by a categorical column.
    """
    evidence_list: List[Evidence] = []
    n_rows = len(df)
    if n_rows < 30:
        return evidence_list

    curr_idx = start_index

    # Find numeric and categorical columns
    numeric_cols = []
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]) and df[c].nunique() > 5:
            numeric_cols.append(c)

    cat_cols = []
    for c in df.columns:
        n_uniq = df[c].nunique()
        if 2 <= n_uniq <= 12:
            cat_cols.append(c)

    # Limit search space for performance on 50k rows
    numeric_cols = numeric_cols[:8]
    cat_cols = cat_cols[:5]

    paradox_found = False

    for i in range(len(numeric_cols)):
        for j in range(i + 1, len(numeric_cols)):
            col1 = numeric_cols[i]
            col2 = numeric_cols[j]

            # Drop NAs
            sub_df = df[[col1, col2] + cat_cols].dropna(subset=[col1, col2])
            if len(sub_df) < 30:
                continue

            overall_corr = sub_df[col1].corr(sub_df[col2])
            if pd.isna(overall_corr) or abs(overall_corr) < 0.15:
                # Weak overall correlation is prone to noise flips, skip
                continue

            for cat in cat_cols:
                groups = sub_df.groupby(cat)
                group_corrs: Dict[str, float] = {}
                reversals = 0
                valid_groups = 0

                for grp_val, grp_data in groups:
                    if len(grp_data) >= 15:
                        grp_r = grp_data[col1].corr(grp_data[col2])
                        if not pd.isna(grp_r):
                            group_corrs[str(grp_val)] = round(float(grp_r), 3)
                            valid_groups += 1
                            # Check sign reversal with meaningful difference
                            if (overall_corr > 0 and grp_r < -0.1) or (overall_corr < 0 and grp_r > 0.1):
                                reversals += 1

                # If at least 2 valid groups and all or majority reverse sign
                if valid_groups >= 2 and reversals >= max(2, int(0.6 * valid_groups)):
                    paradox_found = True
                    avg_grp_corr = round(float(np.mean(list(group_corrs.values()))), 3)
                    evidence_list.append(
                        Evidence(
                            id=f"{id_prefix}{curr_idx}",
                            type="correlation",
                            columns=[col1, col2, cat],
                            metric={
                                "overall_corr": round(float(overall_corr), 3),
                                "group_corr_mean": avg_grp_corr,
                                "subgroup_corrs": group_corrs,
                                "reversal_count": reversals,
                                "grouping_column": cat,
                            },
                            status="PROVEN",
                            summary=(
                                f"Simpson's paradox detected: correlation between '{col1}' and '{col2}' is "
                                f"{overall_corr:.2f} overall, but reverses sign in '{cat}' subgroups "
                                f"(average group r = {avg_grp_corr:+.2f})."
                            ),
                            sample_rows=sub_df[[col1, col2, cat]].head(5).to_dict(orient="records"),
                        )
                    )
                    curr_idx += 1
                    # Limit to at most 2 paradox findings to avoid overwhelming evidence
                    if len(evidence_list) >= 2:
                        return evidence_list

    if not paradox_found:
        evidence_list.append(
            Evidence(
                id=f"{id_prefix}{curr_idx}",
                type="correlation",
                columns=[],
                metric={"paradox_count": 0},
                status="NO_EVIDENCE",
                summary="No Simpson's paradox or misleading correlation sign reversals detected across categorical subgroups.",
                sample_rows=[],
            )
        )
        curr_idx += 1

    return evidence_list
