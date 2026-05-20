"""
Streamlit Dashboard for Database Quality Analysis
Integrates tools.py, Ollama, and MCP for a complete analysis platform
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from decimal import Decimal
import plotly.graph_objects as go
from tools import (
    get_missing_rows,
    get_mismatched_rows,
    get_quality_score,
    run_full_comparison,
    export_report,
    preview_migration,
    create_backup_snapshot,
    migrate_missing_rows,
    migrate_mismatched_rows,
    rollback_to_backup
)
from ollama import Client

# Page configuration
st.set_page_config(
    page_title="Database Quality Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL = "llama3"

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .status-good { color: #28a745; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    .status-critical { color: #dc3545; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def get_all_data():
    """Fetch all analysis data."""
    return {
        'quality_score': get_quality_score(),
        'missing_rows': get_missing_rows(),
        'mismatched_rows': get_mismatched_rows(),
        'full_comparison': run_full_comparison()
    }


def get_status_badge(score):
    """Determine status based on quality score."""
    if score >= 90:
        return "✅ GOOD", "status-good"
    elif score >= 80:
        return "⚠️ WARNING", "status-warning"
    else:
        return "🔴 CRITICAL", "status-critical"


def create_gauge_chart(score):
    """Create a gauge chart for quality score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={'text': "Quality Score"},
        delta={'reference': 90},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 70], 'color': "#ffcccc"},
                {'range': [70, 85], 'color': "#ffffcc"},
                {'range': [85, 100], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=300)
    return fig


def create_status_chart(data):
    """Create a pie chart showing data status."""
    quality = data['quality_score']
    
    fig = go.Figure(data=[go.Pie(
        labels=['Healthy', 'Missing', 'Mismatched'],
        values=[
            quality['healthy_count'],
            quality['missing_count'],
            quality['mismatched_count']
        ],
        marker=dict(colors=['#28a745', '#ffc107', '#dc3545']),
        textposition='inside',
        textinfo='label+percent'
    )])
    fig.update_layout(height=300)
    return fig


def page_overview():
    """Page 1: Data Quality Overview"""
    st.title("📊 Data Quality Dashboard")
    
    # Get data
    data = get_all_data()
    quality = data['quality_score']
    
    # Status and score section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = quality['quality_score']
        status_text, status_class = get_status_badge(score)
        st.metric(
            label="Quality Score",
            value=f"{score}%",
            delta=f"{score-70}% vs baseline"
        )
        st.markdown(f"<p class='{status_class}'>{status_text}</p>", unsafe_allow_html=True)
    
    with col2:
        st.metric(
            label="Missing Records",
            value=quality['missing_count'],
            delta=f"{quality['missing_percentage']}%"
        )
    
    with col3:
        st.metric(
            label="Mismatched Records",
            value=quality['mismatched_count'],
            delta=f"{quality['mismatched_percentage']}%"
        )
    
    st.divider()
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quality Score Gauge")
        fig_gauge = create_gauge_chart(quality['quality_score'])
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col2:
        st.subheader("Data Status Distribution")
        fig_pie = create_status_chart(data)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # Database summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info(f"**Production DB**\n{quality['prod_total']} records")
    
    with col2:
        st.info(f"**Staging DB**\n{quality['staging_total']} records")
    
    with col3:
        st.success(f"**Healthy Records**\n{quality['healthy_count']} ({quality['healthy_percentage']}%)")
    
    with col4:
        st.warning(f"**Data Loss**\n{quality['missing_count']} records")
    
    st.divider()
    
    # Recommendations
    recommendation = data['full_comparison']['summary']['recommendation']
    status = data['full_comparison']['summary']['status']
    
    if status == "GOOD":
        st.success(f"✅ {recommendation}")
    elif status == "WARNING":
        st.warning(f"⚠️ {recommendation}")
    else:
        st.error(f"🔴 {recommendation}")


def page_detailed_comparison():
    """Page 2: Detailed Comparison View"""
    st.title("📋 Detailed Comparison")
    
    data = get_all_data()
    
    # Missing rows section
    st.subheader("❌ Missing Rows")
    st.text(f"Found {data['missing_rows']['count']} records in Production but missing in Staging ({data['missing_rows']['percentage']}%)")
    
    if data['missing_rows']['rows']:
        missing_df = pd.DataFrame(data['missing_rows']['rows'])
        st.dataframe(missing_df, use_container_width=True, hide_index=True)
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Missing Count", data['missing_rows']['count'])
        with col2:
            total_amount = missing_df['amount'].sum()
            st.metric("Total Amount at Risk", f"${total_amount:.2f}")
        with col3:
            st.metric("Percentage", f"{data['missing_rows']['percentage']}%")
    else:
        st.success("✅ No missing rows!")
    
    st.divider()
    
    # Mismatched rows section
    st.subheader("⚠️ Mismatched Rows")
    st.text(f"Found {data['mismatched_rows']['count']} records with data differences ({data['mismatched_rows']['percentage']}%)")
    
    if data['mismatched_rows']['rows']:
        # Create comparison table
        comparison_data = []
        for row in data['mismatched_rows']['rows']:
            for field, values in row['changes'].items():
                comparison_data.append({
                    'Order ID': row['order_id'],
                    'Field': field,
                    'Production': values['prod'],
                    'Staging': values['staging'],
                    'Difference': abs(values['prod'] - values['staging']) if isinstance(values['prod'], (int, float)) else 'N/A'
                })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Summary statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Mismatched Count", data['mismatched_rows']['count'])
        with col2:
            st.metric("Percentage", f"{data['mismatched_rows']['percentage']}%")
    else:
        st.success("✅ No mismatched rows!")
    
    st.divider()
    
    # Detailed production vs staging comparison
    st.subheader("🔄 Full Records Comparison")
    
    # Show mismatched rows side by side
    if data['mismatched_rows']['rows']:
        for row in data['mismatched_rows']['rows'][:5]:  # Show first 5
            with st.expander(f"Order {row['order_id']} - Detailed Comparison"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Production DB:**")
                    prod_data = row['production']
                    for key, value in prod_data.items():
                        st.write(f"- {key}: {value}")
                
                with col2:
                    st.write("**Staging DB:**")
                    staging_data = row['staging']
                    for key, value in staging_data.items():
                        st.write(f"- {key}: {value}")
                
                st.write("**Changes:**")
                for field, values in row['changes'].items():
                    st.write(f"- {field}: {values['prod']} → {values['staging']}")


# Define available tools with descriptions
AVAILABLE_TOOLS_INFO = {
    "get_missing_rows": {
        "description": "Get all rows that exist in Production DB but are missing in Staging DB",
        "function": get_missing_rows,
        "params": []
    },
    "get_mismatched_rows": {
        "description": "Get all rows with data differences between Production and Staging databases",
        "function": get_mismatched_rows,
        "params": []
    },
    "get_quality_score": {
        "description": "Get overall data quality score and metrics comparing the databases",
        "function": get_quality_score,
        "params": []
    },
    "run_full_comparison": {
        "description": "Run a full comparison between Production and Staging databases",
        "function": run_full_comparison,
        "params": []
    },
    "export_report": {
        "description": "Export the comparison report to a JSON file",
        "function": export_report,
        "params": ["output_file"]
    }
}


def parse_tool_call(response_text: str):
    """Parse tool calls from LLM response."""
    tool_name = None
    explanation = ""
    
    for line in response_text.split('\n'):
        line = line.strip()
        
        # Check for tool call patterns
        if "TOOL:" in line:
            try:
                tool_name = line.split("TOOL:")[1].strip().split()[0].lower()
            except:
                pass
        
        if "EXPLANATION:" in line:
            try:
                explanation = line.split("EXPLANATION:")[1].strip()
            except:
                pass
    
    return tool_name, explanation


def get_tools_description():
    """Generate formatted tool descriptions for the system prompt."""
    description = "Available Tools:\n"
    for name, info in AVAILABLE_TOOLS_INFO.items():
        description += f"- {name}: {info['description']}\n"
    return description


def page_ai_assistant():
    """Page 3: AI Assistant Panel"""
    st.title("🤖 AI Assistant Analysis")
    
    st.markdown("""
    Ask natural language questions about your database quality. The AI will:
    1. Understand your question
    2. Select the appropriate analysis tool
    3. Execute the tool
    4. Provide insights and explanations
    """)
    
    # Display available tools
    with st.expander("📋 Available Tools", expanded=False):
        for tool_name, info in AVAILABLE_TOOLS_INFO.items():
            st.write(f"**{tool_name}**: {info['description']}")
    
    st.divider()
    
    # Input section
    st.subheader("📝 Ask a Question")
    
    # Quick templates
    col1, col2, col3, col4 = st.columns(4)
    
    quick_queries = [
        "What is the data quality score?",
        "Show me missing rows",
        "What data is different?",
        "What tools are available?"
    ]
    
    with col1:
        if st.button("🎯 Quality Score"):
            st.session_state.user_query = quick_queries[0]
            st.rerun()
    
    with col2:
        if st.button("📍 Missing Rows"):
            st.session_state.user_query = quick_queries[1]
            st.rerun()
    
    with col3:
        if st.button("🔄 Differences"):
            st.session_state.user_query = quick_queries[2]
            st.rerun()
    
    with col4:
        if st.button("🛠️ Tools"):
            st.session_state.user_query = quick_queries[3]
            st.rerun()
    
    st.write("**OR**")
    
    # Initialize session state for query
    if 'user_query' not in st.session_state:
        st.session_state.user_query = ""
    
    # Use form for Enter key support
    with st.form("query_form"):
        user_query = st.text_area(
            "Enter your question:",
            value=st.session_state.user_query,
            placeholder="e.g., What's our data quality? Show missing records? What tools do you have?",
            height=80,
            key="query_input"
        )
        
        analyze_button = st.form_submit_button("🔍 Analyze", use_container_width=True)
    
    # Update session state when form is submitted
    if analyze_button:
        st.session_state.user_query = user_query
    
    if analyze_button and user_query:
        st.divider()
        
        # Check if user is asking about available tools
        if "tools" in user_query.lower() or "what can" in user_query.lower():
            st.subheader("🛠️ Available Tools")
            
            tool_list = pd.DataFrame([
                {"Tool Name": name, "Description": info["description"]}
                for name, info in AVAILABLE_TOOLS_INFO.items()
            ])
            st.dataframe(tool_list, use_container_width=True, hide_index=True)
            
            st.divider()
            
            st.success("""
            ✅ **Available Tools:**
            1. **get_quality_score** - Get overall data quality metrics and statistics
            2. **get_missing_rows** - Find rows missing in staging database
            3. **get_mismatched_rows** - Find rows with data differences
            4. **run_full_comparison** - Run complete database comparison
            5. **export_report** - Export results to JSON file
            
            Try asking about any of these!
            """)
            
            return
        
        with st.spinner("🤖 Ollama is analyzing..."):
            try:
                client = Client(host=OLLAMA_BASE_URL)
                
                # Enhanced system prompt with clear tool definitions
                tools_description = get_tools_description()
                system_prompt = f"""You are a database quality analysis expert with access to specific tools.

{tools_description}

When the user asks a question, determine which tool would best answer it.
Respond EXACTLY in this format:
TOOL: <tool_name>
EXPLANATION: <brief explanation of why this tool answers the question>

Choose the most appropriate tool. If unsure, use 'run_full_comparison'."""
                
                # Get Ollama recommendation
                response = client.generate(
                    model=MODEL,
                    prompt=user_query,
                    system=system_prompt,
                    stream=False
                )
                
                response_text = response['response']
                tool_name, explanation = parse_tool_call(response_text)
                
                # Display Ollama's recommendation
                st.subheader("🔍 Analysis Plan")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"**Tool Selected:** {tool_name or 'get_quality_score'}")
                
                with col2:
                    st.info(f"**Approach:** {explanation or 'Analyzing database quality'}")
                
                st.divider()
                
                # Use recommended tool or fallback
                tool_name = tool_name or 'get_quality_score'
                
                # Execute tool if valid
                if tool_name in AVAILABLE_TOOLS_INFO:
                    st.subheader("⚙️ Executing Tool...")
                    
                    with st.spinner(f"Executing {tool_name}..."):
                        try:
                            tool_func = AVAILABLE_TOOLS_INFO[tool_name]['function']
                            result = tool_func()
                            
                            st.success("✅ Tool executed successfully!")
                            
                            st.subheader("📊 Results")
                            
                            # Display results nicely
                            if isinstance(result, dict):
                                # Show key metrics
                                metrics_cols = st.columns(4)
                                metric_count = 0
                                
                                if 'quality_score' in result:
                                    with metrics_cols[metric_count % 4]:
                                        st.metric("Quality Score", f"{result['quality_score']}%")
                                    metric_count += 1
                                
                                if 'count' in result:
                                    with metrics_cols[metric_count % 4]:
                                        st.metric("Count", result['count'])
                                    metric_count += 1
                                
                                if 'percentage' in result:
                                    with metrics_cols[metric_count % 4]:
                                        st.metric("Percentage", f"{result['percentage']}%")
                                    metric_count += 1
                                
                                if 'missing_count' in result:
                                    with metrics_cols[metric_count % 4]:
                                        st.metric("Missing", result['missing_count'])
                                
                                # Show detailed data
                                st.subheader("📋 Detailed Data")
                                
                                if 'rows' in result and result['rows'] and len(result['rows']) > 0:
                                    df = pd.DataFrame(result['rows'])
                                    st.dataframe(df, use_container_width=True, hide_index=True)
                                else:
                                    # Show as JSON for complex results
                                    st.json(result)
                            
                            st.divider()
                            
                            # Get Ollama's explanation
                            st.subheader("💡 AI Explanation")
                            
                            with st.spinner("Ollama is generating explanation..."):
                                explanation_prompt = f"""Based on this database analysis result, provide a brief, 
                                non-technical explanation of what it means and what actions might be needed.
                                
Result Summary:
{json.dumps(result, indent=2)[:800]}

Keep it to 2-3 sentences maximum. Focus on actionable insights."""
                                
                                explanation_response = client.generate(
                                    model=MODEL,
                                    prompt=explanation_prompt,
                                    stream=False
                                )
                                
                                explanation_text = explanation_response['response']
                                st.write(explanation_text)
                            
                        except Exception as e:
                            st.error(f"❌ Error executing tool: {str(e)}")
                else:
                    st.warning(f"⚠️ Tool '{tool_name}' not found. Using full comparison.")
                    
                    # Fallback: show full comparison
                    data = get_all_data()
                    result = data['full_comparison']
                    st.json(result)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Make sure Ollama is running: `ollama serve`")
    
    elif analyze_button and not user_query:
        st.warning("⚠️ Please enter a question first!")


def page_migration():
    """Page 4: Data Migration Tool"""
    st.title("🔄 Data Migration Tool")
    
    st.markdown("""
    Safely migrate missing and mismatched rows between Production and Staging databases.
    - 📋 Preview migration before executing
    - 🛡️ Automatic backups before migration
    - ⏮️ Rollback capability if needed
    """)
    
    st.divider()
    
    # Initialize session state for migration
    if 'migration_backup_id' not in st.session_state:
        st.session_state.migration_backup_id = None
    
    # Step 1: Direction
    st.subheader("Step 1️⃣: Choose Migration Direction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Production → Staging", use_container_width=True, key="direction_prod_to_staging"):
            st.session_state.migration_direction = "prod_to_staging"
    
    with col2:
        if st.button("📥 Staging → Production", use_container_width=True, key="direction_staging_to_prod"):
            st.session_state.migration_direction = "staging_to_prod"
    
    if 'migration_direction' not in st.session_state:
        st.info("👈 Select a migration direction to continue")
        return
    
    # Display selected direction
    if st.session_state.migration_direction == "prod_to_staging":
        st.success("✅ Selected: Production → Staging")
        source_db = "prod"
        dest_db = "staging"
    else:
        st.success("✅ Selected: Staging → Production")
        source_db = "staging"
        dest_db = "prod"
    
    st.divider()
    
    # Step 2: Choose scope
    st.subheader("Step 2️⃣: Choose Migration Scope")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔴 Missing Rows Only", use_container_width=True, key="scope_missing"):
            st.session_state.migration_scope = "missing"
    
    with col2:
        if st.button("🟡 Mismatched Rows Only", use_container_width=True, key="scope_mismatched"):
            st.session_state.migration_scope = "mismatched"
    
    with col3:
        if st.button("🟢 Both", use_container_width=True, key="scope_both"):
            st.session_state.migration_scope = "both"
    
    if 'migration_scope' not in st.session_state:
        st.info("👈 Select what to migrate to continue")
        return
    
    scope_name = {
        "missing": "Missing Rows",
        "mismatched": "Mismatched Rows",
        "both": "Both Missing & Mismatched Rows"
    }
    
    st.success(f"✅ Selected: {scope_name[st.session_state.migration_scope]}")
    
    st.divider()
    
    # Step 3: Preview
    st.subheader("Step 3️⃣: Preview Migration")
    
    if st.button("👁️ Preview What Will Be Migrated", use_container_width=True, key="btn_preview"):
        with st.spinner("Generating preview..."):
            preview = preview_migration(source_db, dest_db, st.session_state.migration_scope)
            
            if preview['status'] == 'success':
                st.session_state.preview_data = preview
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Missing Rows", preview['missing_rows_count'])
                
                with col2:
                    st.metric("Mismatched Rows", preview['mismatched_rows_count'])
                
                with col3:
                    st.metric("Total to Migrate", preview['total_rows_to_migrate'])
                
                st.divider()
                
                # Show missing rows preview
                if preview['missing_rows_count'] > 0:
                    st.write("**Missing Rows (will be added):**")
                    missing_df = pd.DataFrame(preview['missing_rows_preview'])
                    st.dataframe(missing_df, use_container_width=True, hide_index=True)
                    
                    if preview['missing_rows_count'] > len(preview['missing_rows_preview']):
                        st.caption(f"... and {preview['missing_rows_count'] - len(preview['missing_rows_preview'])} more")
                
                # Show mismatched rows preview
                if preview['mismatched_rows_count'] > 0:
                    st.write("**Mismatched Rows (will be updated):**")
                    mismatched_df = pd.DataFrame(preview['mismatched_rows_preview'])
                    st.dataframe(mismatched_df, use_container_width=True, hide_index=True)
                    
                    if preview['mismatched_rows_count'] > len(preview['mismatched_rows_preview']):
                        st.caption(f"... and {preview['mismatched_rows_count'] - len(preview['mismatched_rows_preview'])} more")
            else:
                st.error(f"❌ Error generating preview: {preview.get('error', 'Unknown error')}")
    
    if 'preview_data' not in st.session_state:
        st.info("👈 Click 'Preview' to see what will be migrated")
        return
    
    st.divider()
    
    # Step 4: Confirm and Execute
    st.subheader("Step 4️⃣: Execute Migration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧪 Dry Run (Test Only)", use_container_width=True, key="btn_dryrun"):
            st.divider()
            st.subheader("🧪 Dry Run Preview - How Data Will Look After Migration")
            
            # Get current destination data
            if dest_db == "prod":
                from tools import _connect_prod
                dest_conn = _connect_prod()
            else:
                from tools import _connect_staging
                dest_conn = _connect_staging()
            
            from tools import _get_all_orders
            dest_orders = _get_all_orders(dest_conn)
            dest_conn.close()
            
            # Convert to DataFrame
            dest_list = []
            for order_id, row in dest_orders.items():
                dest_list.append({
                    'order_id': row[0],
                    'customer_name': row[1],
                    'amount': float(row[2]) if isinstance(row[2], Decimal) else row[2],
                    'country': row[3],
                    'created_at': str(row[4]) if row[4] else None
                })
            
            current_df = pd.DataFrame(dest_list)
            
            # Simulate the migration by combining with source data
            if source_db == 'prod':
                from tools import _connect_prod
                source_conn = _connect_prod()
            else:
                from tools import _connect_staging
                source_conn = _connect_staging()
            
            source_orders = _get_all_orders(source_conn)
            source_conn.close()
            
            # Create simulated state after migration
            simulated_list = list(dest_list)  # Start with current
            
            for order_id in source_orders:
                row = source_orders[order_id]
                new_row = {
                    'order_id': row[0],
                    'customer_name': row[1],
                    'amount': float(row[2]) if isinstance(row[2], Decimal) else row[2],
                    'country': row[3],
                    'created_at': str(row[4]) if row[4] else None
                }
                
                # Check if this is missing or mismatched
                existing = next((x for x in simulated_list if x['order_id'] == order_id), None)
                
                if st.session_state.migration_scope in ['missing', 'both']:
                    # Missing: only add if not exists
                    if not existing:
                        simulated_list.append(new_row)
                
                if st.session_state.migration_scope in ['mismatched', 'both']:
                    # Mismatched: update if exists and different
                    if existing and existing != new_row:
                        idx = simulated_list.index(existing)
                        simulated_list[idx] = new_row
            
            simulated_df = pd.DataFrame(simulated_list).sort_values('order_id').reset_index(drop=True)
            
            # Show comparison
            col_before, col_after = st.columns(2)
            
            with col_before:
                st.write("**📊 Current State:**")
                st.dataframe(current_df.sort_values('order_id').reset_index(drop=True), use_container_width=True, height=400)
                st.caption(f"Total records: {len(current_df)}")
            
            with col_after:
                st.write("**✨ After Migration:**")
                st.dataframe(simulated_df, use_container_width=True, height=400)
                st.caption(f"Total records: {len(simulated_df)}")
            
            st.divider()
            
            # Show changes summary
            new_records = len(simulated_df) - len(current_df)
            updated_records = len(st.session_state.preview_data.get('mismatched_rows_preview', []))
            
            if new_records > 0:
                st.success(f"✅ {new_records} new records will be added")
            if updated_records > 0:
                st.info(f"ℹ️ {updated_records} records will be updated")
            
            st.warning("⚠️ **This is a simulation. No data has been modified.**")
    
    with col2:
        if st.button("⚠️ EXECUTE MIGRATION", use_container_width=True, key="btn_execute"):
            # Create backup first
            with st.spinner("💾 Creating backup..."):
                backup_result = create_backup_snapshot(dest_db)
                
                if backup_result['status'] == 'success':
                    st.session_state.migration_backup_id = backup_result['backup_id']
                    st.success(f"✅ Backup created: {backup_result['backup_id']}")
                    
                    # Execute migration
                    with st.spinner("🔄 Executing migration..."):
                        all_success = True
                        total_migrated = 0
                        
                        # Migrate missing rows
                        if st.session_state.migration_scope in ['missing', 'both']:
                            missing_result = migrate_missing_rows(
                                source_db,
                                dest_db,
                                st.session_state.migration_backup_id
                            )
                            
                            if missing_result['status'] == 'success':
                                total_migrated += missing_result['rows_migrated']
                                st.success(f"✅ Migrated {missing_result['rows_migrated']} missing rows")
                            else:
                                all_success = False
                                st.error(f"❌ Error migrating missing rows: {missing_result['error']}")
                        
                        # Migrate mismatched rows
                        if st.session_state.migration_scope in ['mismatched', 'both']:
                            mismatched_result = migrate_mismatched_rows(
                                source_db,
                                dest_db,
                                st.session_state.migration_backup_id
                            )
                            
                            if mismatched_result['status'] == 'success':
                                total_migrated += mismatched_result['rows_migrated']
                                st.success(f"✅ Migrated {mismatched_result['rows_migrated']} mismatched rows")
                            else:
                                all_success = False
                                st.error(f"❌ Error migrating mismatched rows: {mismatched_result['error']}")
                        
                        if all_success:
                            st.success(f"🎉 Migration completed! {total_migrated} rows migrated.")
                            st.info(f"💾 Backup ID: {st.session_state.migration_backup_id} (for rollback if needed)")
                        else:
                            st.error("❌ Migration encountered errors. Check backup for rollback.")
                else:
                    st.error(f"❌ Failed to create backup: {backup_result['error']}")
    
    st.divider()
    
    # Step 5: Rollback
    st.subheader("Step 5️⃣: Rollback (if needed)")
    
    if st.session_state.migration_backup_id:
        st.warning(f"⚠️ Backup available: {st.session_state.migration_backup_id}")
        
        if st.button("🔙 Rollback to Backup", use_container_width=True, key="btn_rollback"):
            with st.spinner("⏮️ Rolling back..."):
                rollback_result = rollback_to_backup(
                    st.session_state.migration_backup_id,
                    dest_db
                )
                
                if rollback_result['status'] == 'success':
                    st.success(f"✅ {rollback_result['message']}")
                    st.info(f"Records restored: {rollback_result['records_restored']}")
                else:
                    st.error(f"❌ Rollback failed: {rollback_result['error']}")
    else:
        st.info("ℹ️ No active backup. Complete a migration first to enable rollback.")


# Sidebar navigation
st.sidebar.title("📍 Navigation")

page = st.sidebar.radio(
    "Select Page:",
    ["📊 Overview", "📋 Detailed Comparison", "🤖 AI Assistant", "🔄 Migration"]
)

st.sidebar.divider()

# Sidebar info
st.sidebar.subheader("ℹ️ System Status")

try:
    client = Client(host=OLLAMA_BASE_URL)
    st.sidebar.success("✅ Ollama Connected")
except:
    st.sidebar.error("❌ Ollama Not Running")

# Get database info
try:
    data = get_all_data()
    st.sidebar.info(f"""
    **Database Status:**
    - Prod: {data['quality_score']['prod_total']} records
    - Staging: {data['quality_score']['staging_total']} records
    - Quality: {data['quality_score']['quality_score']}%
    """)
except:
    st.sidebar.warning("⚠️ Database Error")

st.sidebar.divider()

# Export section
st.sidebar.subheader("📥 Export")

if st.sidebar.button("📥 Export Report to JSON"):
    try:
        result = export_report()
        st.sidebar.success("✅ Report exported!")
        st.sidebar.write(f"Location: {result['file_path']}")
    except Exception as e:
        st.sidebar.error(f"❌ Export failed: {str(e)}")

# Page routing
if page == "📊 Overview":
    page_overview()
elif page == "📋 Detailed Comparison":
    page_detailed_comparison()
elif page == "🤖 AI Assistant":
    page_ai_assistant()
elif page == "🔄 Migration":
    page_migration()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
Built with Streamlit | Powered by Ollama | MCP Integration
</div>
""", unsafe_allow_html=True)
