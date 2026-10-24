import sys
import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer


def generate_crime_scene_dataset(n_samples: int = 1200, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a realistic tabular dataset with deliberately planted data crimes:
    1. Leaky feature derived directly from the target
    2. 5% duplicated feature rows crossing train/test split
    3. 3% flipped labels on identical feature vectors
    4. Simpson's paradox pair conditioned on a categorical subgroup
    5. Innocent-but-suspicious-looking column that must return NO_EVIDENCE
    6. Constant metadata column
    7. High-cardinality unique ID column
    """
    np.random.seed(random_state)
    raw = load_breast_cancer(as_frame=True)
    df_base = raw.frame.copy()

    # Rename target to 'target'
    df_base = df_base.rename(columns={"target": "diagnosis"})
    
    # If we need more samples than 569, repeat and add subtle jitter
    if n_samples > len(df_base):
        repeats = (n_samples // len(df_base)) + 1
        df_base = pd.concat([df_base] * repeats, ignore_index=True).iloc[:n_samples].copy()

    df = pd.DataFrame()

    # 1. High-cardinality identifier column (ID leakage risk)
    df["patient_uuid"] = [f"PT-{10000 + i}" for i in range(len(df_base))]

    # 2. Add realistic base features from dataset
    feature_cols = [
        "mean radius", "mean texture", "mean perimeter", "mean area",
        "mean smoothness", "mean compactness", "mean concavity",
    ]
    for col in feature_cols:
        clean_name = col.replace(" ", "_")
        df[clean_name] = df_base[col].values

    # Target variable (0: Malignant, 1: Benign)
    df["diagnosis"] = df_base["diagnosis"].values

    # 3. CRIME 1: Planted Leaky Column (derived directly from target)
    # 99% aligned with target plus minuscule noise
    df["post_biopsy_malignancy_index"] = (
        df["diagnosis"] * 10.0 + np.random.normal(0, 0.05, size=len(df))
    ).round(3)

    # 4. CRIME 2: Simpson's Paradox Pair conditioned on 'clinic_facility'
    # Groups: 'Clinic_Alpha' and 'Clinic_Beta'
    # Within each clinic, dosage and biomarker have POSITIVE correlation.
    # Across both clinics, overall correlation is strongly NEGATIVE.
    group = np.random.choice(["Clinic_Alpha", "Clinic_Beta"], size=len(df), p=[0.5, 0.5])
    df["clinic_facility"] = group

    dosage = np.zeros(len(df))
    biomarker = np.zeros(len(df))

    # Clinic Alpha: dosage low (10-30), biomarker high (70-90) -> within group: + slope
    mask_a = (group == "Clinic_Alpha")
    dosage[mask_a] = np.random.uniform(10, 30, size=mask_a.sum())
    biomarker[mask_a] = 60 + 0.9 * dosage[mask_a] + np.random.normal(0, 1.5, size=mask_a.sum())

    # Clinic Beta: dosage high (60-90), biomarker low (15-40) -> within group: + slope
    mask_b = (group == "Clinic_Beta")
    dosage[mask_b] = np.random.uniform(60, 90, size=mask_b.sum())
    biomarker[mask_b] = 5 + 0.8 * dosage[mask_b] + np.random.normal(0, 1.5, size=mask_b.sum())

    df["drug_dosage_mg"] = dosage.round(2)
    df["cellular_biomarker_level"] = biomarker.round(2)

    # 5. INNOCENT COLUMN: Scary sounding name, but legitimate feature (safe CV score ~0.65, NO_EVIDENCE)
    df["suspicious_risk_index"] = (
        np.random.normal(50, 10, size=len(df)) + (df["diagnosis"] * 3.0)
    ).round(2)

    # 6. Constant column
    df["trial_protocol_version"] = "IRB-2026-V4"

    # Split column: train / test
    split_assign = np.random.choice(["train", "test"], size=len(df), p=[0.75, 0.25])
    df["data_split"] = split_assign

    # 7. CRIME 3: 5% Duplicated rows crossing the train/test split
    n_dups = int(0.05 * len(df))
    train_indices = df[df["data_split"] == "train"].index[:n_dups]
    test_dup_rows = df.loc[train_indices].copy()
    test_dup_rows["data_split"] = "test"  # Leaked into test partition!
    test_dup_rows["patient_uuid"] = [f"PT-{90000 + i}" for i in range(len(test_dup_rows))]

    df = pd.concat([df, test_dup_rows], ignore_index=True)

    # 8. CRIME 4: 3% conflicting labels on identical feature vectors
    n_flip = int(0.03 * len(df))
    flip_indices = np.random.choice(len(df), size=n_flip, replace=False)
    conflict_rows = df.iloc[flip_indices].copy()
    # Flip the diagnosis label
    conflict_rows["diagnosis"] = 1 - conflict_rows["diagnosis"]
    df = pd.concat([df, conflict_rows], ignore_index=True)

    return df


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Dataset Crime Scene demo CSV.")
    parser.add_argument("--output", type=str, default="samples/crime_scene_dataset.csv", help="Output CSV path")
    parser.add_argument("--selftest", action="store_true", help="Run self-test asserting all planted crimes are detected")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_crime_scene_dataset()
    df.to_csv(out_path, index=False)
    print(f"Generated crime scene dataset with {len(df)} rows and {len(df.columns)} columns at {out_path}")

    if args.selftest:
        print("\n--- Running Crime Scene Self-Test ---")
        # Add parent dir to sys.path if needed
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from checks import run_all_checks

        evidence = run_all_checks(df, target="diagnosis", split_col="data_split")
        print(f"Total evidence items generated: {len(evidence)}")

        proven_types = {e.type for e in evidence if e.status == "PROVEN"}
        print(f"Proven crime types detected: {proven_types}")

        # Assertions
        assert "leakage" in proven_types, "FAIL: Target leakage not detected!"
        assert "duplicates" in proven_types, "FAIL: Cross-split duplicates not detected!"
        assert "label_noise" in proven_types, "FAIL: Conflicting labels not detected!"
        assert "correlation" in proven_types, "FAIL: Simpson's paradox not detected!"

        # Assert innocent column is clean
        innocent_checks = [
            e for e in evidence
            if "suspicious_risk_index" in e.columns
        ]
        assert len(innocent_checks) > 0, "FAIL: Innocent column was not checked!"
        for e in innocent_checks:
            assert e.status == "NO_EVIDENCE", f"FAIL: Innocent column flagged as {e.status}!"

        print("\n[SUCCESS] ALL SELF-TEST ASSERTIONS PASSED:")
        print("  ✓ Target leakage detected (post_biopsy_malignancy_index)")
        print("  ✓ Cross-split duplicate leakage detected (data_split)")
        print("  ✓ Identical feature conflicting labels detected")
        print("  ✓ Simpson's paradox detected (drug_dosage_mg vs cellular_biomarker_level)")
        print("  ✓ Innocent column 'suspicious_risk_index' confirmed NO_EVIDENCE")


if __name__ == "__main__":
    main()
