import pandas as pd
import plotly.express as px

def smart_chart(df, x_col=None, y_col=None, title="Chart", top_n=None):

    if x_col and y_col:

        # date vs metric → line chart with area fill
        if pd.api.types.is_datetime64_any_dtype(df[x_col]):
            fig = px.area(
                df, x=x_col, y=y_col,
                title=title,
                template="plotly_dark"
            )
            fig.update_traces(line_color="#00C9FF", fillcolor="rgba(0,201,255,0.1)")

        # numeric vs numeric → scatter with trendline
        elif pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
            fig = px.scatter(
                df, x=x_col, y=y_col,
                title=title,
                trendline="ols",
                template="plotly_dark",
                opacity=0.6
            )

        # category vs metric → ranked bar chart with color scale
        elif df[x_col].dtype == "object" and pd.api.types.is_numeric_dtype(df[y_col]):
            grouped = (
                df.groupby(x_col)[y_col]
                .sum()
                .sort_values(ascending=False)
            )
            if top_n:
                grouped = grouped.head(top_n)
            grouped = grouped.reset_index()
            fig = px.bar(
                grouped, x=x_col, y=y_col,
                title=title,
                color=y_col,
                color_continuous_scale="Blues",
                template="plotly_dark"
            )

        # metric vs category → flip and do bar
        elif pd.api.types.is_numeric_dtype(df[x_col]) and df[y_col].dtype == "object":
            grouped = (
                df.groupby(y_col)[x_col]
                .sum()
                .sort_values(ascending=False)
            )
            if top_n:
                grouped = grouped.head(top_n)
            grouped = grouped.reset_index()
            fig = px.bar(
                grouped, x=y_col, y=x_col,
                title=title,
                color=x_col,
                color_continuous_scale="Blues",
                template="plotly_dark"
            )

        else:
            fig = px.bar(df, x=x_col, y=y_col, title=title, template="plotly_dark")

    elif x_col:

        # numeric → histogram with box on top
        if pd.api.types.is_numeric_dtype(df[x_col]):
            fig = px.histogram(
                df, x=x_col,
                nbins=50,
                title=title,
                marginal="box",
                template="plotly_dark",
                color_discrete_sequence=["#00C9FF"]
            )

        # categorical → horizontal bar for better readability
        else:
            value_counts = df[x_col].value_counts()
            if top_n:
                value_counts = value_counts.head(top_n)
            value_counts = value_counts.reset_index()
            value_counts.columns = [x_col, "Count"]
            fig = px.bar(
                value_counts,
                x="Count", y=x_col,
                title=title,
                orientation="h",
                color="Count",
                color_continuous_scale="Blues",
                template="plotly_dark"
            )

    else:
        return None

    # apply to all charts
    fig.update_layout(
        title_font_size=18,
        title_font_color="#00C9FF",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig