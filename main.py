import streamlit as st
import pandas as pd
import plotly.express as px
import re
from modules.ai_engine import ask_claude

from modules.dataset_loader import load_dataset
from modules.dataset_understanding import (
    clean_column_name,
    detect_column_roles,
    infer_dataset_type,
    infer_dataset_type_ai,
    get_primary_columns,
    generate_recommended_questions,
)
from modules.analysis_router import (
    choose_analysis_path,
    choose_analysis_path_ai,
    get_best_numeric_column,
    get_best_category_column,
    get_best_metric_column,
)

from modules.smart_charts import smart_chart
from modules.explanations import generate_explanation

from modules.profiling_dashboard import run_profiling_dashboard
from modules.data_quality import run_data_quality_checks




st.title("DataSense Pilot")
df = load_dataset()






# -------- DATASET UNDERSTANDING LAYER --------

# Try converting possible date columns automatically
for col in df.columns:
    cleaned = clean_column_name(col)
    if any(word in cleaned for word in ["date", "time", "month", "year"]):
        try:
            df[col] = pd.to_datetime(df[col])
        except Exception:
            pass

detected_roles = detect_column_roles(df)
try:
    dataset_type, dataset_confidence = infer_dataset_type_ai(df)
    dataset_scores = {}
except Exception:
    dataset_type, dataset_confidence, dataset_scores = infer_dataset_type(df, detected_roles)
primary_columns = get_primary_columns(detected_roles)
recommended_questions = generate_recommended_questions(dataset_type, primary_columns, df)

st.header("Detected Dataset Understanding")

col_a, col_b = st.columns(2)

with col_a:
    st.metric("Detected Dataset Type", dataset_type)

with col_b:
    st.metric("Confidence", f"{dataset_confidence}%")

tab1, tab2, tab3, tab4 = st.tabs([
    "Dataset Understanding",
    "Profiling Dashboard",
    "Data Quality",
    "Ask Questions"
])

with tab1:
    st.subheader("Primary Column Roles")
    role_display = pd.DataFrame({
        "Role": list(primary_columns.keys()),
        "Detected Column": [primary_columns[role] if primary_columns[role] is not None else "Not detected" for role in primary_columns]
    })
    st.dataframe(role_display)

    st.subheader("All Column Role Mappings")
    role_mapping_df = pd.DataFrame({
        "Column Name": list(detected_roles.keys()),
        "Detected Roles": [", ".join(roles) for roles in detected_roles.values()]
    })
    st.dataframe(role_mapping_df)

    st.subheader("Suggested Questions for This Dataset")
    for q in recommended_questions:
        st.write(f"- {q}")

with tab2:
    run_profiling_dashboard(df, primary_columns)

with tab3:
    run_data_quality_checks(df)

with tab4:
    st.header("Ask Questions About the Dataset")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_question = st.text_input(
        "Enter your question",
        placeholder="Example: Which column has the most missing values?"
    )

    ask_button = st.button("Ask")



    if ask_button:
        if user_question.strip() == "":
            st.warning("Please enter a question before clicking Ask.")
        else:
            st.session_state.chat_history.append({
                "question": user_question,
            })

            question = user_question.lower()
            question_words = question.split()
            top_n = 10

            followup_keywords = ["same", "now", "instead", "also", "again", "what about", "how about"]
            is_followup = any(word in question for word in followup_keywords)

            if is_followup and len(st.session_state.chat_history) > 1:
                last_question = st.session_state.chat_history[-2]["question"].lower()
                st.info(f"Following up on: '{last_question}'")
                question = last_question + " " + question

            matched_columns = []
            match_scores = {}

            for col in df.columns:
                cleaned_col = clean_column_name(col)
                col_words = cleaned_col.split()

                score = 0
                for word in col_words:
                    if word in question:
                        score += 1

                if score > 0:
                    matched_columns.append(col)
                    match_scores[col] = score

            matched_columns = sorted(matched_columns, key=lambda col: match_scores[col], reverse=True)
            matched_columns = list(dict.fromkeys(matched_columns))

            top_score = match_scores[matched_columns[0]] if matched_columns else 0
            top_matches = [col for col in matched_columns if match_scores[col] == top_score]

            if len(top_matches) > 2:
                st.warning("I found multiple columns that match your question. Which one did you mean?")
                for col in top_matches:
                    st.write(f"- {col}")
                st.stop()

            matched_column = matched_columns[0] if len(matched_columns) > 0 else None

            try:
                selected_analysis, ai_column = choose_analysis_path_ai(
                    question, df, primary_columns, dataset_type
                )
                if ai_column and ai_column in df.columns:
                    matched_column = ai_column
                    matched_columns = [ai_column]
            except Exception:
                selected_analysis, ai_column = ask_claude(
                    question,
                    column_names=df.columns.tolist(),
                    dataset_type=dataset_type,
                    primary_columns=primary_columns
                )
                if not selected_analysis:
                    selected_analysis = choose_analysis_path(question, matched_columns, df, primary_columns)
                if ai_column and ai_column in df.columns:
                    matched_column = ai_column
                    matched_columns = [ai_column]

            for word in question_words:
                if word.isdigit():
                    top_n = int(word)
                    break

            st.success("Question received successfully.")
            st.write("Your question:", user_question)

            if (
                ("column" in question and "name" in question) or
                "column names" in question or
                "field names" in question or
                "headers" in question
            ):
                st.subheader("Column Names")
                st.write(list(df.columns))
                st.markdown("**Suggested next questions:**")
                st.write("- What is the shape of the dataset?")
                st.write("- Which column has the most missing values?")

            elif selected_analysis == "shape":
                st.subheader("Dataset Shape")
                st.write(f"Rows: {df.shape[0]}")
                st.write(f"Columns: {df.shape[1]}")
                st.info(generate_explanation("shape", rows=df.shape[0], cols=df.shape[1]))
                st.markdown("**Suggested next questions:**")
                st.write("- What are the column names?")
                st.write("- Which column has missing values?")

            elif selected_analysis == "missing":
                st.subheader("Missing Values Result")
                missing_summary = pd.DataFrame({
                    "Column Name": df.columns.tolist(),
                    "Missing Count": df.isnull().sum().tolist(),
                    "Missing %": ((df.isnull().sum() / len(df)) * 100).round(2).tolist()
                })
                missing_summary = missing_summary[missing_summary["Missing Count"] > 0]
                total_missing = int(df.isnull().sum().sum())

                if missing_summary.empty:
                    st.success("No missing values found in the dataset.")
                else:
                    st.dataframe(missing_summary)
                    st.info(generate_explanation("missing", missing_count=total_missing))
                    fig_missing = px.bar(missing_summary, x="Column Name", y="Missing Count", title="Missing Values by Column")
                    st.plotly_chart(fig_missing)
                    st.markdown("**Suggested next questions:**")
                    st.write("- What are the column names?")
                    st.write("- What is the shape of the dataset?")

            elif selected_analysis == "ranking":
                category_col = get_best_category_column(primary_columns, df)
                metric_col = get_best_metric_column(primary_columns=primary_columns, df=df, exclude_cols=[category_col] if category_col else [])

                if category_col is not None and metric_col is not None:
                    st.subheader(f"Top {top_n} {category_col} values by {metric_col}")
                    ranking_df = (
                        df.groupby(category_col)[metric_col]
                        .sum()
                        .sort_values(ascending=False)
                        .head(top_n)
                        .reset_index()
                    )
                    st.dataframe(ranking_df)
                    fig_ranking = smart_chart(df, x_col=category_col, y_col=metric_col, title=f"Top {top_n} {category_col} by {metric_col}", top_n=top_n)
                    st.plotly_chart(fig_ranking)
                    st.markdown("**Suggested next questions:**")
                    st.write(f"- What is the summary of {metric_col}?")
                else:
                    st.error("I could not detect suitable category and metric columns for ranking.")

            elif selected_analysis == "trend":
                date_col = primary_columns.get("date")
                metric_col = get_best_metric_column(primary_columns=primary_columns, df=df)

                if date_col and metric_col:
                    trend_df = df.groupby(date_col)[metric_col].sum().reset_index()
                    st.dataframe(trend_df)
                    fig_trend = smart_chart(df, x_col=date_col, y_col=metric_col, title=f"Trend of {metric_col} over {date_col}")
                    st.plotly_chart(fig_trend)
                    st.info(generate_explanation("trend"))
                else:
                    st.error("I could not detect a suitable date column and numeric metric column for trend analysis.")

            elif selected_analysis == "compare":
                selected_columns = matched_columns[:2]
                if len(selected_columns) < 2:
                    numeric_cols = df.select_dtypes(include="number").columns.tolist()
                    if len(numeric_cols) >= 2:
                        selected_columns = numeric_cols[:2]

                if len(selected_columns) >= 2:
                    col1 = selected_columns[0]
                    col2 = selected_columns[1]
                    st.subheader(f"Multi-column Analysis: {col1} vs {col2}")

                    if pd.api.types.is_numeric_dtype(df[col1]) and pd.api.types.is_numeric_dtype(df[col2]):
                        corr_df = df[[col1, col2]].dropna()
                        if len(corr_df) < 2:
                            st.error("Not enough valid numeric rows are available to compute correlation.")
                        else:
                            correlation_value = corr_df.corr().iloc[0, 1]
                            st.write(f"Correlation between '{col1}' and '{col2}': {correlation_value:.2f}")
                            fig_scatter = smart_chart(corr_df, x_col=col1, y_col=col2, title=f"{col1} vs {col2}")
                            st.plotly_chart(fig_scatter)
                            st.info(generate_explanation("correlation", col1=col1, col2=col2, corr=correlation_value))
                    else:
                        st.error("Both detected columns must be numeric for correlation or scatter analysis.")
                else:
                    st.error("I could not detect two suitable numeric columns for comparison.")

            elif matched_column is not None:
                st.subheader(f"Column-specific Analysis: {matched_column}")

                if any(word in question for word in ["average", "mean", "summary", "describe"]):
                    if pd.api.types.is_numeric_dtype(df[matched_column]):
                        summary_stats = df[matched_column].describe()
                        st.dataframe(summary_stats.to_frame(name="Value"))
                        st.info(generate_explanation("numeric_summary", column=matched_column, mean_value=df[matched_column].mean()))
                    else:
                        st.error(f"The column '{matched_column}' is not numeric.")

                elif selected_analysis == "distribution":
                    if pd.api.types.is_numeric_dtype(df[matched_column]):
                        fig_col_dist = smart_chart(df, x_col=matched_column, title=f"Distribution of {matched_column}")
                        st.plotly_chart(fig_col_dist)
                        st.info(generate_explanation("column_distribution", column=matched_column))
                    else:
                        st.error(f"The column '{matched_column}' is not numeric.")

                elif any(word in question for word in ["missing", "null", "blank"]):
                    missing_count = df[matched_column].isnull().sum()
                    missing_percent = (missing_count / len(df)) * 100
                    st.write(f"Missing values in '{matched_column}': {missing_count}")
                    st.write(f"Missing percentage: {missing_percent:.2f}%")
                    st.info(generate_explanation("column_missing", column=matched_column, missing_count=missing_count, missing_percent=missing_percent))

                elif selected_analysis == "top_values":
                    top_values = df[matched_column].value_counts().head(top_n).reset_index()
                    top_values.columns = [matched_column, "Count"]
                    st.dataframe(top_values)
                    fig_top_values = px.bar(top_values, x=matched_column, y="Count", title=f"Top {top_n} Values in {matched_column}")
                    st.plotly_chart(fig_top_values)
                    st.info(generate_explanation("categorical_top_values", column=matched_column))

                else:
                    st.warning(f"I detected '{matched_column}' but could not match the analysis type.")
                    st.markdown("**Try asking things like:**")
                    st.write(f"- Summary of {matched_column}")
                    st.write(f"- Distribution of {matched_column}")
                    st.write(f"- Missing values in {matched_column}")

            elif selected_analysis == "summary":
                metric_col = get_best_metric_column(primary_columns=primary_columns, df=df)
                if metric_col is not None and pd.api.types.is_numeric_dtype(df[metric_col]):
                    st.subheader(f"Summary Statistics for {metric_col}")
                    summary_df = df[metric_col].describe().reset_index()
                    summary_df.columns = ["Statistic", "Value"]
                    st.dataframe(summary_df)
                    st.info(generate_explanation("numeric_summary", column=metric_col, mean_value=df[metric_col].mean()))
                else:
                    st.error("I could not detect a suitable numeric column for summary analysis.")

            elif selected_analysis == "top_values":
                category_col = get_best_category_column(primary_columns, df)
                if category_col is not None:
                    st.subheader(f"Most Common Values in {category_col}")
                    value_counts_df = df[category_col].value_counts().head(top_n).reset_index()
                    value_counts_df.columns = [category_col, "Count"]
                    st.dataframe(value_counts_df)
                    fig_top = px.bar(value_counts_df, x=category_col, y="Count", title=f"Top {top_n} values in {category_col}")
                    st.plotly_chart(fig_top)
                    st.info(generate_explanation("categorical_top_values", column=category_col))
                else:
                    st.error("I could not detect a suitable categorical column.")

            else:
                st.warning("Sorry, I do not understand that question yet.")
                st.markdown("**Try asking questions like:**")
                st.write("- What are the column names?")
                st.write("- What is the shape of the dataset?")
                st.write("- Which column has missing values?")
                st.write("- Show sales over time")

    # ----- CONVERSATION HISTORY -----
    if "chat_history" in st.session_state and len(st.session_state.chat_history) > 0:
        st.header("Your Question History")
        for i, entry in enumerate(st.session_state.chat_history):
            st.write(f"**Q{i+1}:** {entry['question']}")