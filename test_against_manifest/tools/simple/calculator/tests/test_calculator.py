#!/usr/bin/env python3
"""
Tests for calculator tool
"""
import json
import subprocess
import sys


def run_calculator(params):
    """Run calculator with given parameters"""
    result = subprocess.run(
        ["python3", "scripts/calculator.py", json.dumps(params)],
        capture_output=True,
        text=True,
        cwd="/home/mlamkadm/repos/Cortex-Prime-MK1/test_against_manifest/tools/simple/calculator"
    )
    if result.stdout.strip():
        return json.loads(result.stdout)
    else:
        return {"success": False, "error": result.stderr}


def test_addition():
    """Test addition"""
    result = run_calculator({"operation": "add", "a": 5, "b": 3})
    assert result["success"] == True
    assert result["result"] == 8
    print("✓ Addition test passed")


def test_division():
    """Test division"""
    result = run_calculator({"operation": "divide", "a": 10, "b": 2})
    assert result["success"] == True
    assert result["result"] == 5.0
    print("✓ Division test passed")


def test_division_by_zero():
    """Test division by zero"""
    result = run_calculator({"operation": "divide", "a": 10, "b": 0})
    assert result["success"] == False
    assert "zero" in result["error"].lower()
    print("✓ Division by zero test passed")


def test_health_check():
    """Test health check"""
    result = run_calculator({"operation": "health_check"})
    assert result["success"] == True
    assert result["status"] == "ok"
    print("✓ Health check test passed")


if __name__ == "__main__":
    try:
        test_addition()
        test_division()
        test_division_by_zero()
        test_health_check()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
