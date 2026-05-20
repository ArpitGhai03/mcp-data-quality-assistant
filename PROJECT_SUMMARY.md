# MCP Data Quality Assistant - Complete Project Summary

**Date:** May 20, 2026  
**Project Type:** AI-powered Data Quality Monitoring System  
**Architecture:** MCP (Model Context Protocol) + Ollama LLM + PostgreSQL  
**Status:** Production-ready with PostgreSQL backend and integrated CLI launcher

---

## 📋 Project Overview

This is an **AI-powered data quality and consistency monitoring system** that detects data inconsistencies between production and staging database environments. The system leverages:
- **MCP (Model Context Protocol)** for tool exposure to external AI clients
- **Ollama** for running local LLMs (LLaMA3/Gemma)
- **Tool-based AI reasoning** where the LLM selects and calls appropriate tools
- **PostgreSQL** for robust production and staging databases
- **Multiple interfaces**: CLI agent, MCP server, and Streamlit dashboard

### Key Capabilities
- PostgreSQL Production & Staging databases with environment-based configuration
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
├── run_app.py                    # Master CLI launcher (Ollama + Dashboard + Agent)
├── .env                          # PostgreSQL connection credentials (environment config)
├── src/
│   ├── agent.py                  # Ollama-based reasoning agent with tool-calling
│   ├── tools.py                  # Core data quality analysis tools
│   ├── mcp_server.py             # MCP server exposing tools to external clients
│   ├── compare.py                # CLI utility for database comparison
│   ├── dashboard.py              # Streamlit web UI for analysis
│   ├── db_config.py              # PostgreSQL connection configuration
│   ├── test_mcp_ollama.py        # Testing utilities
│   └── requirements.txt           # Python dependencies
├── db_setup/
│   └── init_db.py                # Database initialization (creates tables and seed data)
├── data/
│   ├── comparison_report.json    # Latest comparison report
│   └── [export files]
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

### 4. **init_db.py** - Database Initialization

**Purpose:** Initializes PostgreSQL production and staging databases with table schema and seed data. Demonstrates data quality issues by simulating inconsistencies between environments.

**Database Configuration:**
- Reads PostgreSQL connection settings from `.env` file
- Uses `db_config.py` module to load production and staging credentials
- Environment variables: `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PROD_DB_NAME`, `STAGING_DB_NAME`

**Database Schema (PostgreSQL):**

```sql
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    amount NUMERIC(10, 2),
    country VARCHAR(100),
    created_at DATE
)
```

**Initialization Process:**

#### `connect(config)`
- Establishes PostgreSQL connection using psycopg2
- Uses configuration from `db_config.py`

#### `create_tables(conn)`
- Creates `orders` table in both production and staging databases
- Uses `CREATE TABLE IF NOT EXISTS` to handle idempotency

#### `insert_data(conn, num_rows=500, missing_ratio=0.1, modify_ratio=0.1)`
- Generates 500 synthetic records using Faker library
- Checks for existing data to prevent duplication
- Creates records with:
  - `order_id`: Auto-generated SERIAL PRIMARY KEY
  - `customer_name`: Faker-generated names
  - `amount`: Random numeric values (100-5000)
  - `country`: Faker-generated countries
  - `created_at`: Faker-generated dates

#### `insert_staging_data(prod_conn, staging_conn)`
- Copies production data to staging with intentional quality issues:
  - **Data Loss Simulation:** 20% chance to skip a row (simulates sync failures)
  - **Data Corruption:** 20% chance to modify amount by ±30% (simulates ETL errors)
  - Creates realistic data mismatch scenarios for quality testing

**Execution:**
```bash
python db_setup/init_db.py
```

**Options:**
```bash
python db_setup/init_db.py --reset    # Drop and recreate all tables
```

**Output:**
- PostgreSQL production database with 500 seeded records
- PostgreSQL staging database with ~400 records and ~20% corrupted values
- Confirmation message indicating databases are ready

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
psycopg2-binary    # PostgreSQL adapter for Python
python-dotenv      # Environment variable management
ollama             # Ollama client library
```

**Additional System Requirements:**
- Python 3.11+
- PostgreSQL 12+ (local or remote)
- Ollama (installed and running locally)
- MCP protocol support (for MCP server)

---

## 🚀 How to Run

### Prerequisites
1. **PostgreSQL Setup**
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

2. **Python Environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   
   pip install -r src/requirements.txt
   ```

### Quick Start (Master CLI - Recommended)
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
- Optionally starts the AI agent with `--agent` flag

**Additional Options:**
```bash
python run_app.py --agent           # Include AI agent
python run_app.py --no-browser      # Don't auto-open browser
python run_app.py --agent --no-browser
```

### Individual Services

**Option A: Reset & Reinitialize Databases**
```bash
python db_setup/init_db.py --reset  # Drops tables and recreates them
```

**Option B: CLI Agent with Ollama**
```bash
python src/agent.py
```
Enter queries like:
- "What is the data quality score?"
- "Show missing records in staging"
- "Why is staging different from production?"

**Option C: MCP Server**
```bash
python src/mcp_server.py
```
Connect from Claude Desktop or other MCP client

**Option D: CLI Comparison Report**
```bash
python src/compare.py
```

**Option E: Web Dashboard (standalone)**
```bash
streamlit run src/dashboard.py
```
Access at http://localhost:8501

---

## 📊 Data Model

### Database: PostgreSQL Orders Table
- **Table:** orders
- **Columns:**
  - `order_id` (SERIAL PRIMARY KEY) - Auto-incrementing unique identifier
  - `customer_name` (VARCHAR(255)) - Customer name (Faker-generated)
  - `amount` (NUMERIC(10,2)) - Order amount (100-5000)
  - `country` (VARCHAR(100)) - Country (Faker-generated)
  - `created_at` (DATE) - Creation date (Faker-generated)

### Databases:
- **Production (`prod`):** 500 complete records representing authoritative source
- **Staging (`staging`):** ~400 records (~20% missing)
  - ~20% of amounts modified by ±30%
  - Simulates real-world ETL and sync issues

### Configuration:
- Environment-based PostgreSQL connection settings (`.env` file)
- Supports both local and remote PostgreSQL instances
- Configurable database names, host, port, and credentials

---

## 🎯 Example Workflows

### Workflow 1: Detect Quality Issues
1. Run `init_db.py` to initialize PostgreSQL databases and seed data
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
| Database | PostgreSQL 12+ | Production & staging data storage |
| ORM/Driver | psycopg2 | PostgreSQL connection and queries |
| CLI | Python + Tabulate | Command-line reporting |
| Web UI | Streamlit | Interactive dashboard |
| Visualization | Plotly | Charts and gauges |
| Data Gen | Faker | Synthetic test data |
| Data Processing | Pandas | Data manipulation |
| Config | python-dotenv | Environment variable management |

1. **Tool-Calling AI Systems** - LLM selects and calls appropriate tools
2. **MCP Protocol** - Standard interface for AI to access external tools
3. **Data Quality Engineering** - Detecting and analyzing data inconsistencies
4. **Local LLM Integration** - Using Ollama for privacy and control
5. **Multi-Interface Systems** - Same backend with CLI, web, and API access
6. **Synthetic Data Generation** - Creating realistic test scenarios
7. **Agentic AI** - Autonomous reasoning and decision-making

---

## 📝 Notes

- PostgreSQL must be running before initializing databases with `init_db.py`
- Create PostgreSQL databases (`prod` and `staging`) before running initialization
- Database credentials are managed via `.env` file (not committed to version control)
- The `agent.py` will be replaced by the MCP server in future versions
- Ollama must be running locally for agent and dashboard AI features
- MCP server communicates via stdio (suitable for subprocess spawning)
- Quality score threshold: 90% for "GOOD", 80% for "WARNING"
- Use `init_db.py --reset` to drop and recreate tables if needed

---

---

## ✨ Recent Updates (May 20, 2026)

- **PostgreSQL Migration**: Upgraded from SQLite to PostgreSQL for production-grade database management
- **Database Initialization**: Renamed `create_db.py` to `init_db.py` for clearer intent
- **Environment Configuration**: Added `.env` file support for flexible database credentials
- **Master CLI Launcher** (`run_app.py`): Orchestrates all services (Ollama, Streamlit, Agent)
- **Automated Service Detection**: Checks Ollama status and auto-starts if needed
- **Browser Auto-Launch**: Dashboard automatically opens in default browser
- **Flexible Startup Options**: Run with or without agent, disable browser opening
- **Improved Documentation**: Updated with PostgreSQL setup and configuration guidance

---

**Last Updated:** May 20, 2026  
**Status:** Production-ready with integrated service orchestration
