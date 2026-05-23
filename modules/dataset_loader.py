import streamlit as st
import pandas as pd

def load_dataset():

    uploaded_file = st.file_uploader(
        "Upload a dataset to begin analysis",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is None:
        st.warning("Please upload any data file to start the analysis.")
        st.stop()

    # FILE SIZE WARNING
    file_size_mb = uploaded_file.size / (1024 * 1024)

    if file_size_mb > 50:
        st.error(f"File size is {file_size_mb:.1f}MB — this is a very large file. Analysis may be slow or crash.")
    elif file_size_mb > 10:
        st.warning(f"File size is {file_size_mb:.1f}MB — this is a moderately large file. Some sections may take time.")
    else:
        st.info(f"File size: {file_size_mb:.1f}MB — good to go!")

    try:
        if uploaded_file.name.endswith(".csv"):
            # for large files use chunking hint
            if file_size_mb > 50:
                st.info("Large file detected — loading with optimized settings...")
                df = pd.read_csv(uploaded_file, low_memory=False)
            else:
                df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success(f"Dataset loaded successfully: {uploaded_file.name} ({file_size_mb:.1f}MB — {len(df):,} rows)")

    except Exception as e:
        st.error("We could not read this dataset.")
        st.info(f"{str(e)}")
        st.stop()

    # AUTO DATE DETECTION
    # handles both uppercase and lowercase YEAR/MONTH columns
    year_col = next((col for col in df.columns if col.lower() == "year"), None)
    month_col = next((col for col in df.columns if col.lower() == "month"), None)

    if year_col and month_col:
        try:
            df["DATE"] = pd.to_datetime(
                df[year_col].astype(str) + "-" + df[month_col].astype(str) + "-01",
                errors="coerce"
            )
            st.info(f"Auto-created DATE column from '{year_col}' and '{month_col}'.")
        except Exception:
            pass

    return df
