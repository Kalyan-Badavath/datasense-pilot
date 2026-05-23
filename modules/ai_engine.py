from groq import Groq
import json

def ask_claude(question, column_names, dataset_type, primary_columns):

    client = Groq(api_key="PASTE_YOUR_KEY_HERE")

    system_prompt = f"""
You are a data analysis assistant. A user has uploaded a dataset and asked a question.

Dataset Information:
- Dataset Type: {dataset_type}
- Column Names: {column_names}
- Primary Columns Detected: {primary_columns}

Based on the user's question, return a JSON object with exactly these two fields:
1. "intent" - one of: shape, missing, trend, ranking, compare, summary, distribution, top_values, unknown
2. "column" - the most relevant column name from the list above, or null if not applicable

Rules:
- For trend questions pick a meaningful numeric metric column, NOT latitude or longitude
- For ranking questions pick a category column and a metric column
- For summary pick the most relevant numeric column
- If question is vague like "explain data" or "describe" return intent as "summary"
- Return ONLY valid JSON. No explanation. No extra text.

Example output:
{{"intent": "trend", "column": "PM2_5_ug_m3"}}
"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        max_tokens=50,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
        intent = result.get("intent", "unknown").lower()
        column = result.get("column", None)

        valid_intents = [
            "shape", "missing", "trend", "ranking",
            "compare", "summary", "distribution", "top_values"
        ]

        if intent not in valid_intents:
            intent = "unknown"

        return intent, column

    except Exception:
        return "unknown", None