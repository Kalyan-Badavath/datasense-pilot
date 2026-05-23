import streamlit as st
import pandas as pd
import numpy as np

def run_data_quality_checks(df):

    st.header("Data Quality Checks")

    # DUPLICATE ROWS
    st.subheader("Duplicate Rows")
    duplicate_count = df.duplicated().sum()

    if duplicate_count == 0:
        st.success("No duplicate rows found in the dataset.")
    else:
        st.warning(f"The dataset contains {duplicate_count} duplicate rows.")
        st.write("**Recommendation:** Consider removing duplicates using `df.drop_duplicates()`")
        duplicate_rows = df[df.duplicated()]
        st.dataframe(duplicate_rows.head(10))


    # CONSTANT COLUMNs
    st.subheader("Constant Columns")
    constant_columns = [col for col in df.columns if df[col].nunique() == 1]

    if len(constant_columns) == 0:
        st.success("No constant columns detected.")
    else:
        for col in constant_columns:
            st.write(f"- **{col}** contains only one unique value.")
        st.warning("**Recommendation:** Constant columns add no value to analysis. Consider dropping them.")


    #HIGH CARDINALITY COLUMNS
    st.subheader("High Cardinality Columns")
    high_cardinality = []

    for col in df.select_dtypes(include=['object']).columns:
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio > 0.5:
            high_cardinality.append(col)

    if len(high_cardinality) == 0:
        st.info("No high-cardinality categorical columns detected.")
    else:
        for col in high_cardinality:
            st.write(f"- **{col}** has a very high number of unique values.")
        st.warning("**Recommendation:** High cardinality columns may be ID columns or free text. Consider encoding or dropping them.")


    # POSSIBLE ID COLUMNS
    st.subheader("Possible Identifier Columns")
    id_columns = []

    for col in df.columns:
        if df[col].nunique() == len(df):
            id_columns.append(col)

    if len(id_columns) == 0:
        st.info("No obvious identifier columns detected.")
    else:
        for col in id_columns:
            st.write(f"- **{col}** appears to be a unique identifier column.")
        st.warning("**Recommendation:** ID columns should be excluded from analysis and modeling.")


    # ZERO-HEAVY NUMERIC COLUMNS
    st.subheader("Zero-heavy Numeric Columns")
    zero_heavy_cols = []
    numeric_df = df.select_dtypes(include=['number'])

    if numeric_df.empty:
        st.info("No numeric columns available for zero-heavy analysis.")
    else:
        for col in numeric_df.columns:
            zero_ratio = (numeric_df[col] == 0).sum() / len(numeric_df)
            if zero_ratio > 0.8:
                zero_heavy_cols.append((col, zero_ratio))

        if len(zero_heavy_cols) == 0:
            st.info("No zero-heavy numeric columns detected.")
        else:
            for col, ratio in zero_heavy_cols:
                st.write(f"- **{col}** contains {ratio:.0%} zero values.")
            st.warning("**Recommendation:** Zero-heavy columns may indicate sparse data or missing values coded as zero.")


    # SKEWNESS ANALYSIS
    st.subheader("Skewness Analysis")

    if numeric_df.empty:
        st.info("No numeric columns available for skewness analysis.")
    else:
        skewness_data = []

        for col in numeric_df.columns:
            skew_val = numeric_df[col].skew()
            if abs(skew_val) > 1:
                level = "Highly Skewed"
                recommendation = "Consider log transformation or normalization"
            elif abs(skew_val) > 0.5:
                level = "Moderately Skewed"
                recommendation = "May benefit from transformation"
            else:
                level = "Normal"
                recommendation = "No transformation needed"

            skewness_data.append({
                "Column": col,
                "Skewness": round(skew_val, 3),
                "Level": level,
                "Recommendation": recommendation
            })

        skewness_df = pd.DataFrame(skewness_data)
        st.dataframe(skewness_df)


    # OUTLIER DETECTION
    st.subheader("Outlier Detection (IQR Method)")

    if numeric_df.empty:
        st.info("No numeric columns available for outlier detection.")
    else:
        outlier_data = []

        for col in numeric_df.columns:
            Q1 = numeric_df[col].quantile(0.25)
            Q3 = numeric_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outlier_count = ((numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)).sum()
            outlier_percent = round((outlier_count / len(df)) * 100, 2)

            if outlier_count > 0:
                outlier_data.append({
                    "Column": col,
                    "Outlier Count": outlier_count,
                    "Outlier %": outlier_percent,
                    "Lower Bound": round(lower_bound, 2),
                    "Upper Bound": round(upper_bound, 2),
                    "Recommendation": "Consider capping, removing, or investigating these outliers"
                })

        if len(outlier_data) == 0:
            st.success("No significant outliers detected in any numeric column.")
        else:
            outlier_df = pd.DataFrame(outlier_data)
            st.dataframe(outlier_df)
            st.warning(f"**{len(outlier_data)} columns** have outliers. Review them before modeling.")


    # MISSING VALUES
    st.subheader("Missing Values Analysis")

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

        for _, row in missing_summary.iterrows():
            if row["Missing %"] > 50:
                st.write(f"- **{row['Column Name']}** has {row['Missing %']}% missing → Consider **dropping** this column")
            elif row["Missing %"] > 20:
                st.write(f"- **{row['Column Name']}** has {row['Missing %']}% missing → Consider **imputation** (mean/median/mode)")
            else:
                st.write(f"- **{row['Column Name']}** has {row['Missing %']}% missing → Safe to **impute or drop rows**")


    # OVERALL DATA QUALITY SCORE
    st.subheader("Overall Data Quality Score")

    score = 100

    if duplicate_count > 0:
        score -= 10
    if len(constant_columns) > 0:
        score -= 5
    if len(high_cardinality) > 0:
        score -= 5
    if not missing_summary.empty:
        score -= min(20, int(missing_summary["Missing %"].max()))
    if len(outlier_data) > 0 if 'outlier_data' in dir() else False:
        score -= min(10, len(outlier_data) * 2)

    score = max(0, score)

    if score >= 80:
        st.success(f"Data Quality Score: {score}/100 — Good quality dataset!")
    elif score >= 60:
        st.warning(f"Data Quality Score: {score}/100 — Moderate quality, some issues found.")
    else:
        st.error(f"Data Quality Score: {score}/100 — Poor quality, significant issues detected.")
