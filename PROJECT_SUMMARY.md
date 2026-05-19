# MCP Data Quality Assistant - Complete Project Summary

**Date:** May 18, 2026  
**Project Type:** AI-powered Data Quality Monitoring System  
**Architecture:** MCP (Model Context Protocol) + Ollama LLM + SQLite

---

## 📋 Project Overview

This is an **AI-powered data quality and consistency monitoring system** that detects data inconsistencies between production and staging database environments. The system leverages:
- **MCP (Model Context Protocol)** for tool exposure to external AI clients
- **Ollama** for running local LLMs (LLaMA3/Gemma)
- **Tool-based AI reasoning** where the LLM selects and calls appropriate tools
- **Multiple interfaces**: CLI agent, MCP server, and Streamlit dashboard

### Key Capabilities
- Synthetic Production & Staging databases (SQLite)
- Data quality analysis (missing rows, mismatches, quality scoring)
- AI-powered natural language analysis through an intelligent agent
- Automated report generation and JSON export
- Interactive web dashboard with real-time visualizations

---

## 🏗️ Architecture Overview

```
User Query 
  ↓
Ollama LLM (Local) 
  ↓
Tool Selection & Execution
  ↓
SQLite Databases (Production & Staging)
  ↓
Data Analysis & Comparison
  ↓
AI-Generated Explanation & Results
```

---

## 🗂️ Project Structure

```
mcp_project/
├── README.md                      # Project documentation
├── PROJECT_SUMMARY.md            # This file
├── src/
│   ├── agent.py                  # Ollama-based reasoning agent with tool-calling
│   ├── tools.py                  # Core data quality analysis tools
│   ├── mcp_server.py             # MCP server exposing tools to external clients
│   ├── compare.py                # CLI utility for database comparison
│   ├── dashboard.py              # Streamlit web UI for analysis
│   ├── test_mcp_ollama.py        # Testing utilities
│   └── requirements.txt           # Python dependencies
├── db_setup/
│   └── create_db.py              # Database initialization and synthetic data generation
├── data/
│   ├── prod.db                   # Production database (SQLite)
│   └── staging.db                # Staging database (SQLite)
└── images/
    └── [Project visualizations]
```

---

## 🔧 Core Components

### 1. **tools.py** - Analysis Engine

**Purpose:** Provides core data quality analysis functions that act as callable "tools" for the AI system.

**Available Tools:**

#### `get_missing_rows()`
- Returns all rows that exist in Production but are missing in Staging
- Output includes:
  - `count`: Number of missing rows
  - `percentage`: Percentage of data loss
  - `total_prod_records`: Total production records
  - `rows`: List of missing row details (order_id, customer_name, amount, country, created_at)

#### `get_mismatched_rows()`
- Identifies rows with data differences between databases
- Compares all fields for matching order IDs
- Output includes:
  - `count`: Number of mismatched rows
  - `percentage`: Percentage of mismatched records
  - `rows`: List with detailed before/after comparisons for each field

#### `get_quality_score()`
- Calculates overall data quality metrics
- Compares Production vs Staging databases
- Returns:
  - `quality_score`: Percentage of records that match perfectly
  - `prod_total`: Total production records
  - `staging_total`: Total staging records
  - `missing_count`: Number of missing records
  - `mismatched_count`: Number of mismatched records
  - `health_status`: System status indicator

#### `run_full_comparison()`
- Combines all analysis into a comprehensive report
- Provides holistic view of data consistency
- Returns combined results from all analysis tools

#### `export_report(output_file=None)`
- Exports comprehensive analysis report to JSON
- Optional custom output file path
- Includes timestamps and all analysis metrics

**Database Operations:**
- Connects to SQLite databases (PROD_DB and STAGING_DB)
- Uses `_connect()` for database connections
- Uses `_get_all_orders()` helper to fetch and index all records by order_id
- Performs row-by-row comparisons

---

### 2. **agent.py** - AI Reasoning Agent

**Purpose:** Connects Ollama LLM to tools with an intelligent reasoning loop.

**Configuration:**
- **Ollama Base URL:** http://localhost:11434
- **Model:** llama3 (can be switched to gemma3)
- **System Prompt:** Instructs the agent on available tools and how to use them

**Available Tools (from tools.py):**
1. `get_missing_rows` - Get rows missing in staging
2. `get_mismatched_rows` - Get rows with data differences
3. `get_quality_score` - Get quality metrics
4. `run_full_comparison` - Run complete analysis
5. `export_report` - Export results to JSON

**Key Functions:**

#### `get_ollama_client()`
- Initializes and returns Ollama client connection

#### `call_tool(tool_name, **kwargs)`
- Executes a tool from tools.py
- Returns structured result with status, tool name, and result/error
- Handles exceptions gracefully

#### `parse_tool_calls(response_text)`
- Parses tool calls from LLM responses
- Recognizes patterns: `CALL_TOOL: tool_name()`, `TOOL: tool_name()`, `- tool_name()`
- Extracts tool name and arguments

**Workflow:**
1. Accept user query
2. Send to Ollama LLM with system prompt and available tools
3. Parse LLM's tool selection from response
4. Execute selected tools via `call_tool()`
5. Collect results and provide to user
6. Generate human-readable explanation

**Note:** This agent will be replaced by MCP server in future versions.

---

### 3. **mcp_server.py** - MCP Protocol Server

**Purpose:** Exposes database quality tools as an MCP server for compatibility with Claude Desktop and other MCP clients.

**Server Configuration:**
- **Server Name:** database-quality-server
- **Logging:** Debug level to stderr
- **Protocol:** MCP (Model Context Protocol)

**Exposed Tools:**

All 5 tools from tools.py are exposed as MCP-compliant tools with:
- Tool name and description
- Input schema definition (JSON schema)
- Proper error handling and JSON response formatting

**Tool Definitions:**

1. **get_missing_rows** - No input parameters required
2. **get_mismatched_rows** - No input parameters required
3. **get_quality_score** - No input parameters required
4. **run_full_comparison** - No input parameters required
5. **export_report** - Optional `output_file` (string) parameter

**Implementation:**
- Each tool has an async handler function
- `@server.list_tools()` - Advertises available tools to MCP clients
- Tool handlers convert Python results to JSON strings
- Error handling returns JSON error messages
- `@server.call_tool()` - Route handler for tool invocations (pattern shown but full implementation continues)

**Usage:**
- Start MCP server as a subprocess
- Connect from MCP-compatible client (Claude Desktop)
- Send tool calls via MCP protocol
- Receive structured JSON responses

---

### 4. **create_db.py** - Database Setup

**Purpose:** Creates synthetic production and staging databases with intentional inconsistencies to demonstrate data quality issues.

**Database Schema:**

```sql
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_name TEXT,
    amount REAL,
    country TEXT,
    created_at TEXT
)
```

**Data Generation Process:**

#### `create_tables(conn)`
- Creates the `orders` table if it doesn't exist
- Same schema for both production and staging

#### `insert_data(conn, num_rows=100, missing_ratio=0.1, modify_ratio=0.1)`
- Generates synthetic data using Faker library
- Creates 100 records by default with:
  - `order_id`: Sequential integer (1-100)
  - `customer_name`: Generated with Faker
  - `amount`: Random float between 20-500
  - `country`: Generated with Faker
  - `created_at`: Random date

#### `insert_staging_data(prod_conn, staging_conn)`
- Copies data from production to staging with intentional issues:
  - **Missing Data Simulation:** 10% chance to skip a row (data loss)
  - **Data Modification:** 10% chance to modify amount by ±20% (data corruption)
  - Simulates real-world sync issues

**Execution:**
```bash
python db_setup/create_db.py
```

**Output:**
- `data/prod.db` - Production database with 100 records
- `data/staging.db` - Staging database with ~90 records and ~10% modified values
- "Databases created successfully!" confirmation message

---

### 5. **compare.py** - CLI Comparison Utility

**Purpose:** Provides command-line interface for database comparison and report generation.

**Key Functions:**

#### `connect(db_path)`
- Establishes SQLite connection

#### `get_all_orders(conn)`
- Fetches all orders as dictionary with order_id as key
- Enables O(1) lookup for comparisons

#### `compare_databases()`
- Compares production and staging databases
- Returns:
  - `prod_total`: Total production records
  - `staging_total`: Total staging records
  - `missing_rows`: Rows in production but not in staging
  - `modified_rows`: Rows with data differences (includes before/after data)

#### `generate_report()`
- Creates formatted console report showing:
  - Summary statistics (record counts, data loss %, modifications %)
  - Missing rows table (Order ID, Customer, Amount, Country, Date)
  - Modified rows details with side-by-side comparison
- Uses tabulate library for formatted output

**Report Sections:**
1. **Summary Statistics** - High-level metrics
2. **Missing Rows** - Grid table of missing records
3. **Modified Rows** - Detailed comparison of changed data

**Execution:**
```bash
python src/compare.py
```

---

### 6. **dashboard.py** - Streamlit Web Dashboard

**Purpose:** Interactive web UI for data quality analysis with visualizations and AI integration.

**Features:**

#### Dashboard Components:
- **Metric Cards** - KPI display with color-coded status
- **Gauge Chart** - Quality score visualization (0-100)
- **Status Badges** - Visual indicators (✅ GOOD, ⚠️ WARNING, 🔴 CRITICAL)

#### Data Cache:
- `get_all_data()` - Cached data retrieval from analysis tools
- Prevents redundant database queries

#### Status Determination:
- **Score ≥ 90%:** ✅ GOOD (green)
- **Score 80-89%:** ⚠️ WARNING (yellow)
- **Score < 80%:** 🔴 CRITICAL (red)

#### Visualizations:
- Gauge chart for quality score with delta reference (90%)
- Custom color-coded ranges:
  - 0-70: Red (#ffcccc)
  - 70-90: Yellow
  - 90-100: Green

#### Ollama Integration:
- Connection URL: http://localhost:11434
- Model: llama3
- AI assistant available for natural language queries

**Configuration:**
- **Page Title:** Database Quality Dashboard
- **Icon:** 📊
- **Layout:** Wide (expanded sidebar)
- **Custom CSS:** Metric cards, color-coded status classes

**Execution:**
```bash
streamlit run src/dashboard.py
```

---

## 📦 Dependencies (requirements.txt)

```
streamlit          # Web UI framework
pandas             # Data manipulation
plotly             # Interactive visualizations
faker              # Synthetic data generation
```

**Additional System Requirements:**
- Python 3.11+
- Ollama (installed and running locally)
- SQLite3 (included with Python)
- MCP protocol support (for MCP server)

---

## 🚀 How to Run

### 1. **Setup Environment**
```bash
cd mcp_project
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. **Install Dependencies**
```bash
pip install -r src/requirements.txt
```

### 3. **Create Databases**
```bash
python db_setup/create_db.py
```

### 4. **Start Ollama** (separate terminal)
```bash
ollama serve
```

### 5. **Run Desired Interface**

**Option A: CLI Agent with Ollama**
```bash
python src/agent.py
```
Enter queries like:
- "What is the data quality score?"
- "Show missing records in staging"
- "Why is staging different from production?"

**Option B: MCP Server**
```bash
python src/mcp_server.py
```
Connect from Claude Desktop or other MCP client

**Option C: CLI Comparison Report**
```bash
python src/compare.py
```

**Option D: Web Dashboard**
```bash
streamlit run src/dashboard.py
```
Access at http://localhost:8501

---

## 📊 Data Model

### Database: Orders
- **Table:** orders
- **Columns:**
  - `order_id` (INTEGER PRIMARY KEY) - Unique identifier
  - `customer_name` (TEXT) - Customer name (Faker-generated)
  - `amount` (REAL) - Order amount ($20-500)
  - `country` (TEXT) - Country (Faker-generated)
  - `created_at` (TEXT) - Creation date

### Synthetic Inconsistencies:
- **Production:** 100 complete records
- **Staging:** ~90 records (~10% missing)
  - ~10% of amounts modified by ±20%

---

## 🎯 Example Workflows

### Workflow 1: Detect Quality Issues
1. Run `create_db.py` to generate databases
2. Run `compare.py` to see missing and modified records
3. Review report to identify data loss and corruption

### Workflow 2: AI Analysis
1. Start Ollama service
2. Run `agent.py`
3. Query: "What's our data quality score?"
4. Agent calls `get_quality_score()` and explains results
5. Query: "Show me what's different?"
6. Agent calls `get_mismatched_rows()` and analyzes differences

### Workflow 3: Export Reports
1. Run dashboard or agent
2. Call `export_report("path/to/report.json")`
3. Share JSON report with stakeholders

### Workflow 4: MCP Integration
1. Start `mcp_server.py`
2. Connect Claude Desktop to MCP server
3. Ask Claude to analyze data quality
4. Claude uses MCP tools to fetch data and explain

---

## 🔮 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Local LLM | Ollama + LLaMA3/Gemma | AI reasoning and tool selection |
| Protocol | MCP (Model Context Protocol) | Tool exposure to AI clients |
| Database | SQLite | Production & staging data storage |
| CLI | Python + Tabulate | Command-line reporting |
| Web UI | Streamlit | Interactive dashboard |
| Visualization | Plotly | Charts and gauges |
| Data Gen | Faker | Synthetic test data |
| Data Processing | Pandas | Data manipulation |

---

## 🧠 Key Concepts Demonstrated

1. **Tool-Calling AI Systems** - LLM selects and calls appropriate tools
2. **MCP Protocol** - Standard interface for AI to access external tools
3. **Data Quality Engineering** - Detecting and analyzing data inconsistencies
4. **Local LLM Integration** - Using Ollama for privacy and control
5. **Multi-Interface Systems** - Same backend with CLI, web, and API access
6. **Synthetic Data Generation** - Creating realistic test scenarios
7. **Agentic AI** - Autonomous reasoning and decision-making

---

## 📝 Notes

- The `agent.py` will be replaced by the MCP server in future versions
- All database paths are relative to the `data/` directory
- Ollama must be running locally for agent and dashboard AI features
- MCP server communicates via stdio (suitable for subprocess spawning)
- Quality score threshold: 90% for "GOOD", 80% for "WARNING"

---

**Last Updated:** May 18, 2026  
**Status:** Production-ready with demonstration databases
