#!/usr/bin/env python3
"""
Model training and evaluation pipeline for Beta Thalassemia classification using k-mer features.

Loads extracted k-mer features from expanded_feature_dataset.csv, splits data 80/20 into
training and test sets (random_state=42), trains LogisticRegression and RandomForestClassifier,
evaluates Accuracy, Precision, Recall, F1-Score, ROC-AUC, 5-Fold Cross-Validation, Confusion
Matrix, and Classification Report, and serializes model artifacts and feature_columns.json to disk.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    StratifiedGroupKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.preprocessing import LabelEncoder

DEFAULT_DATASET_PATH: Path = (
    PROJECT_ROOT / "dataset" / "processed" / "expanded_feature_dataset.csv"
)
DEFAULT_MODEL_DIR: Path = PROJECT_ROOT / "ai" / "models"


class ModelTrainingError(Exception):
    """Raised when data loading, splitting, training, or evaluation fails."""


def load_and_preprocess_data(
    csv_path: Path,
) -> Tuple[pd.DataFrame, pd.Series, LabelEncoder]:
    """
    Load dataset CSV and separate features from target label.

    Args:
        csv_path: Path to feature dataset CSV file.

    Returns:
        Tuple of (features_df, encoded_target_series, label_encoder).

    Raises:
        ModelTrainingError: If file is missing or required columns not found.
    """
    if not csv_path.is_file():
        raise ModelTrainingError(
            f"Feature dataset not found: {csv_path.resolve()}"
        )

    df = pd.read_csv(csv_path)
    if "label" not in df.columns:
        raise ModelTrainingError(
            f"Target column 'label' missing from {csv_path}"
        )

    metadata_cols = {
        "id",
        "label",
        "mutation_name",
        "mutation_type",
        "clinvar_accession",
        "clinical_significance",
        "review_status",
        "condition",
        "mutation_group",
        "dataset_split",
        "source",
    }
    feature_cols = [col for col in df.columns if col not in metadata_cols]

    if not feature_cols:
        raise ModelTrainingError("No feature columns found in dataset.")

    X = df[feature_cols]

    label_encoder = LabelEncoder()
    y = pd.Series(label_encoder.fit_transform(df["label"]))

    return X, y, label_encoder


def train_and_evaluate_model(
    model_name: str,
    model: Any,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    X_full: pd.DataFrame,
    y_full: pd.Series,
    groups: Optional[pd.Series] = None,
) -> Dict[str, Any]:
    """
    Train a machine learning model and compute comprehensive evaluation metrics.

    Args:
        model_name: Human-readable model description.
        model: Scikit-learn estimator instance.
        X_train: Training features.
        X_test: Test features.
        y_train: Training labels.
        y_test: Test labels.
        X_full: Full dataset features for cross-validation.
        y_full: Full dataset labels for cross-validation.

    Returns:
        Dictionary containing evaluation metrics and fitted model.
    """
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_probs = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(
        precision_score(y_test, y_pred, average="binary", zero_division=0)
    )
    rec = float(
        recall_score(y_test, y_pred, average="binary", zero_division=0)
    )
    f1 = float(f1_score(y_test, y_pred, average="binary", zero_division=0))

    roc_auc = float(roc_auc_score(y_test, y_probs))
    fpr, tpr, thresholds = roc_curve(y_test, y_probs)

    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=0)

    if groups is None:
        cv_scores = cross_val_score(model, X_full, y_full, cv=5, scoring="accuracy")
    else:
        split_count = min(5, int(groups.nunique()))
        if split_count < 2:
            raise ModelTrainingError(
                "Grouped cross-validation requires at least two variant positions."
            )
        cv = StratifiedGroupKFold(
            n_splits=split_count, shuffle=True, random_state=42
        )
        cv_scores = cross_val_score(
            model,
            X_full,
            y_full,
            groups=groups,
            cv=cv,
            scoring="accuracy",
        )
    cv_mean = float(cv_scores.mean())
    cv_std = float(cv_scores.std())

    metrics: Dict[str, Any] = {
        "name": model_name,
        "model": model,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "fpr": fpr,
        "tpr": tpr,
        "thresholds": thresholds,
        "cv_scores": cv_scores,
        "cv_mean": cv_mean,
        "cv_std": cv_std,
        "confusion_matrix": cm,
        "classification_report": report,
    }

    return metrics


def print_evaluation_summary(metrics: Dict[str, Any]) -> None:
    """
    Print formatted evaluation metrics to stdout.

    Args:
        metrics: Dictionary returned by train_and_evaluate_model.
    """
    print("=" * 65)
    print(f" Model Evaluation: {metrics['name']}")
    print("=" * 65)
    print(f"Accuracy:                  {metrics['accuracy']:.4f}")
    print(f"Precision:                 {metrics['precision']:.4f}")
    print(f"Recall:                    {metrics['recall']:.4f}")
    print(f"F1-Score:                  {metrics['f1_score']:.4f}")
    print(f"ROC-AUC Score:             {metrics['roc_auc']:.4f}")
    print(f"5-Fold CV Accuracy:        {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})")
    print("\nConfusion Matrix:")
    print(metrics["confusion_matrix"])
    print("\nClassification Report:")
    print(metrics["classification_report"])
    print("-" * 65)


def save_model(model: Any, output_path: Path) -> None:
    """
    Serialize a trained model to a .pkl file using joblib.

    Args:
        model: Trained scikit-learn estimator.
        output_path: Path to output .pkl file.

    Raises:
        ModelTrainingError: If writing to disk fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        joblib.dump(model, output_path)
    except Exception as exc:
        raise ModelTrainingError(
            f"Failed to save model to {output_path}: {exc}"
        ) from exc


def save_feature_columns(
    feature_columns: List[str], output_path: Path
) -> None:
    """
    Save the ordered list of feature column names to a JSON file.

    Args:
        feature_columns: List of feature names in training order.
        output_path: Destination JSON file path.

    Raises:
        ModelTrainingError: If writing JSON to disk fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_path.write_text(
            json.dumps(feature_columns, indent=4), encoding="utf-8"
        )
    except OSError as exc:
        raise ModelTrainingError(
            f"Failed to save feature columns to {output_path}: {exc}"
        ) from exc


def run_training_pipeline(
    dataset_path: Path = DEFAULT_DATASET_PATH,
    model_dir: Path = DEFAULT_MODEL_DIR,
) -> Dict[str, Any]:
    """
    Execute full dataset loading, train-test split, model training, and evaluation.

    Args:
        dataset_path: Path to input feature dataset CSV.
        model_dir: Directory where trained .pkl models will be saved.

    Returns:
        Dictionary mapping model names to evaluation metrics.
    """
    dataset = pd.read_csv(dataset_path)
    X, y, _ = load_and_preprocess_data(dataset_path)

    # Save ordered feature column list to ai/models/feature_columns.json
    feature_columns: List[str] = X.columns.tolist()
    feature_columns_path = model_dir / "feature_columns.json"
    save_feature_columns(feature_columns, feature_columns_path)
    print(f"Saved feature columns list to: {feature_columns_path.resolve()}")

    groups: Optional[pd.Series] = None
    if {"dataset_split", "mutation_group"}.issubset(dataset.columns):
        train_mask = dataset["dataset_split"] == "train"
        challenge_mask = dataset["dataset_split"] == "challenge"
        if not train_mask.any() or not challenge_mask.any():
            raise ModelTrainingError(
                "Curated data must contain both train and challenge partitions."
            )

        train_groups = set(dataset.loc[train_mask, "mutation_group"].astype(str))
        challenge_groups = set(dataset.loc[challenge_mask, "mutation_group"].astype(str))
        if train_groups & challenge_groups:
            raise ModelTrainingError(
                "A variant position appears in both train and challenge partitions."
            )

        X_train = X.loc[train_mask].reset_index(drop=True)
        X_test = X.loc[challenge_mask].reset_index(drop=True)
        y_train = y.loc[train_mask].reset_index(drop=True)
        y_test = y.loc[challenge_mask].reset_index(drop=True)
        groups = dataset.loc[train_mask, "mutation_group"].astype(str).reset_index(drop=True)
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train = X_train.reset_index(drop=True)
        X_test = X_test.reset_index(drop=True)
        y_train = y_train.reset_index(drop=True)
        y_test = y_test.reset_index(drop=True)

    models_to_train = [
        (
            "Logistic Regression",
            LogisticRegression(random_state=42, max_iter=1000),
            model_dir / "logistic_regression.pkl",
        ),
        (
            "Random Forest Classifier",
            RandomForestClassifier(random_state=42, n_estimators=100),
            model_dir / "random_forest.pkl",
        ),
    ]

    results: Dict[str, Any] = {}
    for name, model_instance, save_path in models_to_train:
        metrics = train_and_evaluate_model(
            name,
            model_instance,
            X_train,
            X_test,
            y_train,
            y_test,
            X_train,
            y_train,
            groups,
        )
        print_evaluation_summary(metrics)
        save_model(metrics["model"], save_path)
        print(f"Saved model to: {save_path.resolve()}\n")
        results[name] = metrics

    return results


def main() -> int:
    """
    Entry point for baseline model training.

    Returns:
        0 on success, 1 on error.
    """
    try:
        parser = argparse.ArgumentParser(
            description="Train and evaluate GeneMindAI models."
        )
        parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
        parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
        args = parser.parse_args()
        run_training_pipeline(args.dataset, args.model_dir)
        return 0
    except ModelTrainingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
