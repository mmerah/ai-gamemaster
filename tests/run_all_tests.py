"""
Test runner for all tests in the reorganized test structure.

Usage:
    python -m tests.run_all_tests
    or
    cd tests && python run_all_tests.py
"""
import unittest
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def discover_and_run_tests():
    """Discover and run all tests in the test directories."""
    
    # Get the tests directory
    tests_dir = os.path.dirname(__file__)
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add unit tests
    unit_tests = loader.discover(
        start_dir=os.path.join(tests_dir, 'unit'),
        pattern='test_*.py',
        top_level_dir=tests_dir
    )
    suite.addTests(unit_tests)
    
    # Add integration tests
    integration_tests = loader.discover(
        start_dir=os.path.join(tests_dir, 'integration'),
        pattern='test_*.py',
        top_level_dir=tests_dir
    )
    suite.addTests(integration_tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_unit_tests_only():
    """Run only unit tests."""
    tests_dir = os.path.dirname(__file__)
    loader = unittest.TestLoader()
    
    unit_tests = loader.discover(
        start_dir=os.path.join(tests_dir, 'unit'),
        pattern='test_*.py',
        top_level_dir=tests_dir
    )
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unit_tests)
    
    return result.wasSuccessful()


def run_integration_tests_only():
    """Run only integration tests."""
    tests_dir = os.path.dirname(__file__)
    loader = unittest.TestLoader()
    
    integration_tests = loader.discover(
        start_dir=os.path.join(tests_dir, 'integration'),
        pattern='test_*.py',
        top_level_dir=tests_dir
    )
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(integration_tests)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == 'unit':
            success = run_unit_tests_only()
        elif test_type == 'integration':
            success = run_integration_tests_only()
        else:
            print(f"Unknown test type: {test_type}")
            print("Usage: python run_all_tests.py [unit|integration]")
            sys.exit(1)
    else:
        success = discover_and_run_tests()
    
    sys.exit(0 if success else 1)
