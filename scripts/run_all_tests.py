#!/usr/bin/env python3
"""
Master Test Suite for test_against_manifest directory
Validates manifests and tests tool implementations
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*70}")
    print(f"🔬 {description}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    start_time = datetime.now()
    
    print(f"\n{'#'*70}")
    print(f"# Cortex-Prime MK1 - Test Against Manifest Suite")
    print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")
    
    results = {}
    
    # Test 1: Validate all manifests
    results['manifest_validation'] = run_command(
        "python3 test_manifests.py",
        "Phase 1: Manifest Validation"
    )
    
    # Test 2: Test all tool implementations
    results['tool_tests'] = run_command(
        "python3 test_tools.py",
        "Phase 2: Tool Implementation Tests"
    )
    
    # Test 3: Run calculator unit tests
    results['calculator_unit_tests'] = run_command(
        "python3 test_against_manifest/tools/simple/calculator/tests/test_calculator.py",
        "Phase 3: Calculator Unit Tests"
    )
    
    # Print final summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"\n{'#'*70}")
    print(f"# Final Test Report")
    print(f"{'#'*70}\n")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*70}")
    print(f"Overall Results: {passed_tests}/{total_tests} test suites passed")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    print(f"{'='*70}\n")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Manifests are ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
