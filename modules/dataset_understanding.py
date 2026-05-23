import re
import pandas as pd
from groq import Groq
import json


def clean_column_name(col):
    return re.sub(r"[^a-z0-9]+", " ", str(col).lower()).strip()


def infer_dataset_type_ai(df):
    client = Groq(api_key="YOUR_KEY_HERE")

    system_prompt = """
You are a data analysis assistant.
Given column names of a dataset, identify what type of dataset it is.

Return ONLY a JSON object with exactly these two fields:
1. "dataset_type" - a short human readable name like "Air Quality", "Retail / Sales", "Healthcare" etc.
2. "confidence" - a number between 75 and 100. NEVER return below 75.

Rules:
- Always return a meaningful dataset type, never return "Generic Tabular"
- Always be confident — minimum confidence is 75
- Look at ALL column names together to understand the full context
- A dataset with Store, Location, Customer columns is Retail Store Operations NOT HR
- A dataset with Staff or Employee columns inside a store context is still Retail
- HR datasets have salary, department, designation, performance review columns
- Return ONLY valid JSON. No explanation. No extra text.

Example output:
{"dataset_type": "Retail Store Operations", "confidence": 88}
"""

    column_names = df.columns.tolist()

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        max_tokens=50,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Column names: {column_names}"}
        ]
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
        dataset_type = result.get("dataset_type", "Generic Tabular")
        confidence = result.get("confidence", 75)

        if confidence < 75:
            confidence = 75

        return dataset_type, confidence

    except Exception:
        return "Generic Tabular", 75


def detect_column_roles(df):
    role_keywords = {
        "date": [
            "date", "time", "month", "year", "day", "timestamp", "created", "updated"
        ],
        "id": [
            "id", "code", "number", "no", "serial", "record"
        ],
        "name": [
            "name", "title"
        ],
        "category": [
            "category", "type", "class", "group", "segment", "department", "supplier", "vendor", "item", "product", "region"
        ],
        "sales": [
            "sales", "revenue", "income", "amount", "price", "profit", "cost", "value"
        ],
        "quantity": [
            "quantity", "qty", "count", "units", "volume", "stock", "inventory", "transfer"
        ],
        "location": [
            "city", "state", "country", "location", "address", "region", "branch"
        ],
        "person": [
            "employee", "student", "customer", "patient", "person", "staff", "user", "age", "gender"
        ],
        "performance": [
            "score", "rating", "marks", "grade", "gpa", "performance"
        ]
    }

    detected_roles = {}

    for col in df.columns:
        cleaned = clean_column_name(col)
        assigned_roles = []

        for role, keywords in role_keywords.items():
            if any(keyword in cleaned for keyword in keywords):
                assigned_roles.append(role)

        if pd.api.types.is_datetime64_any_dtype(df[col]):
            if "date" not in assigned_roles:
                assigned_roles.append("date")

        if pd.api.types.is_numeric_dtype(df[col]):

            # skip location columns
            if any(word in cleaned for word in ["latitude", "longitude", "lat", "lon", "lng"]):
                if "location" not in assigned_roles:
                    assigned_roles.append("location")

            else:
                if any(word in cleaned for word in ["sales", "revenue", "amount", "price", "profit", "cost", "value"]):
                    if "sales" not in assigned_roles:
                        assigned_roles.append("sales")

                if any(word in cleaned for word in ["qty", "quantity", "count", "units", "stock", "inventory", "transfer"]):
                    if "quantity" not in assigned_roles:
                        assigned_roles.append("quantity")

        if len(assigned_roles) == 0:
            assigned_roles.append("unknown")

        detected_roles[col] = assigned_roles

    return detected_roles


def infer_dataset_type(df, detected_roles):
    dataset_scores = {
        "Retail / Sales": 0,
        "HR / Employee": 0,
        "Student / Education": 0,
        "Finance / Transactions": 0,
        "Healthcare": 0,
        "Logistics / Inventory": 0,
        "Generic Tabular": 0
    }

    column_names = [clean_column_name(col) for col in df.columns]

    for col in column_names:
        if any(word in col for word in ["sales", "revenue", "supplier", "vendor", "item", "product", "retail", "warehouse"]):
            dataset_scores["Retail / Sales"] += 2

        if any(word in col for word in ["employee", "staff", "salary", "department", "designation", "gender", "age"]):
            dataset_scores["HR / Employee"] += 2

        if any(word in col for word in ["student", "marks", "grade", "subject", "course", "gpa", "attendance", "exam"]):
            dataset_scores["Student / Education"] += 2

        if any(word in col for word in ["transaction", "account", "balance", "payment", "amount", "fraud", "credit", "debit"]):
            dataset_scores["Finance / Transactions"] += 2

        if any(word in col for word in ["patient", "disease", "hospital", "doctor", "treatment", "diagnosis", "medicine"]):
            dataset_scores["Healthcare"] += 2

        if any(word in col for word in ["inventory", "stock", "shipment", "delivery", "warehouse", "transfer", "logistics"]):
            dataset_scores["Logistics / Inventory"] += 2

    all_roles = [role for roles in detected_roles.values() for role in roles]

    if all_roles.count("sales") >= 1 and all_roles.count("category") >= 1:
        dataset_scores["Retail / Sales"] += 3

    if all_roles.count("person") >= 1 and any(
        "salary" in clean_column_name(col) or "department" in clean_column_name(col)
        for col in df.columns
    ):
        dataset_scores["HR / Employee"] += 3

    if all_roles.count("performance") >= 1 and any(
        "student" in clean_column_name(col) or "course" in clean_column_name(col)
        for col in df.columns
    ):
        dataset_scores["Student / Education"] += 3

    if any("transaction" in clean_column_name(col) for col in df.columns):
        dataset_scores["Finance / Transactions"] += 3

    if any("patient" in clean_column_name(col) for col in df.columns):
        dataset_scores["Healthcare"] += 3

    if all_roles.count("quantity") >= 1 and any(
        "warehouse" in clean_column_name(col) or "inventory" in clean_column_name(col)
        for col in df.columns
    ):
        dataset_scores["Logistics / Inventory"] += 3

    best_dataset_type = max(dataset_scores, key=dataset_scores.get)
    best_score = dataset_scores[best_dataset_type]

    total_score = sum(dataset_scores.values())
    confidence = 0 if total_score == 0 else round((best_score / total_score) * 100, 1)

    if best_score == 0:
        best_dataset_type = "Generic Tabular"
        confidence = 0.0

    return best_dataset_type, confidence, dataset_scores


def get_primary_columns(detected_roles):
    primary_columns = {
        "date": None,
        "id": None,
        "category": None,
        "sales": None,
        "quantity": None,
        "person": None,
        "performance": None
    }

    for col, roles in detected_roles.items():
        for role in roles:
            if role in primary_columns and primary_columns[role] is None:
                primary_columns[role] = col

    return primary_columns


def generate_recommended_questions(dataset_type, primary_columns, df=None):
    from groq import Groq
    import json

    client = Groq(api_key="YOUR_KEY_HERE")

    column_names = df.columns.tolist() if df is not None else list(primary_columns.values())

    system_prompt = """
You are a data analysis assistant.
Given a dataset type and its column names, generate exactly 6 useful and specific analytical questions a user might want to ask about this dataset.

Rules:
- Questions must be specific to the actual column names provided
- Mix different types: trend, ranking, summary, distribution, missing values, comparison
- Write questions in plain English as if a business user is asking
- Return ONLY a JSON array of 6 question strings
- No explanation. No extra text. Just the JSON array.

Example output:
["What is the trend of PM2_5_ug_m3 over time?", "Which city has the highest Carbon_Monoxide_ug_m3?", "What is the summary of European_AQI?"]
"""

    user_message = f"""
Dataset Type: {dataset_type}
Column Names: {column_names}

Generate 6 specific analytical questions for this dataset.
"""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            max_tokens=300,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        questions = json.loads(raw)

        if isinstance(questions, list) and len(questions) > 0:
            return questions[:6]
        else:
            return _fallback_questions(primary_columns)

    except Exception:
        return _fallback_questions(primary_columns)


def _fallback_questions(primary_columns):
    questions = []

    date_col = primary_columns.get("date")
    category_col = primary_columns.get("category")
    sales_col = primary_columns.get("sales")
    quantity_col = primary_columns.get("quantity")

    if category_col and sales_col:
        questions.append(f"What are the top 5 {category_col} values by {sales_col}?")
    if date_col and sales_col:
        questions.append(f"Show the trend of {sales_col} over time")
    if sales_col:
        questions.append(f"What is the summary of {sales_col}?")
    if category_col:
        questions.append(f"What are the most common values in {category_col}?")

    questions.extend([
        "What is the shape of the dataset?",
        "Which column has the most missing values?",
        "What are the column names?"
    ])

    questions = list(dict.fromkeys(questions))
    return questions[:6]