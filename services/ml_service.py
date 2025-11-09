"""Machine learning services for healthcare analytics"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from mysql.connector import MySQLConnection
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "cost_risk_model.pkl"
PIPELINE_PATH = MODEL_DIR / "cost_risk_pipeline.pkl"

CATEGORICAL_COLUMNS = [
    "gender",
    "state",
    "hospital_state",
    "visit_type",
    "payment_method",
    "specialization",
]
NUMERIC_COLUMNS = [
    "age",
    "visit_duration_minutes",
    "consultation_fee",
]
TARGET_COLUMN = "high_cost_flag"


def fetch_training_dataframe(connection: MySQLConnection) -> pd.DataFrame:
    query = """
        SELECT
            pv.total_cost,
            pv.visit_duration_minutes,
            pv.payment_method,
            pv.visit_type,
            p.age,
            p.gender,
            p.state,
            d.specialization,
            d.consultation_fee,
            h.state AS hospital_state
        FROM patient_visits pv
        JOIN patients p ON pv.patient_id = p.patient_id
        JOIN doctors d ON pv.doctor_id = d.doctor_id
        JOIN hospitals h ON pv.hospital_id = h.hospital_id
        WHERE pv.total_cost IS NOT NULL
    """
    df = pd.read_sql(query, connection)
    if df.empty:
        return df

    df["visit_duration_minutes"].fillna(df["visit_duration_minutes"].median(), inplace=True)
    df["consultation_fee"].fillna(df["consultation_fee"].median(), inplace=True)
    df["age"].fillna(df["age"].median(), inplace=True)
    df["state"].fillna("Unknown", inplace=True)
    df["hospital_state"].fillna(df["state"], inplace=True)
    df["specialization"].fillna("General Medicine", inplace=True)
    df["gender"].fillna("Other", inplace=True)

    threshold = df["total_cost"].median()
    df[TARGET_COLUMN] = (df["total_cost"] >= threshold).astype(int)
    return df


def build_pipeline() -> Pipeline:
    categorical_transformer = OneHotEncoder(handle_unknown="ignore")
    numeric_transformer = Pipeline(
        steps=[("scaler", StandardScaler())]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical_transformer, CATEGORICAL_COLUMNS),
            ("num", numeric_transformer, NUMERIC_COLUMNS),
        ],
        remainder='drop',
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", model),
        ]
    )

    return pipeline


def train_cost_risk_model(connection: MySQLConnection) -> Dict:
    df = fetch_training_dataframe(connection)
    if df.empty or len(df) < 100:
        return {
            "success": False,
            "message": "Not enough data to train the model (minimum 100 records required)",
        }

    feature_columns = CATEGORICAL_COLUMNS + NUMERIC_COLUMNS
    X = df[feature_columns]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    return {
        "success": True,
        "message": "Model trained successfully",
        "metrics": {
            "precision": report["weighted avg"]["precision"],
            "recall": report["weighted avg"]["recall"],
            "f1_score": report["weighted avg"]["f1-score"],
            "support": int(report["accuracy"] * len(y_test)),
            "threshold": df["total_cost"].median(),
        },
    }


def load_model() -> Pipeline:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not trained. Please run training first.")
    return joblib.load(MODEL_PATH)


def predict_cost_risk(payload: Dict) -> Dict:
    model = load_model()

    data = {
        "age": payload.get("age", 40),
        "gender": payload.get("gender", "Other"),
        "state": payload.get("state", "Unknown"),
        "hospital_state": payload.get("hospital_state", payload.get("state", "Unknown")),
        "visit_type": payload.get("visit_type", "OPD"),
        "payment_method": payload.get("payment_method", "Cash"),
        "visit_duration_minutes": payload.get("visit_duration_minutes", 30),
        "specialization": payload.get("specialization", "General Medicine"),
        "consultation_fee": payload.get("consultation_fee", 500.0),
    }

    df = pd.DataFrame([data])
    probability = model.predict_proba(df)[0][1]
    prediction = int(probability >= 0.5)

    return {
        "prediction": prediction,
        "probability": float(probability),
        "risk_level": "High" if prediction == 1 else "Low",
    }
