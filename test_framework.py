#!/usr/bin/env python3
"""
File-Based Testing Framework

A simple yet powerful framework for running tests defined in text files.
Tests are defined in .test files with a simple format.
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import argparse

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    description: str
    input_data: str
    expected_output: str
    test_type: str = "exact"  # exact, contains, regex, json
    file_path: str = ""
    line_number: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Represents the result of a test execution."""
    test_case: TestCase
    passed: bool
    actual_output: str
    error_message: str = ""
    execution_time: float = 0.0


class TestParser:
    """Parses test files and extracts test cases."""
    
    def __init__(self):
        self.test_case_pattern = re.compile(
            r'###\s*TEST:\s*(.+?)$', re.MULTILINE
        )
    
    def parse_file(self, file_path: str) -> List[TestCase]:
        """Parse a test file and return list of test cases."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        test_cases = []
        sections = content.split('### TEST:')
        
        for section in sections[1:]:  # Skip first empty section
            test_case = self._parse_test_section(section, file_path)
            if test_case:
                test_cases.append(test_case)
        
        return test_cases
    
    def _parse_test_section(self, section: str, file_path: str) -> Optional[TestCase]:
        """Parse a single test section."""
        lines = section.strip().split('\n')
        if not lines:
            return None
        
        name = lines[0].strip()
        description = ""
        input_data = ""
        expected_output = ""
        test_type = "exact"
        tags = []
        
        current_block = None
        block_content = []
        
        if os.environ.get('TEST_DEBUG'):
            print(f"\n=== PARSING TEST: {name} ===")
        
        for line in lines[1:]:
            stripped = line.strip()
            
            if os.environ.get('TEST_DEBUG'):
                print(f"Line: '{stripped}' | Block: {current_block}")
            
            if stripped.startswith('DESCRIPTION:'):
                # Save previous block
                if current_block == 'description':
                    description = '\n'.join(block_content).strip()
                elif current_block == 'input':
                    input_data = '\n'.join(block_content).strip()
                elif current_block == 'expected':
                    expected_output = '\n'.join(block_content).strip()
                
                current_block = 'description'
                desc_value = stripped[12:].strip()  # Skip 'DESCRIPTION:'
                block_content = [desc_value] if desc_value else []
                
            elif stripped.startswith('INPUT:'):
                # Save previous block
                if current_block == 'description':
                    description = '\n'.join(block_content).strip()
                elif current_block == 'input':
                    input_data = '\n'.join(block_content).strip()
                elif current_block == 'expected':
                    expected_output = '\n'.join(block_content).strip()
                
                current_block = 'input'
                input_value = stripped[6:].strip()  # Skip 'INPUT:'
                block_content = [input_value] if input_value else []
                
            elif stripped.startswith('EXPECTED:'):
                # Save previous block
                if current_block == 'description':
                    description = '\n'.join(block_content).strip()
                elif current_block == 'input':
                    input_data = '\n'.join(block_content).strip()
                elif current_block == 'expected':
                    expected_output = '\n'.join(block_content).strip()
                
                current_block = 'expected'
                expected_value = stripped[9:].strip()  # Skip 'EXPECTED:'
                block_content = [expected_value] if expected_value else []
                
            elif stripped.startswith('TYPE:'):
                test_type = stripped[5:].strip().lower()
                
            elif stripped.startswith('TAGS:'):
                tags = [t.strip() for t in stripped[5:].split(',')]
                
            elif stripped:  # Non-empty line
                if current_block:
                    block_content.append(stripped)
        
        # Save last block
        if current_block == 'description':
            description = '\n'.join(block_content).strip()
        elif current_block == 'input':
            input_data = '\n'.join(block_content).strip()
        elif current_block == 'expected':
            expected_output = '\n'.join(block_content).strip()
        
        if os.environ.get('TEST_DEBUG'):
            print(f"PARSED - Input: '{input_data}' | Expected: '{expected_output}'")
            print("=" * 50)
        
        return TestCase(
            name=name,
            description=description,
            input_data=input_data,
            expected_output=expected_output,
            test_type=test_type,
            file_path=file_path,
            tags=tags
        )
    
    def _save_block(self, block_type: str, content: List[str], var_dict: dict):
        """Helper to save parsed block content."""
        text = '\n'.join(content).strip()
        if block_type == 'description':
            var_dict['description'] = text
        elif block_type == 'input':
            var_dict['input_data'] = text
        elif block_type == 'expected':
            var_dict['expected_output'] = text
    
    def _save_block_to_vars(self, block_type: str, content: List[str], var_dict: dict):
        """Save block content to local variables."""
        text = '\n'.join(content).strip()
        if block_type == 'description':
            var_dict['description'] = text
        elif block_type == 'input':
            var_dict['input_data'] = text
        elif block_type == 'expected':
            var_dict['expected_output'] = text


class TestRunner:
    """Executes tests and compares results."""
    
    def __init__(self, command_template: Optional[str] = None):
        self.command_template = command_template or "echo {input}"
    
    def run_test(self, test_case: TestCase) -> TestResult:
        """Run a single test case."""
        start_time = datetime.now()
        
        try:
            # Execute the command
            actual_output = self._execute_command(test_case.input_data)
            
            # Compare results
            passed = self._compare_output(
                test_case.expected_output,
                actual_output,
                test_case.test_type
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_case=test_case,
                passed=passed,
                actual_output=actual_output,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_case=test_case,
                passed=False,
                actual_output="",
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _execute_command(self, input_data: str) -> str:
        """Execute the test command with input."""
        # Properly escape the input for Windows PowerShell/CMD
        # Escape double quotes and wrap in double quotes
        escaped_input = input_data.replace('"', '""')
        cmd = self.command_template.replace('{input}', f'"{escaped_input}"')
        
        # Debug output
        if os.environ.get('TEST_DEBUG'):
            print(f"DEBUG: Command: {cmd}")
            print(f"DEBUG: Input: {input_data}")
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if os.environ.get('TEST_DEBUG'):
            print(f"DEBUG: stdout: {result.stdout}")
            print(f"DEBUG: stderr: {result.stderr}")
            print(f"DEBUG: returncode: {result.returncode}")
        
        return result.stdout.strip()
    
    def _compare_output(self, expected: str, actual: str, test_type: str) -> bool:
        """Compare expected and actual output based on test type."""
        # Normalize whitespace
        expected = expected.strip()
        actual = actual.strip()
        
        if test_type == "exact":
            return expected == actual
        elif test_type == "contains":
            return expected in actual
        elif test_type == "regex":
            return bool(re.search(expected, actual))
        elif test_type == "json":
            try:
                expected_json = json.loads(expected)
                actual_json = json.loads(actual)
                return expected_json == actual_json
            except json.JSONDecodeError:
                return False
        else:
            return expected == actual


class TestReporter:
    """Generates test reports."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def print_results(self, results: List[TestResult]):
        """Print test results to console."""
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        print("\n" + "="*70)
        print("TEST RESULTS")
        print("="*70)
        
        for result in results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            color = "\033[92m" if result.passed else "\033[91m"
            reset = "\033[0m"
            
            print(f"\n{color}{status}{reset} {result.test_case.name}")
            
            if self.verbose or not result.passed:
                print(f"  File: {result.test_case.file_path}")
                print(f"  Time: {result.execution_time:.3f}s")
                
                if result.test_case.description:
                    print(f"  Description: {result.test_case.description}")
                
                if not result.passed:
                    print(f"  Expected: {result.test_case.expected_output[:100]}")
                    print(f"  Actual:   {result.actual_output[:100]}")
                    if result.error_message:
                        print(f"  Error: {result.error_message}")
        
        print("\n" + "="*70)
        print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
        print("="*70 + "\n")
        
        return failed == 0


def find_test_files(directory: str, pattern: str = "*.test") -> List[str]:
    """Find all test files in a directory."""
    path = Path(directory)
    return [str(f) for f in path.rglob(pattern)]


def main():
    """Main entry point for the test framework."""
    parser = argparse.ArgumentParser(
        description="File-Based Testing Framework"
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory or file to test (default: current directory)'
    )
    parser.add_argument(
        '-c', '--command',
        default='echo {input}',
        help='Command template to execute (use {input} as placeholder)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '-t', '--tags',
        help='Run only tests with specified tags (comma-separated)'
    )
    parser.add_argument(
        '-p', '--pattern',
        default='*.test',
        help='Test file pattern (default: *.test)'
    )
    
    args = parser.parse_args()
    
    # Find test files
    if os.path.isfile(args.path):
        test_files = [args.path]
    else:
        test_files = find_test_files(args.path, args.pattern)
    
    if not test_files:
        print(f"No test files found matching '{args.pattern}' in '{args.path}'")
        return 1
    
    print(f"Found {len(test_files)} test file(s)")
    
    # Parse tests
    test_parser = TestParser()
    all_tests = []
    
    for test_file in test_files:
        try:
            tests = test_parser.parse_file(test_file)
            all_tests.extend(tests)
        except Exception as e:
            print(f"Error parsing {test_file}: {e}")
    
    # Filter by tags if specified
    if args.tags:
        tag_list = [t.strip() for t in args.tags.split(',')]
        all_tests = [
            t for t in all_tests
            if any(tag in t.tags for tag in tag_list)
        ]
    
    if not all_tests:
        print("No tests found to run")
        return 1
    
    print(f"Running {len(all_tests)} test(s)...\n")
    
    # Run tests
    runner = TestRunner(args.command)
    results = []
    
    for test in all_tests:
        result = runner.run_test(test)
        results.append(result)
    
    # Report results
    reporter = TestReporter(verbose=args.verbose)
    success = reporter.print_results(results)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())


# SAMPLE TEST FILES TO GET STARTED
# Save the following content to separate .test files:

"""
=== sample_math.test ===
### TEST: Addition Test
DESCRIPTION: Test basic addition
TYPE: exact
TAGS: math, basic
INPUT:
2 + 2
EXPECTED:
4

### TEST: Multiplication Test
DESCRIPTION: Test multiplication
TYPE: exact
TAGS: math, basic
INPUT:
5 * 3
EXPECTED:
15

### TEST: Division Test
DESCRIPTION: Test division with decimal result
TYPE: contains
TAGS: math, decimal
INPUT:
10 / 3
EXPECTED:
3.3
"""