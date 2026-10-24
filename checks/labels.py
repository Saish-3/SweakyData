from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import cross_val_predict
from sklearn.preprocessing import LabelEncoder
from models import Evidence


def check_labels(
    df: pd.DataFrame,
    target_col: Optional[str] = None,
    split_col: Optional[str] = None,
    id_prefix: str = "E",
    start_index: int = 1,
) -> List[Evidence]:
    """
    Checks for:
    1. Identical feature rows with contradictory labels.
    2. High-confidence label noise / label disagreement via cross-validation.
    """
    evidence_list: List[Evidence] = []
    if not target_col or target_col not in df.columns:
        return evidence_list

    n_rows = len(df)
    if n_rows < 10:
        return evidence_list

    curr_idx = start_index

    # Identify feature columns
    ignore_cols = {target_col}
    if split_col and split_col in df.columns:
        ignore_cols.add(split_col)

    feature_cols = [c for c in df.columns if c not in ignore_cols]
    if not feature_cols:
        return evidence_list

    # 1. Identical feature rows with contradictory labels
    # Use fillna for grouping to not lose NA rows
    df_for_grp = df[feature_cols + [target_col]].fillna("__NA__")
    grouped = df_for_grp.groupby(feature_cols)[target_col].nunique()
    conflict_mask = grouped > 1
    conflict_groups = grouped[conflict_mask]
    conflict_group_count = int(len(conflict_groups))

    if conflict_group_count > 0:
        # Count total rows involved in conflicts
        conflict_keys = set(conflict_groups.index)
        # Find matching rows
        if len(feature_cols) == 1:
            matching_rows_mask = df_for_grp[feature_cols[0]].isin(conflict_keys)
        else:
            multi_idx = pd.MultiIndex.from_frame(df_for_grp[feature_cols])
            matching_rows_mask = multi_idx.isin(conflict_keys)

        total_conflict_rows = int(matching_rows_mask.sum())
        conflict_pct = round((total_conflict_rows / n_rows) * 100, 2)

        sample_rows = df[matching_rows_mask].head(10).to_dict(orient="records")

        evidence_list.append(
            Evidence(
                id=f"{id_prefix}{curr_idx}",
                type="label_noise",
                columns=[target_col] + feature_cols[:3],
                metric={
                    "conflicting_identical_rows": total_conflict_rows,
                    "conflict_groups": conflict_group_count,
                    "conflict_pct": conflict_pct,
                },
                status="PROVEN",
                summary=f"Found {total_conflict_rows} rows ({conflict_pct}%) where identical feature records have conflicting '{target_col}' labels.",
                sample_rows=sample_rows,
            )
        )
        curr_idx += 1
    else:
        evidence_list.append(
            Evidence(
                id=f"{id_prefix}{curr_idx}",
                type="label_noise",
                columns=[target_col],
                metric={"conflicting_identical_rows": 0, "conflict_pct": 0.0},
                status="NO_EVIDENCE",
                summary=f"No identical feature rows with conflicting '{target_col}' labels were detected.",
                sample_rows=[],
            )
        )
        curr_idx += 1

    # 2. Out-of-fold label disagreement check
    # Sample down to 5000 rows if larger for speed
    df_sample = df.sample(n=min(5000, n_rows), random_state=42) if n_rows > 5000 else df.copy()

    # Encode features quickly
    X_parts = []
    for c in feature_cols:
        col_s = df_sample[c]
        if col_s.dtype == "object" or col_s.dtype == "bool":
            X_parts.append(pd.factorize(col_s.astype(str))[0].reshape(-1, 1))
        else:
            X_parts.append(pd.to_numeric(col_s, errors="coerce").fillna(0).values.reshape(-1, 1))

    if X_parts:
        X = np.hstack(X_parts)
        y_raw = df_sample[target_col]
        n_unique_y = y_raw.nunique()
        is_classification = n_unique_y <= 10 or y_raw.dtype == "object" or y_raw.dtype == "bool"

        try:
            if is_classification and n_unique_y >= 2:
                le = LabelEncoder()
                y = le.fit_transform(y_raw.astype(str))
                min_class_count = np.min(np.bincount(y))
                if min_class_count >= 2:
                    cv = min(3, min_class_count)
                    clf = RandomForestClassifier(n_estimators=20, max_depth=5, random_state=42, n_jobs=1)
                    proba = cross_val_predict(clf, X, y, cv=cv, method="predict_proba")
                    # Probability assigned to the true label
                    true_class_proba = proba[np.arange(len(y)), y]
                    # Strong disagreement: model gives true class < 15% probability
                    suspicious_mask = true_class_proba < 0.15
                    suspicious_count = int(np.sum(suspicious_mask))
                    suspicious_pct = round((suspicious_count / len(y)) * 100, 2)

                    if suspicious_pct >= 2.0 and suspicious_count >= 5:
                        evidence_list.append(
                            Evidence(
                                id=f"{id_prefix}{curr_idx}",
                                type="label_noise",
                                columns=[target_col],
                                metric={
                                    "cv_disagreement_count": suspicious_count,
                                    "cv_disagreement_pct": suspicious_pct,
                                },
                                status="PROVEN",
                                summary=f"CV anomaly check: {suspicious_count} rows ({suspicious_pct}%) strongly contradict out-of-fold model predictions (P(y) < 0.15).",
                                sample_rows=df_sample[suspicious_mask].head(5).to_dict(orient="records"),
                            )
                        )
                        curr_idx += 1
        except Exception:
            pass

    return evidence_list
