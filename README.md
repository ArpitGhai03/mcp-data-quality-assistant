# MCP Data Quality Assistant 🤖📊

An AI-powered data quality and consistency monitoring system built using **MCP (Model Context Protocol)** and **Ollama (local LLMs)**.

It uses PostgreSQL for production and staging databases, detects data inconsistencies (missing rows, mismatches, data corruption), and enables natural language analysis through an AI agent with tool-calling capabilities via MCP protocol.

---

## 🚀 Features

- 🗄️ PostgreSQL Production & Staging databases with environment-based configuration
- 📉 Data quality analysis (missing rows, mismatches, quality score)
- 🤖 AI assistant powered by Ollama (LLaMA3 / Gemma)
- 🔌 MCP server for tool exposure to external AI clients (Claude Desktop compatible)
- 📊 Streamlit dashboard with interactive visualizations
- 📄 Automated report generation and export
- 🧠 Tool-based AI reasoning system (LLM selects and uses tools)

---

## 🏗️ Architecture

User Query → Ollama LLM → MCP Tools → PostgreSQL Databases → Analysis Result → AI Explanation

---

## 🧰 Tech Stack

- Python 3.11
- PostgreSQL 12+
- Ollama (local LLM runtime)
- MCP (Model Context Protocol)
- Streamlit
- Pandas
- Faker
- Plotly

---


## ⚙️ How It Works

1. Synthetic data is generated for production and staging databases
2. MCP tools analyze data inconsistencies
3. Ollama LLM receives user query and selects appropriate tools
4. MCP server executes tools and returns structured results
5. AI generates human-readable explanations
6. Streamlit dashboard visualizes results interactively

---

## 💬 Example Queries

- What is the data quality score?
- Show missing records in staging
- Why is staging different from production?
- Generate a full comparison report

---

## 🖥️ How to Run

### Prerequisites

**1. PostgreSQL Setup**
```bash
# Create .env file with your PostgreSQL credentials
echo "PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=your_password
PROD_DB_NAME=prod
STAGING_DB_NAME=staging" > .env

# Create the two databases in PostgreSQL
createdb prod
createdb staging
```

**2. Python Environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r src/requirements.txt
```

### Quick Start (Recommended)

```bash
# Initialize databases (creates tables and seed data)
python db_setup/init_db.py

# Start everything with automatic orchestration
python run_app.py
```

The `run_app.py` launcher automatically:
- Checks and starts Ollama if not running
- Launches the Streamlit dashboard on port 8503
- Opens dashboard in default browser
- Optionally starts the AI agent

**Options:**
```bash
python run_app.py --agent           # Include AI agent
python run_app.py --no-browser      # Don't auto-open browser
python run_app.py --agent --no-browser
```

### Individual Services

**Reset & Reinitialize Databases:**
```bash
python db_setup/init_db.py --reset
```

**CLI Agent:**
```bash
python src/agent.py
```

**MCP Server:**
```bash
python src/mcp_server.py
```

**CLI Comparison Report:**
```bash
python src/compare.py
```

**Web Dashboard:**
```bash
streamlit run src/dashboard.py
```

---

## 🧠 What This Project Demonstrates
MCP-based tool architecture
LLM tool-calling systems (agentic AI)
Data quality engineering concepts
Multi-interface AI system (CLI + MCP + Web UI)
End-to-end system design thinking

---

## 📊 Sample Results
Data Quality Score: 83%
Missing Records: 9%
Mismatched Records: 8%
System Status: ⚠️ Needs Attention

---

## � Documentation

For detailed component documentation, see [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

## 🔮 Future Improvements
- Cloud deployment (AWS/Azure)
- Advanced data quality metrics
- ML-based anomaly detection
Real-time data pipelines
Multi-user authentication system
Advanced anomaly detection
Scheduled monitoring jobs

---

## 👤 Author
Built by Arpit Ghai
