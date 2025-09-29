#!/usr/bin/env python3
"""
Alignment Test Runner
Runs all alignment tests and generates comprehensive reports
"""
import sys
import os
import json
import time
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_test_file(test_file):
    """Run a single test file and return results"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run pytest on the test file
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v", 
            "--tb=short",
            "--json-report",
            "--json-report-file=test_results.json"
        ], capture_output=True, text=True, cwd=project_root)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "file": test_file,
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
    except Exception as e:
        return {
            "file": test_file,
            "success": False,
            "duration": 0,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def run_ui_tests():
    """Run UI integration tests"""
    print(f"\n{'='*60}")
    print("Running UI Integration Tests")
    print(f"{'='*60}")
    
    try:
        # Import and run UI tests
        from tests.test_ui_integration import run_ui_tests
        results = run_ui_tests()
        
        return {
            "success": True,
            "results": results,
            "summary": results.get("summary", {})
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": None
        }

def main():
    """Main test runner"""
    print("Alignment Test Runner")
    print("=" * 60)
    
    # Test files to run
    test_files = [
        "tests/test_alignment_criteria_compliance.py",
        "tests/test_normalization_functions.py", 
        "tests/test_repetition_detection.py",
        "tests/test_alignment_improvements.py"  # Existing test
    ]
    
    # Results storage
    all_results = {
        "start_time": time.time(),
        "test_files": {},
        "ui_tests": None,
        "summary": {}
    }
    
    # Run individual test files
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_file in test_files:
        if os.path.exists(test_file):
            result = run_test_file(test_file)
            all_results["test_files"][test_file] = result
            
            if result["success"]:
                passed_tests += 1
                print(f"✅ {test_file} - PASSED ({result['duration']:.2f}s)")
            else:
                failed_tests += 1
                print(f"❌ {test_file} - FAILED ({result['duration']:.2f}s)")
                print(f"Error: {result['stderr']}")
        else:
            print(f"⚠️  {test_file} - NOT FOUND")
    
    total_tests = passed_tests + failed_tests
    
    # Run UI tests
    ui_result = run_ui_tests()
    all_results["ui_tests"] = ui_result
    
    if ui_result["success"]:
        print(f"✅ UI Tests - PASSED")
        ui_summary = ui_result.get("summary", {})
        print(f"   UI Test Results: {ui_summary.get('passed_tests', 0)}/{ui_summary.get('total_tests', 0)} passed")
    else:
        print(f"❌ UI Tests - FAILED")
        print(f"Error: {ui_result.get('error', 'Unknown error')}")
    
    # Calculate summary
    all_results["summary"] = {
        "total_test_files": len(test_files),
        "passed_test_files": passed_tests,
        "failed_test_files": failed_tests,
        "ui_tests_success": ui_result["success"],
        "overall_success": failed_tests == 0 and ui_result["success"],
        "total_duration": time.time() - all_results["start_time"]
    }
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Test Files: {passed_tests}/{total_tests} passed")
    print(f"UI Tests: {'PASSED' if ui_result['success'] else 'FAILED'}")
    print(f"Overall: {'PASSED' if all_results['summary']['overall_success'] else 'FAILED'}")
    print(f"Total Duration: {all_results['summary']['total_duration']:.2f} seconds")
    
    # Save detailed results
    results_file = "alignment_test_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    # Generate HTML report
    generate_html_report(all_results)
    
    return all_results["summary"]["overall_success"]

def generate_html_report(results):
    """Generate HTML test report"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alignment Test Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .test-file {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .passed {{ background-color: #d4edda; }}
            .failed {{ background-color: #f8d7da; }}
            .ui-tests {{ background-color: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Alignment Test Results</h1>
            <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Test Files:</strong> {results['summary']['passed_test_files']}/{results['summary']['total_test_files']} passed</p>
            <p><strong>UI Tests:</strong> {'PASSED' if results['summary']['ui_tests_success'] else 'FAILED'}</p>
            <p><strong>Overall:</strong> {'PASSED' if results['summary']['overall_success'] else 'FAILED'}</p>
            <p><strong>Duration:</strong> {results['summary']['total_duration']:.2f} seconds</p>
        </div>
    """
    
    # Test files section
    html_content += "<h2>Test Files</h2>"
    for test_file, result in results["test_files"].items():
        status_class = "passed" if result["success"] else "failed"
        status_icon = "✅" if result["success"] else "❌"
        
        html_content += f"""
        <div class="test-file {status_class}">
            <h3>{status_icon} {test_file}</h3>
            <p><strong>Status:</strong> {'PASSED' if result['success'] else 'FAILED'}</p>
            <p><strong>Duration:</strong> {result['duration']:.2f} seconds</p>
        """
        
        if not result["success"] and result["stderr"]:
            html_content += f"<pre>{result['stderr']}</pre>"
        
        html_content += "</div>"
    
    # UI tests section
    if results["ui_tests"]:
        ui_result = results["ui_tests"]
        ui_status_class = "passed" if ui_result["success"] else "failed"
        ui_status_icon = "✅" if ui_result["success"] else "❌"
        
        html_content += f"""
        <div class="ui-tests">
            <h2>{ui_status_icon} UI Integration Tests</h2>
            <p><strong>Status:</strong> {'PASSED' if ui_result['success'] else 'FAILED'}</p>
        """
        
        if ui_result["success"] and "summary" in ui_result:
            summary = ui_result["summary"]
            html_content += f"""
            <p><strong>Tests:</strong> {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)} passed</p>
            <p><strong>Success Rate:</strong> {summary.get('success_rate', 0):.1f}%</p>
            """
        
        if not ui_result["success"] and "error" in ui_result:
            html_content += f"<pre>{ui_result['error']}</pre>"
        
        html_content += "</div>"
    
    html_content += """
    </body>
    </html>
    """
    
    # Save HTML report
    with open("alignment_test_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("HTML report generated: alignment_test_report.html")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

