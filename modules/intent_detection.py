def detect_question_intent(question):
    question = question.lower()

    # SHAPE
    if any(word in question for word in [
        "shape", "rows", "columns count", "size of dataset", 
        "how big", "how many rows", "how many columns", "dimension"
    ]):
        return "shape"

    # MISSING
    if any(word in question for word in [
        "missing", "null", "blank", "empty", "nan",
        "incomplete", "not filled", "no value"
    ]):
        return "missing"

    # COMPARE
    if any(word in question for word in [
        "correlation", "relationship", "compare", "vs", 
        "between", "scatter", "versus", "difference between",
        "relate", "connected"
    ]):
        return "compare"

    # TREND
    if any(word in question for word in [
        "trend", "over time", "time series", "monthly trend",
        "trend over months", "changed over", "growth", "decline",
        "over months", "over years", "across time", "how did",
        "pattern over", "monthly", "yearly", "weekly"
    ]):
        return "trend"

    # RANKING
    if any(word in question for word in [
        "top", "best", "highest", "largest", "performing",
        "rank", "leading", "most", "maximum", "greatest",
        "who is the best", "which is the best", "winner",
        "worst", "lowest", "bottom", "least"
    ]):
        return "ranking"

    # SUMMARY
    if any(word in question for word in [
        "average", "mean", "summary", "describe", "statistics",
        "median", "std", "standard deviation", "min", "max",
        "overall", "aggregate", "total", "sum", "how much"
    ]):
        return "summary"

    # DISTRIBUTION
    if any(word in question for word in [
        "distribution", "histogram", "spread", "range",
        "how spread", "skewed", "outlier", "concentrated"
    ]):
        return "distribution"

    # TOP VALUES
    if any(word in question for word in [
        "top values", "most common", "frequent values",
        "common values", "breakdown", "categories",
        "unique values", "value counts", "how many types"
    ]):
        return "top_values"

    return "unknown"