"""
Simple test of MCP Server with Ollama - without pipes.
This version tests the tools directly and uses Ollama to recommend which tool to use.
"""

import json
from ollama import Client
from tools import (
    get_missing_rows,
    get_mismatched_rows,
    get_quality_score,
    run_full_comparison,
    export_report
)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL = "llama3"

# Tool definitions
TOOLS_AVAILABLE = {
    "get_missing_rows": {
        "description": "Get all rows that exist in Production DB but are missing in Staging DB",
        "function": get_missing_rows
    },
    "get_mismatched_rows": {
        "description": "Get all rows with data differences between Production and Staging",
        "function": get_mismatched_rows
    },
    "get_quality_score": {
        "description": "Get overall data quality score and metrics",
        "function": get_quality_score
    },
    "run_full_comparison": {
        "description": "Run a complete comparison between Production and Staging",
        "function": run_full_comparison
    },
    "export_report": {
        "description": "Export the comparison report to JSON",
        "function": export_report
    }
}


def call_tool(tool_name: str, **kwargs) -> dict:
    """Call a tool and return results."""
    if tool_name not in TOOLS_AVAILABLE:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        tool_func = TOOLS_AVAILABLE[tool_name]["function"]
        if kwargs:
            result = tool_func(**kwargs)
        else:
            result = tool_func()
        return {
            "status": "success",
            "tool": tool_name,
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "tool": tool_name,
            "error": str(e)
        }


def use_ollama_with_mcp(user_query: str):
    """Use Ollama to decide which MCP tool to use."""
    client = Client(host=OLLAMA_BASE_URL)
    
    # Build tools description for Ollama
    tools_desc = "\n".join([
        f"- {name}: {config['description']}"
        for name, config in TOOLS_AVAILABLE.items()
    ])
    
    system_prompt = f"""You are a database quality analysis assistant.
You have access to these tools:

{tools_desc}

When a user asks a question:
1. Identify which tool(s) would best answer it
2. Respond with: TOOL: <tool_name>
3. Provide a brief explanation

Always recommend exactly ONE tool."""
    
    print(f"\n{'='*80}")
    print(f"🤖 Query: {user_query}")
    print(f"{'='*80}")
    
    try:
        # Get Ollama's recommendation
        response = client.generate(
            model=MODEL,
            prompt=user_query,
            system=system_prompt,
            stream=False
        )
        
        response_text = response['response']
        print(f"\n📝 Ollama Recommendation:\n{response_text}")
        
        # Parse tool recommendation
        tool_name = None
        for line in response_text.split('\n'):
            if "TOOL:" in line:
                try:
                    tool_name = line.split("TOOL:")[1].strip().split()[0]
                    break
                except:
                    pass
        
        if tool_name and tool_name in TOOLS_AVAILABLE:
            print(f"\n🔧 Executing tool: {tool_name}")
            result = call_tool(tool_name)
            
            if result["status"] == "success":
                print(f"\n✅ Tool executed successfully!")
                print(f"\n📊 Result Summary:")
                
                # Display result nicely
                result_data = result["result"]
                if isinstance(result_data, dict):
                    # Display key metrics
                    if "quality_score" in result_data:
                        print(f"   Quality Score: {result_data['quality_score']}%")
                    if "count" in result_data:
                        print(f"   Count: {result_data['count']}")
                    if "percentage" in result_data:
                        print(f"   Percentage: {result_data['percentage']}%")
                    if "missing_percentage" in result_data:
                        print(f"   Missing: {result_data['missing_percentage']}%")
                    if "mismatched_percentage" in result_data:
                        print(f"   Mismatched: {result_data['mismatched_percentage']}%")
                
                print(f"\n📋 Full Result (JSON):")
                print(json.dumps(result_data, indent=2)[:500] + "..." if len(json.dumps(result_data)) > 500 else json.dumps(result_data, indent=2))
                
                return result_data
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                return None
        else:
            print(f"\n⚠️  No valid tool found in Ollama response")
            print(f"   Parsed tool name: {tool_name}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Make sure Ollama is running: ollama serve")
        return None


def main():
    """Main test function."""
    print("\n" + "="*80)
    print("🔗 MCP Server + Ollama Integration Test")
    print("="*80)
    
    # Test queries
    test_queries = [
        "What is the data quality score?",
        "Show me which rows are missing from staging",
        "Generate a full database comparison report",
    ]
    
    results = []
    for query in test_queries:
        result = use_ollama_with_mcp(query)
        results.append({
            "query": query,
            "result": result
        })
        print()
    
    print("\n" + "="*80)
    print("✨ Test Summary")
    print("="*80)
    print(f"Completed {len(results)} queries with Ollama + MCP tools")
    print("\nAvailable tools demonstrated:")
    for tool_name, config in TOOLS_AVAILABLE.items():
        print(f"  ✓ {tool_name}: {config['description']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
