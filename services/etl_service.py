"""ETL service for handling healthcare data ingestion"""
from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
from mysql.connector import Error, MySQLConnection

REQUIRED_COLUMNS = [
    "patient_name",
    "age",
    "gender",
    "city",
    "state",
    "doctor_name",
    "specialization",
    "hospital_name",
    "hospital_type",
    "hospital_state",
    "visit_type",
    "visit_date",
    "total_cost",
    "payment_method",
]

VALID_GENDERS = {"male", "female", "other"}
VALID_VISIT_TYPES = {"opd", "emergency", "ipd", "follow-up"}
VALID_PAYMENT_METHODS = {"cash", "insurance", "card", "upi"}

VISIT_TYPE_CANONICAL = {
    "opd": "OPD",
    "emergency": "Emergency",
    "ipd": "IPD",
    "follow-up": "Follow-up",
}

PAYMENT_METHOD_CANONICAL = {
    "cash": "Cash",
    "insurance": "Insurance",
    "card": "Card",
    "upi": "UPI",
}


class DataValidationError(Exception):
    """Custom exception for validation errors"""


def read_tabular_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Read CSV or Excel file into DataFrame"""
    file_ext = filename.lower().split(".")[-1]
    buffer = io.BytesIO(file_bytes)

    if file_ext in {"csv"}:
        return pd.read_csv(buffer)
    if file_ext in {"xlsx", "xls"}:
        return pd.read_excel(buffer)
    raise DataValidationError("Unsupported file format. Use CSV or Excel (xlsx)")


def validate_columns(df: pd.DataFrame) -> None:
    """Ensure required columns exist"""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataValidationError(f"Missing required columns: {', '.join(missing)}")


def normalise_string(value: str) -> str:
    """Normalize string value, handling None and non-string types"""
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value).strip()
    return value.strip()


def parse_visit_date(value: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except (ValueError, TypeError):
            continue
    raise DataValidationError(f"Invalid visit_date: {value}")


def ensure_date_dimension(cursor, visit_date: datetime) -> int:
    date_id = int(visit_date.strftime("%Y%m%d"))
    cursor.execute(
        "SELECT date_id FROM date_dimension WHERE date_id = %s",
        (date_id,),
    )
    result = cursor.fetchone()
    if result:
        return result[0]

    cursor.execute(
        """
        INSERT INTO date_dimension
        (date_id, full_date, day, month, year, quarter, month_name, day_name, is_weekend)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            date_id,
            visit_date.date(),
            visit_date.day,
            visit_date.month,
            visit_date.year,
            (visit_date.month - 1) // 3 + 1,
            visit_date.strftime("%B"),
            visit_date.strftime("%A"),
            visit_date.weekday() >= 5,
        ),
    )
    return date_id


def get_or_create_patient(cursor, row: Dict) -> int:
    phone = normalise_string(row.get("phone"))
    email = normalise_string(row.get("email"))

    cursor.execute(
        """
        SELECT patient_id
        FROM patients
        WHERE (phone = %s AND phone IS NOT NULL)
           OR (email = %s AND email IS NOT NULL)
        LIMIT 1
        """,
        (phone, email),
    )
    result = cursor.fetchone()
    if result:
        return result[0]

    cursor.execute(
        """
        INSERT INTO patients
        (patient_name, age, gender, phone, email, address, city, state, pincode)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            normalise_string(row.get("patient_name")),
            int(row.get("age")),
            normalise_string(row.get("gender")).title(),
            phone,
            email,
            normalise_string(row.get("address")),
            normalise_string(row.get("city")),
            normalise_string(row.get("state")),
            normalise_string(row.get("pincode")),
        ),
    )
    return cursor.lastrowid


def get_or_create_hospital(cursor, row: Dict) -> int:
    hospital_name = normalise_string(row.get("hospital_name"))
    state = normalise_string(row.get("hospital_state")) or normalise_string(row.get("state"))

    cursor.execute(
        """
        SELECT hospital_id
        FROM hospitals
        WHERE hospital_name = %s AND state = %s
        LIMIT 1
        """,
        (hospital_name, state),
    )
    result = cursor.fetchone()
    if result:
        return result[0]

    cursor.execute(
        """
        INSERT INTO hospitals
        (hospital_name, hospital_type, address, city, state, pincode, phone, email, beds_count, established_year)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            hospital_name,
            normalise_string(row.get("hospital_type")) or "Private",
            normalise_string(row.get("hospital_address")) or normalise_string(row.get("address")),
            normalise_string(row.get("hospital_city")) or normalise_string(row.get("city")),
            state,
            normalise_string(row.get("hospital_pincode")) or normalise_string(row.get("pincode")),
            normalise_string(row.get("hospital_phone")),
            normalise_string(row.get("hospital_email")),
            int(row.get("beds_count")) if row.get("beds_count") else 100,
            int(row.get("established_year")) if row.get("established_year") else 2000,
        ),
    )
    return cursor.lastrowid


def get_or_create_doctor(cursor, row: Dict, hospital_id: int) -> int:
    doctor_name = normalise_string(row.get("doctor_name"))
    cursor.execute(
        """
        SELECT doctor_id
        FROM doctors
        WHERE doctor_name = %s AND hospital_id = %s
        LIMIT 1
        """,
        (doctor_name, hospital_id),
    )
    result = cursor.fetchone()
    if result:
        return result[0]

    cursor.execute(
        """
        INSERT INTO doctors
        (doctor_name, specialization, qualification, experience_years, hospital_id, phone, email, consultation_fee)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            doctor_name,
            normalise_string(row.get("specialization")) or "General Medicine",
            normalise_string(row.get("qualification")) or "MBBS",
            int(row.get("experience_years")) if row.get("experience_years") else 5,
            hospital_id,
            normalise_string(row.get("doctor_phone")),
            normalise_string(row.get("doctor_email")),
            float(row.get("consultation_fee")) if row.get("consultation_fee") else 500.0,
        ),
    )
    return cursor.lastrowid


def get_or_create_disease(cursor, disease_name: str) -> int | None:
    if not disease_name:
        return None
    disease_name = normalise_string(disease_name)
    cursor.execute(
        "SELECT disease_id FROM diseases WHERE disease_name = %s",
        (disease_name,),
    )
    result = cursor.fetchone()
    if result:
        return result[0]

    cursor.execute(
        """
        INSERT INTO diseases (disease_name, disease_category, severity_level, description)
        VALUES (%s, %s, %s, %s)
        """,
        (
            disease_name,
            normalise_string("General"),
            "Medium",
            f"Auto-created during ingestion for {disease_name}",
        ),
    )
    return cursor.lastrowid


def validate_row(row: Dict) -> None:
    gender = normalise_string(row.get("gender"))
    if not gender or gender.lower() not in VALID_GENDERS:
        raise DataValidationError("Invalid gender; must be Male, Female, or Other")

    visit_type = normalise_string(row.get("visit_type"))
    if not visit_type or visit_type.lower() not in VALID_VISIT_TYPES:
        raise DataValidationError("Invalid visit_type; must be OPD/Emergency/IPD/Follow-up")

    payment_method = normalise_string(row.get("payment_method"))
    if not payment_method or payment_method.lower() not in VALID_PAYMENT_METHODS:
        raise DataValidationError("Invalid payment_method; must be Cash/Insurance/Card/UPI")

    if pd.isna(row.get("total_cost")):
        raise DataValidationError("total_cost is required")
    float(row.get("total_cost"))  # raises if invalid

    parse_visit_date(row.get("visit_date"))


def process_patient_visits_file(
    connection: MySQLConnection,
    file_bytes: bytes,
    filename: str,
    source: str = "manual_upload",
) -> Dict:
    """Main ETL entry point"""
    df = read_tabular_file(file_bytes, filename)
    validate_columns(df)

    cursor = connection.cursor()

    # Create ingestion job
    cursor.execute(
        """
        INSERT INTO ingestion_jobs (job_type, source_file, status)
        VALUES ('PATIENT_VISITS', %s, 'PROCESSING')
        """,
        (filename,),
    )
    job_id = cursor.lastrowid

    total_records = len(df)
    success_count = 0
    failure_count = 0

    for _, record in df.iterrows():
        row_dict = {k: (v.strip() if isinstance(v, str) else v) for k, v in record.to_dict().items()}

        cursor.execute(
            """
            INSERT INTO staging_patient_visits (raw_payload, source_file, status)
            VALUES (%s, %s, 'PENDING')
            """,
            (json.dumps(row_dict, default=str), filename),
        )
        staging_id = cursor.lastrowid

        try:
            validate_row(row_dict)
            visit_date = parse_visit_date(row_dict.get("visit_date"))
            date_id = ensure_date_dimension(cursor, visit_date)

            patient_id = get_or_create_patient(cursor, row_dict)
            hospital_id = get_or_create_hospital(cursor, row_dict)
            doctor_id = get_or_create_doctor(cursor, row_dict, hospital_id)
            disease_id = get_or_create_disease(cursor, row_dict.get("disease_name"))

            diagnosis = normalise_string(row_dict.get("diagnosis"))

            visit_type_key = normalise_string(row_dict.get("visit_type")).lower()
            payment_key = normalise_string(row_dict.get("payment_method")).lower()

            cursor.execute(
                """
                INSERT INTO patient_visits
                (patient_id, doctor_id, hospital_id, disease_id, visit_date_id, visit_type,
                 diagnosis, treatment_id, medication_id, medication_quantity, total_cost,
                 payment_method, visit_duration_minutes, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, NULL, NULL, %s, %s, %s, 'Completed')
                """,
                (
                    patient_id,
                    doctor_id,
                    hospital_id,
                    disease_id,
                    date_id,
                    VISIT_TYPE_CANONICAL.get(visit_type_key, "OPD"),
                    diagnosis,
                    float(row_dict.get("total_cost")),
                    PAYMENT_METHOD_CANONICAL.get(payment_key, "Cash"),
                    int(row_dict.get("visit_duration_minutes")) if row_dict.get("visit_duration_minutes") else None,
                ),
            )

            cursor.execute(
                "UPDATE staging_patient_visits SET status='PROCESSED', processed_at = NOW() WHERE staging_id = %s",
                (staging_id,),
            )
            success_count += 1
        except (DataValidationError, ValueError) as validation_error:
            failure_count += 1
            cursor.execute(
                """
                UPDATE staging_patient_visits
                SET status='FAILED', error_message=%s, processed_at = NOW()
                WHERE staging_id = %s
                """,
                (str(validation_error), staging_id),
            )
        except Error as db_error:
            failure_count += 1
            cursor.execute(
                """
                UPDATE staging_patient_visits
                SET status='FAILED', error_message=%s, processed_at = NOW()
                WHERE staging_id = %s
                """,
                (str(db_error), staging_id),
            )

    job_status = 'COMPLETED' if failure_count == 0 else 'FAILED' if success_count == 0 else 'COMPLETED'

    cursor.execute(
        """
        UPDATE ingestion_jobs
        SET total_records=%s,
            success_count=%s,
            failure_count=%s,
            status=%s,
            completed_at = NOW()
        WHERE job_id = %s
        """,
        (total_records, success_count, failure_count, job_status, job_id),
    )

    connection.commit()
    cursor.close()

    return {
        "job_id": job_id,
        "total_records": total_records,
        "success_count": success_count,
        "failure_count": failure_count,
        "status": job_status,
    }


def get_ingestion_jobs(connection: MySQLConnection, limit: int = 20) -> List[Dict]:
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT job_id, job_type, source_file, total_records, success_count, failure_count,
               status, started_at, completed_at, error_message
        FROM ingestion_jobs
        ORDER BY job_id DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows
