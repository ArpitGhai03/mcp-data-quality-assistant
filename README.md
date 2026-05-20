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
- 🔄 **Data Migration Tool** with dry-run preview, automatic backups, and rollback capability

---

## 🏗️ Architecture

User Query → Ollama LLM → MCP Tools → PostgreSQL Databases → Analysis Result → AI Explanation

---

## 🧰 Tech Stack

- Python 3.11
- PostgreSQL 12+ (production & staging databases)
- psycopg2 (PostgreSQL adapter)
- Ollama (local LLM runtime)
- MCP (Model Context Protocol)
- Streamlit (web dashboard)
- Plotly (interactive visualizations)
- Faker (synthetic test data generation)
- python-dotenv (environment configuration)

---


## ⚙️ How It Works

1. PostgreSQL databases are initialized with seeded test data (Faker generates realistic fake records)
2. Production database contains 500 complete records
3. Staging database contains ~400 records (~20% missing) with ~20% corrupted values to simulate real-world sync issues
4. MCP tools analyze data inconsistencies between production and staging
5. Ollama LLM receives user query and selects appropriate tools to execute
6. MCP server executes tools and returns structured results
7. AI generates human-readable explanations
8. Streamlit dashboard visualizes results interactively

---

## 💬 Example Queries

When running the CLI agent or using the dashboard:
- "What is the data quality score?"
- "Show missing records in staging"
- "Why is staging different from production?"
- "Generate a full comparison report"
- "How many records match between databases?"

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

- MCP-based tool architecture
- LLM tool-calling systems (agentic AI)
- Data quality engineering concepts
- Multi-interface AI system (CLI + MCP + Web UI)
- Production-grade database migration with safety features (backups, rollback, dry-run)
- End-to-end system design thinking

---

## 📊 Sample Results
Data Quality Score: 83%
Missing Records: 9%
Mismatched Records: 8%
System Status: ⚠️ Needs Attention

---
## 📦 Migration Tool

The application includes a powerful **Data Migration Tool** accessible through the Streamlit dashboard with the following features:

**Key Features:**
- 📋 **Dry Run Preview** - Preview all changes before executing migration
- 🛡️ **Automatic Backups** - Creates automatic backup snapshots before any migration
- ⏮️ **Rollback Capability** - Rollback to previous backups if migration fails
- 🔄 **Bidirectional** - Migrate from Production → Staging or Staging → Production
- 📊 **Flexible Scope** - Migrate missing rows, mismatched rows, or both

**Migration Workflow:**
1. **Step 1:** Choose migration direction (Prod→Staging or Staging→Prod)
2. **Step 2:** Select migration scope (missing rows, mismatched rows, or both)
3. **Step 3:** Preview migration details and row samples
4. **Step 4:** Automatic backup is created
5. **Step 5:** Execute migration
6. **Step 6:** Rollback available if needed

**Accessing Migration Tool:**
The migration tool is available in the Streamlit dashboard under the "Data Migration" page. Access via:
```bash
python run_app.py
# Then navigate to "🔄 Data Migration Tool" in the sidebar
```

---
## � Documentation

For detailed component documentation, see [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

## 🔮 Future Improvements
- Alembic-based database migration system
- Cloud deployment (AWS/Azure)
- Advanced data quality metrics
- ML-based anomaly detection
- Real-time sync monitoring
Real-time data pipelines
Multi-user authentication system
Advanced anomaly detection
Scheduled monitoring jobs

---

## 👤 Author
Built by Arpit Ghai
