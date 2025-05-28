#!/usr/bin/env python3
"""
Test runner with optimized configuration for AI Game Master.

This script provides convenient commands for running tests with proper configuration
to avoid slow RAG/embeddings initialization.

Usage:
    # Run all tests (fast mode with RAG disabled)
    python tests/run_all_tests.py
    
    # Run only unit tests
    python tests/run_all_tests.py unit
    
    # Run only integration tests  
    python tests/run_all_tests.py integration
    
    # Run with coverage
    python tests/run_all_tests.py coverage
    
    # Run tests with RAG enabled (slower, for testing RAG functionality)
    python tests/run_all_tests.py --with-rag
"""
import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_command(cmd, env=None):
    """Run a command and return its exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    return result.returncode


def get_test_env(with_rag=False):
    """Get environment variables for testing."""
    env = os.environ.copy()
    # Disable RAG by default for faster tests
    if not with_rag:
        env['RAG_ENABLED'] = 'false'
    env['TTS_PROVIDER'] = 'disabled'
    env['GAME_STATE_REPO_TYPE'] = 'memory'
    return env


def run_all_tests(with_rag=False):
    """Run all tests."""
    env = get_test_env(with_rag)
    cmd = ['python', '-m', 'pytest', 'tests/', '-v']
    return run_command(cmd, env)


def run_unit_tests(with_rag=False):
    """Run only unit tests."""
    env = get_test_env(with_rag)
    cmd = ['python', '-m', 'pytest', 'tests/unit/', '-v']
    return run_command(cmd, env)


def run_integration_tests(with_rag=False):
    """Run only integration tests."""
    env = get_test_env(with_rag)
    cmd = ['python', '-m', 'pytest', 'tests/integration/', '-v']
    return run_command(cmd, env)


def run_with_coverage():
    """Run tests with coverage report."""
    env = get_test_env(with_rag=False)
    
    # Run tests with coverage
    print("\n=== Running tests with coverage ===")
    cmd = ['coverage', 'run', '-m', 'pytest', 'tests/', '-v']
    result = run_command(cmd, env)
    
    if result == 0:
        # Generate coverage report
        print("\n=== Coverage Report ===")
        run_command(['coverage', 'report', '-m'])
        
        print("\n=== Generating HTML coverage report ===")
        run_command(['coverage', 'html'])
        print("HTML coverage report generated in htmlcov/")
    
    return result


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run AI Game Master tests with optimized configuration'
    )
    parser.add_argument(
        'test_type',
        nargs='?',
        choices=['all', 'unit', 'integration', 'coverage'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    parser.add_argument(
        '--with-rag',
        action='store_true',
        help='Enable RAG system for tests (slower but tests RAG functionality)'
    )
    
    args = parser.parse_args()
    
    # Print configuration
    print(f"\n{'='*60}")
    print("AI Game Master Test Runner")
    print(f"{'='*60}")
    print(f"Test type: {args.test_type}")
    print(f"RAG enabled: {args.with_rag}")
    print(f"{'='*60}\n")
    
    # Run appropriate tests
    if args.test_type == 'unit':
        result = run_unit_tests(args.with_rag)
    elif args.test_type == 'integration':
        result = run_integration_tests(args.with_rag)
    elif args.test_type == 'coverage':
        if args.with_rag:
            print("Warning: Coverage runs with RAG disabled for speed")
        result = run_with_coverage()
    else:  # 'all' or default
        result = run_all_tests(args.with_rag)
    
    sys.exit(result)


if __name__ == '__main__':
    main()