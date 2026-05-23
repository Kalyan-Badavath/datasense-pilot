import pandas as pd
from .intent_detection import detect_question_intent


def choose_analysis_path(question, matched_columns, df, primary_columns):
    intent = detect_question_intent(question)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    object_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_col = primary_columns.get("date")
    category_col = get_best_category_column(primary_columns, df)
    metric_col = get_best_metric_column(primary_columns=primary_columns, df=df)

    # direct intent mapping first
    if intent in ["shape", "missing", "trend", "ranking", "compare", "summary", "distribution", "top_values"]:
        return intent

    # fallback logic when question is vague
    if len(matched_columns) >= 2:
        if all(pd.api.types.is_numeric_dtype(df[col]) for col in matched_columns[:2]):
            return "compare"

    if len(matched_columns) == 1:
        col = matched_columns[0]

        if pd.api.types.is_numeric_dtype(df[col]):
            return "summary"

        if df[col].dtype == "object" or str(df[col].dtype) == "category":
            return "top_values"

    if date_col is not None and metric_col is not None:
        return "trend"

    if category_col is not None and metric_col is not None:
        return "ranking"

    if len(numeric_cols) >= 2:
        return "compare"

    if len(numeric_cols) == 1:
        return "summary"

    if len(object_cols) >= 1:
        return "top_values"

    return "unknown"


def choose_analysis_path_ai(question, df, primary_columns, dataset_type):
    from groq import Groq
    import json

    client = Groq(api_key="YOUR_KEY_HERE")

    system_prompt = f"""
You are a data analysis assistant. A user has uploaded a dataset and asked a question.

Dataset Information:
- Dataset Type: {dataset_type}
- Column Names: {df.columns.tolist()}
- Primary Columns: {primary_columns}

Based on the user's question, return a JSON object with exactly these two fields:
1. "intent" - one of: shape, missing, trend, ranking, compare, summary, distribution, top_values, unknown
2. "column" - the single most relevant column name from the list above, or null if not applicable

Rules:
- For trend questions pick a meaningful numeric metric column NOT latitude or longitude
- For ranking questions pick the most relevant category column
- For summary pick the most relevant numeric column
- If question is vague like "explain data" or "describe" return intent as "summary"
- Return ONLY valid JSON. No explanation. No extra text.

Example output:
{{"intent": "trend", "column": "PM2_5_ug_m3"}}
"""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            max_tokens=50,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        result = json.loads(raw)
        intent = result.get("intent", "unknown").lower()
        column = result.get("column", None)

        valid_intents = [
            "shape", "missing", "trend", "ranking",
            "compare", "summary", "distribution", "top_values"
        ]

        if intent not in valid_intents:
            intent = "unknown"

        # validate column exists in dataframe
        if column and column not in df.columns:
            column = None

        return intent, column

    except Exception:
        return "unknown", None


def get_best_numeric_column(df, exclude_cols=None):
    if exclude_cols is None:
        exclude_cols = []

    numeric_cols = [
        col for col in df.select_dtypes(include="number").columns
        if col not in exclude_cols
    ]

    if not numeric_cols:
        return None

    return numeric_cols[0]


def get_best_category_column(primary_columns, df):
    if primary_columns.get("category") is not None:
        return primary_columns["category"]

    object_cols = df.select_dtypes(include="object").columns.tolist()
    return object_cols[0] if object_cols else None


def get_best_metric_column(primary_columns, df, exclude_cols=None):
    if exclude_cols is None:
        exclude_cols = []

    if primary_columns.get("sales") is not None and primary_columns["sales"] not in exclude_cols:
        return primary_columns["sales"]

    if primary_columns.get("quantity") is not None and primary_columns["quantity"] not in exclude_cols:
        return primary_columns["quantity"]

    if primary_columns.get("performance") is not None and primary_columns["performance"] not in exclude_cols:
        return primary_columns["performance"]

    return get_best_numeric_column(df, exclude_cols=exclude_cols)