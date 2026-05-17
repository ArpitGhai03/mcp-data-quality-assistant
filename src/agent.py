"""
Agent that connects Ollama to tools.py with a reasoning loop.
This agent uses local LLM (via Ollama) to reason about user queries and call appropriate tools.
Will be replaced by MCP in future versions.
"""

import json
import sys
from typing import Any, Dict, List
from ollama import Client
from tools import (
    get_missing_rows,
    get_mismatched_rows,
    get_quality_score,
    run_full_comparison,
    export_report
)

# ---------- Configuration ----------
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL = "llama3"  # Can be changed to "gemma3" if preferred

# Available tools definition
AVAILABLE_TOOLS = {
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

# System prompt for the agent
SYSTEM_PROMPT = """You are a data quality assistant that helps analyze and compare databases.
You have access to the following tools to perform database comparisons:

1. get_missing_rows - Get rows missing in staging database
2. get_mismatched_rows - Get rows with data differences
3. get_quality_score - Get overall quality metrics
4. run_full_comparison - Run complete analysis
5. export_report - Export results to JSON file

When the user asks a question about database quality or comparison:
1. Identify which tool(s) would best answer the question
2. Call the appropriate tool(s)
3. Analyze and explain the results to the user

Always be helpful and provide actionable insights based on the data."""


# ---------- Ollama Client ----------
def get_ollama_client() -> Client:
    """Initialize and return Ollama client."""
    return Client(host=OLLAMA_BASE_URL)


# ---------- Tool Calling ----------
def call_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Call a tool from tools.py.
    
    Args:
        tool_name: Name of the tool to call
        **kwargs: Arguments to pass to the tool
    
    Returns:
        Result from the tool
    """
    if tool_name not in AVAILABLE_TOOLS:
        return {
            'error': f"Unknown tool: {tool_name}",
            'available_tools': list(AVAILABLE_TOOLS.keys())
        }
    
    tool_config = AVAILABLE_TOOLS[tool_name]
    tool_func = tool_config['function']
    
    try:
        # Call the tool with provided arguments
        if kwargs:
            result = tool_func(**kwargs)
        else:
            result = tool_func()
        
        return {
            'status': 'success',
            'tool': tool_name,
            'result': result
        }
    except Exception as e:
        return {
            'status': 'error',
            'tool': tool_name,
            'error': str(e)
        }


def parse_tool_calls(response_text: str) -> List[Dict[str, str]]:
    """
    Parse tool calls from LLM response.
    Looks for patterns like: CALL_TOOL: tool_name(args) or - tool_name()
    """
    tool_calls = []
    lines = response_text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Check for tool call patterns
        if 'CALL_TOOL:' in line or 'TOOL:' in line or (line.startswith('-') and '(' in line):
            # Extract the call part
            if 'CALL_TOOL:' in line:
                call_part = line.split('CALL_TOOL:', 1)[1].strip()
            elif 'TOOL:' in line:
                call_part = line.split('TOOL:', 1)[1].strip()
            else:
                # Format: - tool_name()
                call_part = line.lstrip('- ').strip()
            
            if '(' in call_part and ')' in call_part:
                tool_name = call_part[:call_part.index('(')].strip()
                args_str = call_part[call_part.index('(') + 1:call_part.rindex(')')].strip()
            elif call_part.strip() in AVAILABLE_TOOLS:
                tool_name = call_part.strip()
                args_str = ""
            else:
                continue
            
            tool_calls.append({
                'tool': tool_name,
                'args': args_str
            })
    
    return tool_calls


# ---------- Reasoning Loop ----------
def reasoning_loop(user_query: str, max_iterations: int = 3) -> Dict[str, Any]:
    """
    Execute the reasoning loop.
    
    Args:
        user_query: The user's question or request
        max_iterations: Maximum number of reasoning iterations
    
    Returns:
        Dict with the final response and execution details
    """
    client = get_ollama_client()
    
    conversation_history = []
    tool_results = []
    
    print(f"\n🤖 Agent Processing Query: {user_query}")
    print("=" * 80)
    
    for iteration in range(max_iterations):
        print(f"\n[Iteration {iteration + 1}/{max_iterations}]")
        
        # Build the prompt
        prompt = f"User Query: {user_query}\n\n"
        
        if tool_results:
            prompt += "Previous Tool Results:\n"
            for result in tool_results:
                prompt += f"- Tool: {result['tool']}\n"
                prompt += f"  Result: {json.dumps(result['result'], indent=2)}\n\n"
        
        prompt += "\nBased on the query and any previous results, decide what to do next."
        prompt += "\nIf you need to gather more information, respond with: CALL_TOOL: tool_name"
        prompt += "\nIf you have enough information to answer, respond with: FINAL_ANSWER: <your analysis>"
        
        # Call Ollama
        try:
            response = client.generate(
                model=MODEL,
                prompt=prompt,
                system=SYSTEM_PROMPT,
                stream=False
            )
            
            response_text = response['response']
            print(f"Agent Response:\n{response_text}")
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Failed to call Ollama: {str(e)}",
                'suggestion': "Make sure Ollama is running: ollama serve"
            }
        
        # Parse tool calls
        # First check for final answer (with or without markdown)
        if 'FINAL_ANSWER' in response_text.upper():
            # Extract the answer, handling markdown formatting
            import re
            # Look for FINAL_ANSWER: or **FINAL_ANSWER:** patterns
            match = re.search(r'\*?\*?FINAL_ANSWER\*?\*?\s*:\s*(.*?)(?:\n|$)', response_text, re.IGNORECASE | re.DOTALL)
            if match:
                final_answer = match.group(1).strip()
                # Clean up the answer
                final_answer = final_answer.split('\n')[0].strip()  # Get first line only
                print(f"\n✅ Final Answer: {final_answer}")
                return {
                    'status': 'success',
                    'answer': final_answer,
                    'iterations': iteration + 1,
                    'tool_results': tool_results
                }
        
        # Check for tool calls
        tool_calls = parse_tool_calls(response_text)
        
        if not tool_calls:
            # No tool calls and no final answer, maybe LLM is thinking
            print("Processing response (no tools called)...")
            continue
        
        # Execute tool calls
        for tool_call in tool_calls:
            tool_name = tool_call['tool']
            args_str = tool_call['args']
            
            print(f"Calling tool: {tool_name}")
            
            # Parse arguments if any
            kwargs = {}
            if args_str:
                # Simple argument parsing
                for arg in args_str.split(','):
                    arg = arg.strip()
                    if '=' in arg:
                        key, value = arg.split('=', 1)
                        kwargs[key.strip()] = value.strip().strip("'\"")
                    else:
                        # Positional argument
                        if tool_name == 'export_report' and not kwargs:
                            kwargs['output_file'] = arg
            
            result = call_tool(tool_name, **kwargs)
            tool_results.append(result)
            print(f"Tool result: {json.dumps(result, indent=2)}\n")
    
    return {
        'status': 'incomplete',
        'message': 'Max iterations reached without final answer',
        'iterations': max_iterations,
        'tool_results': tool_results
    }


# ---------- Main Interface ----------
def run_agent(query: str = None):
    """
    Run the agent with a user query.
    
    Args:
        query: User query. If None, prompt for input.
    """
    if query is None:
        print("\n🤖 Database Quality Analysis Agent")
        print("=" * 80)
        print("Available tools: missing_rows, mismatched_rows, quality_score, full_comparison, export_report")
        print("Type 'exit' to quit\n")
        
        while True:
            query = input("You: ").strip()
            
            if query.lower() == 'exit':
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            result = reasoning_loop(query)
            print(json.dumps(result, indent=2))
    else:
        result = reasoning_loop(query)
        return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Query provided as argument
        query = " ".join(sys.argv[1:])
        result = run_agent(query)
        print(json.dumps(result, indent=2))
    else:
        # Interactive mode
        run_agent()
