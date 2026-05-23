# DataSense Pilot
> AI-Powered Data Analysis Assistant — Upload any dataset and get instant intelligence.

---

## What is DataSense Pilot?

DataSense Pilot is a modular, AI-powered data analysis web application built with Python and Streamlit.

You upload any CSV or Excel dataset — and the app automatically:
- Figures out what kind of dataset it is
- Profiles it completely with charts and statistics
- Checks data quality and flags problems
- Suggests smart questions based on your data
- Answers your questions in plain English
- Generates beautiful visualizations automatically

No coding required. No manual configuration. Just upload and explore.

---

## Features

| Feature | Description |
|---|---|
|  AI Dataset Detection | Automatically identifies dataset domain with confidence score |
|  Automated EDA | Full exploratory data analysis — stats, correlations, distributions, outliers |
|  Data Quality Checks | Detects duplicates, outliers, skewness, missing values with recommendations |
|  Natural Language Q&A | Ask questions about your data in plain English |
|  AI Explanations | Every result explained in plain English using Groq LLaMA3 |
|  Smart Charts | Automatically picks the best chart type for your data |
|  Smart Questions | AI generates 6 relevant questions specific to your dataset |
|  Advanced EDA Report | Full ydata-profiling report generated on demand |
|  Conversation Memory | Remembers your previous questions for follow-up queries |
|  File Support | Supports CSV, XLSX, and XLS file formats |

---

## How It Works
User uploads dataset
↓
AI detects dataset type and column roles
↓
Full EDA and data quality checks run automatically
↓
AI generates smart suggested questions
↓
User asks a question in plain English
↓
AI understands intent and picks the right analysis
↓
Chart generated + plain English explanation shown


---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Web interface |
| Pandas | Data processing |
| Plotly | Interactive charts |
| Groq API (LLaMA3) | AI brain — intent, detection, explanations |
| ydata-profiling | Advanced EDA report generation |
| NumPy | Numerical computations |

---

## Project Structure
datasense-pilot/ │ ├── main.py # App entry point and orchestration │ └── modules/ ├── init.py ├── ai_engine.py # Groq AI integration for intent and column detection ├── analysis_router.py # Routes questions to correct analysis path ├── data_quality.py # Data quality checks and scoring ├── dataset_loader.py # File upload, loading and validation ├── dataset_understanding.py # AI dataset type and column role detection ├── explanations.py # AI-powered plain English explanations ├── intent_detection.py # Natural language intent detection ├── profiling_dashboard.py # Full EDA dashboard └── smart_charts.py # Auto chart type selection


---

## App Tabs

### Tab 1 — Dataset Understanding
- Detected dataset type with confidence score
- Primary column role mappings
- All column role assignments
- AI-generated suggested questions

### Tab 2 — Profiling Dashboard
- Dataset quick stats
- Automatic dataset summary
- Column metadata analyzer
- Numeric column statistics
- Correlation analysis and heatmap
- Outlier and distribution analysis
- Automated insight summary
- Time trend analysis
- Top performers ranking
- Categorical column analysis
- Missing values analysis
- Advanced EDA report generator

### Tab 3 — Data Quality
- Duplicate row detection
- Constant column detection
- High cardinality detection
- Possible ID column detection
- Zero-heavy column detection
- Skewness analysis with recommendations
- Outlier detection using IQR method
- Missing values with fix recommendations
- Overall data quality score out of 100

### Tab 4 — Ask Questions
- Natural language question input
- AI-powered intent detection
- Smart column matching
- Follow-up question support
- Conversation history
- Chart and plain English explanation for every answer

---

## Supported Analysis Types

| Analysis | Example Question |
|---|---|
| Shape | "How many rows does this dataset have?" |
| Missing Values | "Which columns have missing data?" |
| Trend | "Show me the sales trend over time" |
| Ranking | "What are the top 5 categories by revenue?" |
| Compare | "Compare sales and cost" |
| Summary | "Give me a summary of gross sales" |
| Distribution | "Show the distribution of prices" |
| Top Values | "What are the most common product types?" |

---

## How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/datasense-pilot.git
cd datasense-pilot
```

### 2. Install dependencies
```bash
pip install streamlit pandas plotly groq ydata-profiling openpyxl numpy python-dotenv
```

### 3. Set up your API key
Create a `.env` file in the project root and add:
GROQ_API_KEY=your_groq_api_key_here

Get your free Groq API key at: https://console.groq.com

### 4. Run the app
```bash
streamlit run main.py
```

### 5. Open in browser
http://localhost:8501


---

## Example Datasets to Try

- Retail sales data
- HR employee records
- Student grades
- Financial transactions
- Air quality measurements
- Any CSV or Excel file!

---

## Author

**Kalyan Badavath**
- GitHub: [@Kalyan-Badavath](https://github.com/Kalyan-Badavath)
- LinkedIn: [Kalyan Badavath](https://www.linkedin.com/in/kalyan-badavath-589196195ks/)

---

## License

This project is open source and available under the MIT License.

---

 If you found this project helpful, please give it a star!
