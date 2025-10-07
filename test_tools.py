#!/usr/bin/env python3
"""
Comprehensive Tool Implementation Testing Script
Tests all tools in test_against_manifest/ directory
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, Tuple


class ToolTester:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.results = {
            "passed": [],
            "failed": [],
            "total": 0
        }
    
    def run_tool(self, tool_path: Path, params: Dict[str, Any]) -> Tuple[bool, Any]:
        """Run a tool and return success status and result"""
        script_path = tool_path / "scripts"
        
        # Find the script file
        script_file = None
        for ext in ['py', 'sh']:
            possible_files = list(script_path.glob(f'*.{ext}'))
            if possible_files:
                script_file = possible_files[0]
                break
        
        if not script_file:
            return False, "No script file found"
        
        try:
            if script_file.suffix == '.py':
                result = subprocess.run(
                    ["python3", str(script_file), json.dumps(params)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                return False, "Unsupported script type"
            
            if result.returncode != 0:
                return False, f"Exit code {result.returncode}: {result.stderr}"
            
            if result.stdout.strip():
                output = json.loads(result.stdout)
                return output.get("success", False), output
            else:
                return False, "No output"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except Exception as e:
            return False, str(e)
    
    def test_calculator(self) -> Dict[str, Any]:
        """Test calculator tool"""
        tool_path = self.base_path / "tools/simple/calculator"
        tests = [
            {
                "name": "Addition",
                "params": {"operation": "add", "a": 5, "b": 3},
                "expected": 8
            },
            {
                "name": "Subtraction",
                "params": {"operation": "subtract", "a": 10, "b": 4},
                "expected": 6
            },
            {
                "name": "Multiplication",
                "params": {"operation": "multiply", "a": 6, "b": 7},
                "expected": 42
            },
            {
                "name": "Division",
                "params": {"operation": "divide", "a": 10, "b": 2},
                "expected": 5.0
            },
            {
                "name": "Health check",
                "params": {"operation": "health_check"},
                "expected": None  # Just check success
            }
        ]
        
        results = []
        for test in tests:
            success, output = self.run_tool(tool_path, test["params"])
            passed = success
            if passed and test["expected"] is not None:
                passed = output.get("result") == test["expected"]
            
            results.append({
                "name": test["name"],
                "passed": passed,
                "output": output if not passed else None
            })
        
        return {
            "tool": "calculator",
            "tests": results,
            "passed": all(r["passed"] for r in results)
        }
    
    def test_text_analyzer(self) -> Dict[str, Any]:
        """Test text analyzer tool"""
        tool_path = self.base_path / "tools/simple/text_analyzer"
        tests = [
            {
                "name": "Analyze text",
                "params": {"operation": "analyze", "text": "This is a wonderful test!"},
                "check": lambda o: o.get("word_count") == 5
            },
            {
                "name": "Health check",
                "params": {"operation": "health_check"},
                "check": lambda o: True  # Just check success
            }
        ]
        
        results = []
        for test in tests:
            success, output = self.run_tool(tool_path, test["params"])
            passed = success and test["check"](output)
            
            results.append({
                "name": test["name"],
                "passed": passed,
                "output": output if not passed else None
            })
        
        return {
            "tool": "text_analyzer",
            "tests": results,
            "passed": all(r["passed"] for r in results)
        }
    
    def test_time_tool(self) -> Dict[str, Any]:
        """Test time tool (local to assistant agent)"""
        tool_path = self.base_path / "agents/simple/assistant/tools/time_tool"
        tests = [
            {
                "name": "Get datetime",
                "params": {"operation": "get_datetime"},
                "check": lambda o: "datetime" in o
            },
            {
                "name": "Health check",
                "params": {"operation": "health_check"},
                "check": lambda o: True
            }
        ]
        
        results = []
        for test in tests:
            success, output = self.run_tool(tool_path, test["params"])
            passed = success and test["check"](output)
            
            results.append({
                "name": test["name"],
                "passed": passed,
                "output": output if not passed else None
            })
        
        return {
            "tool": "time_tool",
            "tests": results,
            "passed": all(r["passed"] for r in results)
        }
    
    def test_stats_tool(self) -> Dict[str, Any]:
        """Test stats tool (local to analyzer sub-agent)"""
        tool_path = self.base_path / "agents/complex/data_processor/agents/analyzer/tools/stats_tool"
        tests = [
            {
                "name": "Calculate mean",
                "params": {"operation": "mean", "data": [1, 2, 3, 4, 5]},
                "check": lambda o: o.get("result") == 3.0
            },
            {
                "name": "Summary stats",
                "params": {"operation": "summary", "data": [1, 2, 3, 4, 5]},
                "check": lambda o: "summary" in o
            },
            {
                "name": "Health check",
                "params": {"operation": "health_check"},
                "check": lambda o: True
            }
        ]
        
        results = []
        for test in tests:
            success, output = self.run_tool(tool_path, test["params"])
            passed = success and test["check"](output)
            
            results.append({
                "name": test["name"],
                "passed": passed,
                "output": output if not passed else None
            })
        
        return {
            "tool": "stats_tool",
            "tests": results,
            "passed": all(r["passed"] for r in results)
        }
    
    def run_all_tests(self):
        """Run all tool tests"""
        print(f"\n{'='*70}")
        print(f"🧪 Testing Tool Implementations")
        print(f"{'='*70}\n")
        
        tool_tests = [
            self.test_calculator,
            self.test_text_analyzer,
            self.test_time_tool,
            self.test_stats_tool
        ]
        
        for test_func in tool_tests:
            result = test_func()
            self.results["total"] += 1
            
            if result["passed"]:
                self.results["passed"].append(result)
                status_icon = "✅"
                status_color = "\033[92m"
            else:
                self.results["failed"].append(result)
                status_icon = "❌"
                status_color = "\033[91m"
            
            print(f"{status_icon} {status_color}{result['tool']}\033[0m")
            
            for test in result["tests"]:
                test_icon = "  ✓" if test["passed"] else "  ✗"
                print(f"{test_icon} {test['name']}")
                if not test["passed"] and test["output"]:
                    print(f"    Output: {test['output']}")
            
            print()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*70}")
        print("📊 Test Summary")
        print(f"{'='*70}")
        print(f"Total Tools:  {self.results['total']}")
        print(f"✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        
        if self.results["failed"]:
            print(f"\n{'='*70}")
            print("❌ Failed Tools:")
            print(f"{'='*70}")
            for failed in self.results["failed"]:
                print(f"  - {failed['tool']}")
                for test in failed["tests"]:
                    if not test["passed"]:
                        print(f"    ✗ {test['name']}")
        
        print(f"{'='*70}\n")
        
        return len(self.results["failed"]) == 0


def main():
    base_path = Path(__file__).parent / "test_against_manifest"
    
    if not base_path.exists():
        print(f"❌ Error: {base_path} does not exist")
        sys.exit(1)
    
    tester = ToolTester(base_path)
    tester.run_all_tests()
    success = tester.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
