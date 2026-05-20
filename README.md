# MCP Data Quality Assistant 🤖📊

An AI-powered data quality and consistency monitoring system built using **MCP (Model Context Protocol)** and **Ollama (local LLMs)**.

It simulates production and staging database environments, detects inconsistencies (missing rows, mismatches, schema differences), and enables natural language analysis through an AI agent with tool-calling capabilities.

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

### 1. Install dependencies

pip install -r requirements.txt

### 2. Initialize databases
python db_setup/init_db.py

### 3. Run AI agent (Ollama must be running)
python src/agent.py

### 4. Run MCP server
python src/mcp_server.py

### 5. Launch dashboard
streamlit run src/dashboard.py

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

## 🔮 Future Improvements
Cloud deployment (AWS/Azure)
Advanced data quality metrics
ML-based anomaly detection
Real-time data pipelines
Multi-user authentication system
Advanced anomaly detection
Scheduled monitoring jobs

---

## 👤 Author
Built by Arpit Ghai
