"""
Streamlit Dashboard for Database Quality Analysis
Integrates tools.py, Ollama, and MCP for a complete analysis platform
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.graph_objects as go
from tools import (
    get_missing_rows,
    get_mismatched_rows,
    get_quality_score,
    run_full_comparison,
    export_report
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
    
    st.divider()
    
    # Input section
    st.subheader("📝 Ask a Question")
    
    # Quick templates
    col1, col2, col3 = st.columns(3)
    
    quick_queries = [
        "What is the data quality score?",
        "Show me missing rows",
        "What data is different?"
    ]
    
    selected_query = None
    
    with col1:
        if st.button("🎯 Quality Score"):
            selected_query = quick_queries[0]
    
    with col2:
        if st.button("📍 Missing Rows"):
            selected_query = quick_queries[1]
    
    with col3:
        if st.button("🔄 Data Differences"):
            selected_query = quick_queries[2]
    
    st.write("**OR**")
    
    # Custom query input
    user_query = st.text_area(
        "Enter your question:",
        value=selected_query or "",
        placeholder="e.g., Why are we missing data? What's the quality score?",
        height=80
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        analyze_button = st.button("🔍 Analyze", use_container_width=True)
    
    if analyze_button and user_query:
        st.divider()
        
        with st.spinner("🤖 Ollama is thinking..."):
            try:
                client = Client(host=OLLAMA_BASE_URL)
                
                # System prompt
                system_prompt = """You are a database quality analysis expert.
You have access to these analysis tools:
- get_quality_score: Get overall data quality metrics
- get_missing_rows: Find rows missing in staging
- get_mismatched_rows: Find rows with data differences
- run_full_comparison: Run complete analysis
- export_report: Export report to JSON

Analyze the user query and respond with:
TOOL: <tool_name>
EXPLANATION: <brief explanation of what this tool will do>

Then wait for the results."""
                
                # Get Ollama recommendation
                response = client.generate(
                    model=MODEL,
                    prompt=user_query,
                    system=system_prompt,
                    stream=False
                )
                
                response_text = response['response']
                
                # Parse tool recommendation
                tool_name = None
                explanation = ""
                
                for line in response_text.split('\n'):
                    if "TOOL:" in line:
                        try:
                            tool_name = line.split("TOOL:")[1].strip().split()[0]
                        except:
                            pass
                    if "EXPLANATION:" in line:
                        try:
                            explanation = line.split("EXPLANATION:")[1].strip()
                        except:
                            pass
                
                # Display Ollama's recommendation
                st.subheader("🔍 Analysis Plan")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"**Tool Selected:** {tool_name or 'Not found'}")
                
                with col2:
                    st.info(f"**Approach:** {explanation or 'Will execute tool'}")
                
                st.divider()
                
                # Execute tool if found
                if tool_name:
                    available_tools = {
                        'get_quality_score': get_quality_score,
                        'get_missing_rows': get_missing_rows,
                        'mismatched_rows': get_mismatched_rows,
                        'get_mismatched_rows': get_mismatched_rows,
                        'run_full_comparison': run_full_comparison,
                        'export_report': export_report
                    }
                    
                    tool_func = available_tools.get(tool_name)
                    
                    if tool_func:
                        st.subheader("⚙️ Executing Tool...")
                        
                        with st.spinner(f"Executing {tool_name}..."):
                            try:
                                if tool_name == 'export_report':
                                    result = tool_func()
                                else:
                                    result = tool_func()
                                
                                st.success("✅ Tool executed successfully!")
                                
                                st.subheader("📊 Results")
                                
                                # Display results nicely
                                if isinstance(result, dict):
                                    # Show key metrics
                                    metrics_cols = st.columns(4)
                                    
                                    if 'quality_score' in result:
                                        with metrics_cols[0]:
                                            st.metric("Quality Score", f"{result['quality_score']}%")
                                    
                                    if 'count' in result:
                                        with metrics_cols[1]:
                                            st.metric("Count", result['count'])
                                    
                                    if 'percentage' in result:
                                        with metrics_cols[2]:
                                            st.metric("Percentage", f"{result['percentage']}%")
                                    
                                    if 'missing_count' in result:
                                        with metrics_cols[3]:
                                            st.metric("Missing", result['missing_count'])
                                    
                                    # Show detailed data
                                    st.subheader("📋 Detailed Data")
                                    
                                    if 'rows' in result and result['rows']:
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
                                    
Result:
{json.dumps(result, indent=2)[:500]}

Keep it to 2-3 sentences maximum."""
                                    
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
                        st.warning(f"⚠️ Tool '{tool_name}' not found. Using default analysis.")
                        
                        # Fallback: show full comparison
                        data = get_all_data()
                        st.json(data['full_comparison'])
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Make sure Ollama is running: `ollama serve`")
    
    elif analyze_button and not user_query:
        st.warning("⚠️ Please enter a question first!")


# Sidebar navigation
st.sidebar.title("📍 Navigation")

page = st.sidebar.radio(
    "Select Page:",
    ["📊 Overview", "📋 Detailed Comparison", "🤖 AI Assistant"]
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

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
Built with Streamlit | Powered by Ollama | MCP Integration
</div>
""", unsafe_allow_html=True)
