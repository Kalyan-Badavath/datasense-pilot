import streamlit as st
import pandas as pd
import plotly.express as px
from ydata_profiling import ProfileReport
import streamlit.components.v1 as components
from modules.smart_charts import smart_chart

def run_profiling_dashboard(df, primary_columns=None):

    if primary_columns is None:
        primary_columns = {}

    # ----- QUICK DATASET STATS -----
    st.header("Dataset Quick Stats")

    total_rows = df.shape[0]
    total_columns = df.shape[1]
    numeric_columns = len(df.select_dtypes(include=['number']).columns)
    categorical_columns = len(df.select_dtypes(include=['object']).columns)
    missing_values = df.isnull().sum().sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Rows", total_rows)
    col2.metric("Total Columns", total_columns)
    col3.metric("Numeric Columns", numeric_columns)
    col4.metric("Categorical Columns", categorical_columns)
    col5.metric("Missing Values", missing_values)


    # ----- AUTOMATIC DATASET SUMMARY -----
    st.header("Automatic Dataset Summary")

    summary_points = []

    summary_points.append(f"This dataset contains {total_rows} rows and {total_columns} columns.")
    summary_points.append(f"It includes {numeric_columns} numeric columns and {categorical_columns} categorical columns.")

    if missing_values == 0:
        summary_points.append("No missing values were detected in the dataset.")
    else:
        summary_points.append(f"The dataset contains {missing_values} missing values in total.")

    date_col = primary_columns.get("date")
    if date_col:
        summary_points.append(f"A date column '{date_col}' is available, so time-based trend analysis can be performed.")
    else:
        summary_points.append("No obvious time-related column was detected for trend analysis.")

    numeric_df = df.select_dtypes(include=['number'])
    if not numeric_df.empty:
        highest_mean_col = numeric_df.mean().idxmax()
        summary_points.append(f"Among numeric fields, '{highest_mean_col}' has the highest average value.")

    for point in summary_points:
        st.write(f"- {point}")


    # ----- DATASET OVERVIEW -----
    st.header("Dataset Overview")
    st.write(f"Total Rows: {total_rows}")
    st.write(f"Total Columns: {total_columns}")
    st.subheader("Column Names")
    st.write(list(df.columns))


    # ----- COLUMN METADATA ANALYZER -----
    st.header("Column Metadata Analyzer")

    column_summary = pd.DataFrame({
        "Column Name": df.columns.tolist(),
        "Data Type": df.dtypes.astype(str).tolist(),
        "Missing Values": df.isnull().sum().tolist(),
        "Missing %": ((df.isnull().sum() / len(df)) * 100).round(2).tolist(),
        "Unique Values": df.nunique().tolist()
    })
    st.dataframe(column_summary)


    # ----- NUMERIC COLUMN ANALYSIS -----
    st.header("Numeric Column Analysis")

    if numeric_df.empty:
        st.info("No numeric columns are available for numeric analysis.")
    else:
        numeric_summary = numeric_df.describe().T
        st.dataframe(numeric_summary)


    # ----- CORRELATION ANALYSIS -----
    st.header("Correlation Analysis")

    correlation_matrix = pd.DataFrame()

    if numeric_df.shape[1] < 2:
        st.info("At least two numeric columns are needed for correlation analysis.")
    else:
        correlation_matrix = numeric_df.corr()
        st.dataframe(correlation_matrix)

        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            color_continuous_scale="RdBu",
            title="Correlation Heatmap"
        )
        st.plotly_chart(fig, key=f"correlation_heatmap_{len(correlation_matrix.columns)}")


    # ----- OUTLIER AND DISTRIBUTION ANALYSIS -----
    st.header("Outlier and Distribution Analysis")

    if numeric_df.empty:
        st.info("No numeric columns are available for outlier and distribution analysis.")
    else:
        for col in numeric_df.columns:
            st.subheader(f"{col}")

            fig_hist = smart_chart(df, x_col=col, title=f"Distribution of {col}")
            if fig_hist:
                st.plotly_chart(fig_hist, key=f"hist_{col}")

            fig_box = px.box(
                df, y=col,
                title=f"Box Plot of {col}",
                template="plotly_dark",
                color_discrete_sequence=["#00C9FF"]
            )
            fig_box.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                title_font_color="#00C9FF"
            )
            st.plotly_chart(fig_box, key=f"box_{col}")

    # ----- AUTOMATED INSIGHT SUMMARY -----
    st.header("Automated Insight Summary")

    insights = []

    insights.append(f"The dataset contains {total_rows} rows and {total_columns} columns.")

    # generic - uses detected category column instead of hardcoded ITEM TYPE
    category_col = primary_columns.get("category")
    if category_col and category_col in df.columns:
        top_category_value = df[category_col].mode()[0]
        insights.append(f"The most frequent value in '{category_col}' is '{top_category_value}'.")

    if not numeric_df.empty:
        highest_mean_col = numeric_df.mean().idxmax()
        highest_mean_value = numeric_df.mean().max()
        insights.append(f"The numeric column with the highest average value is '{highest_mean_col}' with an average of {highest_mean_value:.2f}.")

    if correlation_matrix.shape[0] > 1:
        corr_pairs = correlation_matrix.where(~correlation_matrix.isna(), 0).copy()
        for col in corr_pairs.columns:
            corr_pairs.loc[col, col] = 0

        max_corr = corr_pairs.abs().max().max()
        if max_corr > 0:
            strongest_pair = corr_pairs.abs().stack().idxmax()
            col1, col2 = strongest_pair
            corr_value = correlation_matrix.loc[col1, col2]
            insights.append(f"The strongest relationship is between '{col1}' and '{col2}' with a correlation of {corr_value:.2f}.")

    total_missing = df.isnull().sum().sum()
    if total_missing == 0:
        insights.append("No missing values were found in the dataset.")
    else:
        insights.append(f"The dataset contains {total_missing} missing values in total.")

    for insight in insights:
        st.write(f"- {insight}")


    # ----- TIME TREND ANALYSIS -----
    st.header("Time Trend Analysis")

    date_col = primary_columns.get("date")
    metric_col = primary_columns.get("sales") or primary_columns.get("quantity") or primary_columns.get("performance")

    if date_col and metric_col and date_col in df.columns and metric_col in df.columns:
        time_trend = (
            df.groupby(date_col)[metric_col]
            .sum()
            .reset_index()
        )

        fig_time = smart_chart(
            time_trend,
            x_col=date_col,
            y_col=metric_col,
            title=f"Trend of {metric_col} over {date_col}"
        )
        if fig_time:
            st.plotly_chart(fig_time, key="time_trend_chart")
    else:
        st.info("Time trend analysis requires a detected date column and a numeric metric column.")


    # ----- TOP PERFORMERS / RANKING ANALYSIS -----
    st.header("Top Performers / Ranking Analysis")

    category_col = primary_columns.get("category")
    metric_col = primary_columns.get("sales") or primary_columns.get("quantity") or primary_columns.get("performance")

    if category_col and metric_col and category_col in df.columns and metric_col in df.columns:
        top_performers = (
            df.groupby(category_col)[metric_col]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        st.subheader(f"Top 10 {category_col} values by {metric_col}")
        st.dataframe(top_performers)

        fig_top = smart_chart(
            top_performers,
            x_col=category_col,
            y_col=metric_col,
            title=f"Top 10 {category_col} by {metric_col}",
            top_n=10
        )
        if fig_top:
            st.plotly_chart(fig_top, key="top_performers_chart")
    else:
        st.info("Top performers analysis requires a detected category column and a numeric metric column.")


    # ----- CATEGORICAL COLUMN ANALYSIS -----
    st.header("Categorical Column Analysis")

    categorical_df = df.select_dtypes(include=['object'])

    if categorical_df.empty:
        st.info("No categorical columns are available for categorical analysis.")
    else:
        for col in categorical_df.columns:
            st.subheader(col)
            st.write(f"Unique Values: {df[col].nunique()}")

            top_values = df[col].value_counts().head(10).reset_index()
            top_values.columns = [col, "Count"]
            st.dataframe(top_values)


    # ----- MISSING VALUES ANALYSIS -----
    st.header("Missing Values Analysis")

    missing_summary = pd.DataFrame({
        "Column Name": df.columns.tolist(),
        "Missing Count": df.isnull().sum().tolist(),
        "Missing %": ((df.isnull().sum() / len(df)) * 100).round(2).tolist()
    })

    missing_summary = missing_summary[missing_summary["Missing Count"] > 0]

    if missing_summary.empty:
        st.success("No missing values found in the dataset.")
    else:
        st.dataframe(missing_summary)


    # ----- DATASET PREVIEW -----
    st.header("Dataset Preview")
    st.dataframe(df.head())


    # ----- ADVANCED EDA REPORT -----
    st.header("Advanced EDA Report")

    if st.button("Generate Full EDA Report"):
        with st.spinner("Generating advanced EDA report... this may take a minute for large datasets"):
            profile = ProfileReport(
                df,
                title="DataSense Pilot - EDA Report",
                explorative=True
            )
            report_html = profile.to_html()
            components.html(report_html, height=800, scrolling=True)