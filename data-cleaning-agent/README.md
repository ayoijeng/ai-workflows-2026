# Data Cleaning Agent

An AI-powered data cleaning agent that automatically cleans messy datasets using LangChain and LangGraph. The agent uses an LLM to generate and execute Python code for common data cleaning tasks like handling missing values, removing duplicates, and dropping low-quality columns.

A Streamlit web interface lets you explore uploaded CSVs, review data quality, run basic EDA, and compare results before and after AI-powered cleaning.

## How It Works

The agent follows a simple workflow:
1. **Analyze**: Examines your dataset structure and identifies data quality issues
2. **Generate**: Uses an LLM to create custom Python cleaning code based on the data
3. **Execute**: Runs the generated code to clean your data
4. **Retry**: Automatically fixes errors if the generated code fails (up to 3 attempts)

This approach combines the flexibility of LLMs with the reliability of pandas operations.

## Streamlit Web Interface

The app provides an interactive workflow for exploring and cleaning CSV files:

| Tab | Features |
|-----|----------|
| **Preview** | Scrollable data preview and column type summary |
| **Data Quality** | Per-column missing/unique stats, duplicate counts, missing-value chart |
| **EDA** | Numeric `describe()`, categorical value counts, correlation heatmap |
| **Visualizations** | Column distributions and scatter plots with configurable axes |
| **Clean & Compare** | Before/after quality metrics, missing-value comparison, cleaned preview |

**Sidebar controls:**
- CSV file upload
- Optional custom cleaning instructions
- One-click AI cleaning
- Download cleaned CSV after processing

## Setup

### Prerequisites

- **Python 3.9 or higher** (3.9, 3.10, 3.11, 3.12, or 3.13) - **Note**: Python 3.9.7 is not supported due to a Streamlit compatibility issue
- **Poetry** (dependency manager)
- **OpenAI API Key**

### Installation Steps

1. **Install Poetry** (if not already installed):
   
   **Windows (PowerShell)**:
   ```powershell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
   ```
   
   **macOS/Linux**:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
   
   After installation, restart your terminal. If `poetry` command is not found:
   - **Windows**: Add `%APPDATA%\Python\Scripts` to your system PATH
   - **macOS/Linux**: Add `export PATH="$HOME/.local/bin:$PATH"` to your `~/.bashrc` or `~/.zshrc`

2. **Install dependencies**:
   ```bash
   poetry install
   ```
   
   This will install all dependencies with the exact versions specified in `poetry.lock`, ensuring consistency across all environments.

3. **Set up your OpenAI API key**:
   
   **Windows**:
   ```powershell
   copy .env.example .env
   ```
   
   **macOS/Linux**:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

### Multiple Python Versions?

If you have multiple Python versions installed and want to use a specific one:

```bash
# Tell Poetry which Python to use
poetry env use python3.11  # or python3.9, python3.10, python3.12, etc.

# Then install dependencies
poetry install
```

Poetry will create a virtual environment with your chosen Python version.

## Usage

### Streamlit Web Interface (Local)

Run the app from the `data-cleaning-agent` directory:

```bash
poetry run streamlit run app.py
```

Then open the URL shown in the terminal (default: `http://localhost:8501`) and:

1. Upload your CSV file
2. Explore data quality, EDA, and visualizations in the tabs
3. Optionally add custom cleaning instructions in the sidebar
4. Click **Clean Data**
5. Review the before/after comparison and download the cleaned dataset

### Python API

For programmatic use or integration into data pipelines:

```python
import pandas as pd
from langchain_openai import ChatOpenAI
from data_cleaning_agent import LightweightDataCleaningAgent

# Initialize the agent with an LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = LightweightDataCleaningAgent(model=llm)

# Load your messy data
df = pd.read_csv("your_data.csv")

# Run the cleaning agent
agent.invoke_agent(data_raw=df)

# Get the cleaned dataset
cleaned_df = agent.get_data_cleaned()

# Save or use the cleaned data
cleaned_df.to_csv("cleaned_data.csv", index=False)
```

**Optional: Provide custom instructions**

```python
# Give specific cleaning instructions to the agent
agent.invoke_agent(
    data_raw=df,
    user_instructions="Remove columns with more than 30% missing values and standardize date formats"
)
```

## Docker Deployment

The app can be packaged and run in a container using the included `Dockerfile`.

### Build the image

From the `data-cleaning-agent` directory:

```bash
docker build -t data-cleaning-agent .
```

### Run the container

Pass your OpenAI API key as an environment variable at runtime. **Do not bake secrets into the image.**

```bash
docker run --rm -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key-here \
  data-cleaning-agent
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Run with a `.env` file

```bash
docker run --rm -p 8501:8501 --env-file .env data-cleaning-agent
```

### Docker notes

- The container listens on port **8501** and binds to `0.0.0.0` so it is reachable from the host.
- A health check polls Streamlit's `/_stcore/health` endpoint.
- Only production dependencies are installed (`poetry install --only main`).
- Generated agent logs are written inside the container unless you mount a volume:

```bash
docker run --rm -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key-here \
  -v "$(pwd)/logs:/app/logs" \
  data-cleaning-agent
```

## Project Structure

```
data-cleaning-agent/
├── data_cleaning_agent/
│   ├── __init__.py
│   ├── data_cleaning_agent.py  # Main agent class
│   └── utils.py                # Utility functions
├── data/
│   └── sample_data.csv         # Sample dataset for testing
├── app.py                      # Streamlit interface
├── streamlit_helpers.py        # Data quality, EDA, and chart helpers
├── Dockerfile                  # Container build definition
├── .dockerignore               # Files excluded from Docker build context
├── pyproject.toml              # Dependencies configuration
├── poetry.lock                 # Locked dependency versions
└── README.md
```

**Important**: The `poetry.lock` file is committed to ensure all users get identical, tested dependency versions.
