"""
Multi-Agent Application - Main Entry Point
Provides both CLI and API interfaces for the multi-agent system
"""
import os
import sys
import json
import argparse
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from orchestrator import AgentOrchestrator
from agents import WeatherAgent, EnvironmentalAgent, AzureAgent


def run_cli():
    """Run the application in CLI mode"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent System for Weather, Environmental, and Azure Data"
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "query", "report"],
        default="interactive",
        help="Application mode"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query to process (for query mode)"
    )
    parser.add_argument(
        "--location",
        type=str,
        default="London",
        help="Location for data queries"
    )
    parser.add_argument(
        "--agent",
        choices=["weather", "environmental", "azure", "all"],
        default="all",
        help="Specific agent to use"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (JSON format)"
    )
    
    args = parser.parse_args()
    
    orchestrator = AgentOrchestrator()
    
    if args.mode == "interactive":
        run_interactive_mode(orchestrator)
    elif args.mode == "query":
        if not args.query:
            print("Error: --query is required for query mode")
            sys.exit(1)
        result = orchestrator.process_query(args.query, {"location": args.location})
        print_result(result, args.output)
    elif args.mode == "report":
        result = orchestrator.get_comprehensive_report(args.location)
        print_result(result, args.output)


def run_interactive_mode(orchestrator: AgentOrchestrator):
    """Run the application in interactive CLI mode"""
    print("=" * 60)
    print("Multi-Agent System - Interactive Mode")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  query <your question>  - Ask a question to the agents")
    print("  report <location>      - Generate comprehensive report")
    print("  capabilities          - List available agent capabilities")
    print("  help                  - Show this help message")
    print("  exit                  - Exit the application")
    print("=" * 60)
    
    location = "London"  # Default location
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
                
            if user_input.lower() == "help":
                print("\nAvailable commands:")
                print("  query <your question>  - Ask a question to the agents")
                print("  report <location>      - Generate comprehensive report")
                print("  capabilities          - List available agent capabilities")
                print("  help                  - Show this help message")
                print("  exit                  - Exit the application")
                continue
                
            if user_input.lower() == "capabilities":
                capabilities = orchestrator.get_available_capabilities()
                print("\nAvailable Agent Capabilities:")
                for agent, funcs in capabilities.items():
                    print(f"\n{agent}:")
                    for func in funcs:
                        print(f"  - {func}")
                continue
                
            if user_input.lower().startswith("report"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    location = parts[1]
                print(f"\nGenerating comprehensive report for {location}...")
                result = orchestrator.get_comprehensive_report(location)
                print(json.dumps(result, indent=2))
                continue
                
            if user_input.lower().startswith("query"):
                query = user_input[5:].strip()
                if query:
                    result = orchestrator.process_query(query, {"location": location})
                    print("\nResults:")
                    print(json.dumps(result, indent=2))
                else:
                    print("Please provide a query after 'query' command")
                continue
                
            # Default: treat input as a query
            result = orchestrator.process_query(user_input, {"location": location})
            print("\nResults:")
            print(json.dumps(result, indent=2))
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


def print_result(result: dict, output_file: Optional[str] = None):
    """Print or save result
    
    Args:
        result: Result dictionary to print/save
        output_file: Optional file path to save results
    """
    formatted_result = json.dumps(result, indent=2)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(formatted_result)
        print(f"Results saved to {output_file}")
    else:
        print(formatted_result)


def main():
    """Main entry point"""
    run_cli()


if __name__ == "__main__":
    main()
