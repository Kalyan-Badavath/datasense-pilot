from groq import Groq

def generate_explanation(result_type, **kwargs):

    client = Groq(api_key="YOUR_KEY_HERE")

    # build context based on result type
    if result_type == "shape":
        context = f"Dataset has {kwargs.get('rows')} rows and {kwargs.get('cols')} columns."

    elif result_type == "missing":
        missing_count = kwargs.get("missing_count")
        if missing_count == 0:
            return "No missing values were found — the dataset appears complete."
        context = f"Dataset has {missing_count} total missing values."

    elif result_type == "trend":
        context = f"A time trend chart was shown for the dataset."

    elif result_type == "numeric_summary":
        context = f"Column '{kwargs.get('column')}' has an average value of {kwargs.get('mean_value'):,.2f}."

    elif result_type == "categorical_top_values":
        context = f"Most frequent values were shown for column '{kwargs.get('column')}'."

    elif result_type == "column_distribution":
        context = f"Distribution chart was shown for column '{kwargs.get('column')}'."

    elif result_type == "column_missing":
        context = f"Column '{kwargs.get('column')}' has {kwargs.get('missing_count')} missing values ({kwargs.get('missing_percent'):.2f}%)."

    elif result_type == "correlation":
        col1 = kwargs.get("col1")
        col2 = kwargs.get("col2")
        corr = kwargs.get("corr")
        direction = "positive" if corr > 0 else "negative"
        context = f"Correlation between '{col1}' and '{col2}' is {direction} at {corr:.2f}."

    elif result_type in ["top_supplier", "top_item_type", "ranking"]:
        category = kwargs.get("category", "category")
        value = kwargs.get("value", "")
        context = f"Top performing {category} was found with value {value}."

    else:
        context = "A data analysis result was generated."

    # send to Groq for a smart explanation
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            max_tokens=80,
            messages=[
                {
                    "role": "system",
                    "content": """You are a data analysis assistant.
Given a data analysis result, write a clear, helpful, 2-3 sentence explanation in plain English.
Be specific, insightful and helpful. No bullet points. No headers. Just plain sentences."""
                },
                {
                    "role": "user",
                    "content": f"Explain this result to the user: {context}"
                }
            ]
        )
        return response.choices[0].message.content.strip()

    except Exception:
        return context