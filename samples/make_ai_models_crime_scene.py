import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd


def generate_ai_models_crime_scene(n_samples: int = 1500, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a realistic AI Model Benchmark & Evaluation dataset with deliberately planted
    data crimes (benchmark leakage, evaluation test set contamination, flaky labels, and Simpson's paradox).

    Dataset Story:
    An AI lab is training an ML classifier to predict whether an AI model run passes enterprise
    production benchmarks (`benchmark_passed`). But the dataset has severe hidden crimes!
    """
    np.random.seed(random_state)

    # Base model archetypes
    model_prefixes = [
        "Llama-3-Instruct", "Gemma-4-Preview", "Mistral-NeMo", "Qwen-2.5-Coder",
        "DeepSeek-V2.5", "Phi-4-Mini", "Claude-3-Sonnet", "Command-R-Plus"
    ]
    quant_types = ["fp16", "int8", "int4-awq", "q4_k_m"]
    gpu_types = ["NVIDIA-H100-SXM5", "NVIDIA-A100-80G", "Apple-M3-Max", "RTX-4090"]

    n = n_samples

    # 1. High Cardinality Identifier
    run_uuids = [f"RUN-{100000 + i:06d}-EVAL" for i in range(n)]

    # Model specs
    model_name = np.random.choice(model_prefixes, size=n)
    quantization = np.random.choice(quant_types, size=n, p=[0.3, 0.3, 0.2, 0.2])
    hardware = np.random.choice(gpu_types, size=n, p=[0.4, 0.3, 0.15, 0.15])
    context_window_k = np.random.choice([8, 16, 32, 64, 128], size=n, p=[0.2, 0.3, 0.25, 0.15, 0.1])
    tokens_per_sec = np.random.normal(65, 18, size=n).clip(15, 140).round(1)
    prompt_token_length = np.random.randint(256, 8192, size=n)

    # Architecture grouping for Simpson's paradox
    # 'Dense-Transformer' vs 'Sparse-MoE'
    architecture_type = np.random.choice(["Dense-Transformer", "Sparse-MoE"], size=n, p=[0.55, 0.45])

    # 2. Target Variable: benchmark_passed (1 = Passed Enterprise Benchmark, 0 = Failed)
    # Influenced realistically by tokens_per_sec and prompt length
    logit = (tokens_per_sec * 0.04) - (prompt_token_length / 4000.0) + np.random.normal(0, 0.5, size=n)
    prob_pass = 1.0 / (1.0 + np.exp(-logit))
    benchmark_passed = (prob_pass > 0.45).astype(int)

    # 3. CRIME 1: Target Leakage (derived from benchmark outcome)
    # An internal post-eval metric that inadvertently leaked into training features!
    # A single-feature depth-2 tree will get 0.999 AUC.
    eval_loss_normalized = (benchmark_passed * 8.5 + np.random.normal(0, 0.04, size=n)).round(3)

    # 4. CRIME 2: Simpson's Paradox Pair
    # Conditioned on 'architecture_type'
    # Features: 'active_parameter_weights_b' and 'latency_per_1k_tokens_ms'
    # Within Dense: larger active parameters -> higher latency (+ slope)
    # Within MoE: larger active parameters -> higher latency (+ slope)
    # Across ALL models: Dense models have low active params (7-14B) but higher relative latency on long context;
    # MoE models have high activated params (32-70B) but hardware optimizations keep baseline low,
    # resulting in a strong NEGATIVE aggregate correlation (- slope)!
    active_params = np.zeros(n)
    latency_ms = np.zeros(n)

    mask_dense = (architecture_type == "Dense-Transformer")
    active_params[mask_dense] = np.random.uniform(7.0, 20.0, size=mask_dense.sum())
    latency_ms[mask_dense] = 80.0 + 1.8 * active_params[mask_dense] + np.random.normal(0, 2.0, size=mask_dense.sum())

    mask_moe = (architecture_type == "Sparse-MoE")
    active_params[mask_moe] = np.random.uniform(35.0, 70.0, size=mask_moe.sum())
    latency_ms[mask_moe] = 15.0 + 1.2 * active_params[mask_moe] + np.random.normal(0, 2.0, size=mask_moe.sum())

    # 5. INNOCENT FEATURE: Scary sounding name, safe evaluation (NO_EVIDENCE)
    suspicious_training_cluster_id = np.random.normal(50, 15, size=n).round(1)

    # 6. Constant metadata column
    eval_benchmark_harness = "LMSYS-Harness-v4.1"

    # Train / test evaluation split
    eval_split = np.random.choice(["train", "test"], size=n, p=[0.75, 0.25])

    df = pd.DataFrame({
        "eval_run_uuid": run_uuids,
        "model_name": model_name,
        "architecture_type": architecture_type,
        "quantization": quantization,
        "hardware": hardware,
        "context_window_k": context_window_k,
        "prompt_token_length": prompt_token_length,
        "tokens_per_sec": tokens_per_sec,
        "active_parameter_weights_b": active_params.round(2),
        "latency_per_1k_tokens_ms": latency_ms.round(2),
        "eval_loss_normalized": eval_loss_normalized,  # LEAK
        "suspicious_training_cluster_id": suspicious_training_cluster_id,  # INNOCENT
        "eval_benchmark_harness": eval_benchmark_harness,  # CONSTANT
        "eval_split": eval_split,
        "benchmark_passed": benchmark_passed,  # TARGET
    })

    # 7. CRIME 3: Benchmark Test Set Contamination (5% duplicate runs leaked into test split)
    n_dups = int(0.05 * len(df))
    train_slice = df[df["eval_split"] == "train"].iloc[:n_dups].copy()
    train_slice["eval_split"] = "test"  # Crossed split boundary!
    train_slice["eval_run_uuid"] = [f"RUN-{800000 + i:06d}-EVAL" for i in range(len(train_slice))]
    df = pd.concat([df, train_slice], ignore_index=True)

    # 8. CRIME 4: Flaky Evaluator Label Noise (3% conflicting labels on identical runs)
    n_flips = int(0.03 * len(df))
    flip_indices = np.random.choice(len(df), size=n_flips, replace=False)
    conflicting_slice = df.iloc[flip_indices].copy()
    conflicting_slice["benchmark_passed"] = 1 - conflicting_slice["benchmark_passed"]
    df = pd.concat([df, conflicting_slice], ignore_index=True)

    return df


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate AI Models Broken Crime Scene CSV.")
    parser.add_argument("--output", type=str, default="samples/ai_models_crime_scene.csv", help="Output path")
    parser.add_argument("--selftest", action="store_true", help="Run forensic checks verification")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_ai_models_crime_scene()
    df.to_csv(out_path, index=False)
    print(f"Generated AI Models Crime Scene dataset ({len(df)} rows, {len(df.columns)} cols) at {out_path}")

    if args.selftest:
        print("\n--- Running AI Models Crime Scene Audit ---")
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from checks import run_all_checks

        evidence = run_all_checks(df, target="benchmark_passed", split_col="eval_split")
        proven_types = {e.type for e in evidence if e.status == "PROVEN"}
        print(f"Proven crimes detected: {proven_types}")

        assert "leakage" in proven_types, "Leakage missing!"
        assert "duplicates" in proven_types, "Contamination duplicates missing!"
        assert "label_noise" in proven_types, "Label noise missing!"
        assert "correlation" in proven_types, "Simpson's paradox missing!"

        innocent_checks = [e for e in evidence if "suspicious_training_cluster_id" in e.columns]
        for e in innocent_checks:
            assert e.status == "NO_EVIDENCE", f"Innocent column failed: {e.status}"

        print("\n[AI MODELS CRIME SCENE AUDIT COMPLETE]")
        print("  ✓ Benchmark Target Leakage: 'eval_loss_normalized' (AUC ~ 1.0)")
        print("  ✓ Benchmark Data Snooping: duplicate evaluation runs crossed eval_split (train -> test)")
        print("  ✓ Flaky Benchmark Evaluations: identical runs with contradictory benchmark_passed outcomes")
        print("  ✓ Simpson's Paradox: active_parameter_weights_b vs latency_per_1k_tokens_ms conditioned on architecture_type")
        print("  ✓ Innocent feature 'suspicious_training_cluster_id' verified clean (NO_EVIDENCE)")


if __name__ == "__main__":
    main()
