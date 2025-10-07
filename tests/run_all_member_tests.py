"""
MASTER TEST RUNNER - ALL MEMBER COMPONENTS
Runs all unit tests for all 4 members' components and provides comprehensive report.
"""

import sys
import os
import unittest
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import test modules
from test_member1_failover import TestFailoverComponent
from test_member2_storage import TestMessageStorageComponent
from test_member3_timesync import TestTimeSyncComponent
from test_member4_consensus import TestConsensusComponent


def print_header(text, width=80):
    """Print a formatted header"""
    print()
    print("=" * width)
    print(text.center(width))
    print("=" * width)
    print()


def run_all_tests():
    """Run all member tests and generate comprehensive report"""
    
    print_header("DISTRIBUTED MESSAGING SYSTEM - COMPLETE TEST SUITE")
    print("Testing all 4 member components with mocked dependencies")
    print("Each member can run their tests independently to verify their work")
    print()
    
    # Test configuration
    test_suites = [
        ("MEMBER 1: Failover & Recovery", TestFailoverComponent),
        ("MEMBER 2: Message Storage & Replication", TestMessageStorageComponent),
        ("MEMBER 3: Time Synchronization", TestTimeSyncComponent),
        ("MEMBER 4: Consensus & Leader Election", TestConsensusComponent)
    ]
    
    all_results = []
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    
    # Run each member's test suite
    for member_name, test_class in test_suites:
        print_header(member_name, width=80)
        
        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        # Run tests with detailed output
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Collect statistics
        tests_run = result.testsRun
        passed = tests_run - len(result.failures) - len(result.errors)
        failed = len(result.failures)
        errors = len(result.errors)
        
        total_tests += tests_run
        total_passed += passed
        total_failed += failed
        total_errors += errors
        
        all_results.append({
            'member': member_name,
            'tests': tests_run,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'success': result.wasSuccessful()
        })
        
        # Print individual summary
        print()
        print("-" * 80)
        print(f"SUMMARY - {member_name}")
        print(f"  Tests Run: {tests_run}")
        print(f"  ✓ Passed: {passed}")
        if failed > 0:
            print(f"  ✗ Failed: {failed}")
        if errors > 0:
            print(f"  ✗ Errors: {errors}")
        print(f"  Status: {'SUCCESS ✓' if result.wasSuccessful() else 'FAILED ✗'}")
        print("-" * 80)
        print()
    
    # Print comprehensive final report
    print_header("COMPREHENSIVE TEST REPORT", width=80)
    
    print("┌" + "─" * 78 + "┐")
    print("│" + " COMPONENT TEST RESULTS".center(78) + "│")
    print("├" + "─" * 40 + "┬" + "─" * 9 + "┬" + "─" * 9 + "┬" + "─" * 9 + "┬" + "─" * 9 + "┤")
    print("│" + " Component".ljust(40) + "│" + " Tests".center(9) + "│" + " Passed".center(9) + "│" + " Failed".center(9) + "│" + " Status".center(9) + "│")
    print("├" + "─" * 40 + "┼" + "─" * 9 + "┼" + "─" * 9 + "┼" + "─" * 9 + "┼" + "─" * 9 + "┤")
    
    for result in all_results:
        member = result['member'][:38]
        tests = str(result['tests'])
        passed = str(result['passed'])
        failed = str(result['failed'] + result['errors'])
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        
        print("│ " + member.ljust(39) + "│" + tests.center(9) + "│" + passed.center(9) + "│" + failed.center(9) + "│" + status.center(9) + "│")
    
    print("├" + "─" * 40 + "┼" + "─" * 9 + "┼" + "─" * 9 + "┼" + "─" * 9 + "┼" + "─" * 9 + "┤")
    print("│" + " TOTAL".ljust(40) + "│" + str(total_tests).center(9) + "│" + str(total_passed).center(9) + "│" + str(total_failed + total_errors).center(9) + "│" + ("✓ PASS" if all(r['success'] for r in all_results) else "✗ FAIL").center(9) + "│")
    print("└" + "─" * 40 + "┴" + "─" * 9 + "┴" + "─" * 9 + "┴" + "─" * 9 + "┴" + "─" * 9 + "┘")
    
    print()
    print("OVERALL STATISTICS:")
    print(f"  Total Tests Run: {total_tests}")
    print(f"  ✓ Total Passed: {total_passed} ({100 * total_passed // total_tests if total_tests > 0 else 0}%)")
    print(f"  ✗ Total Failed: {total_failed + total_errors}")
    print()
    
    if all(r['success'] for r in all_results):
        print("🎉 ALL TESTS PASSED! All components are working correctly!")
        print()
        print("✓ Each member's component is independently verified")
        print("✓ All dependencies properly mocked for isolated testing")
        print("✓ Thread-safety verified for all components")
        print("✓ Ready for integration testing")
    else:
        print("⚠️  SOME TESTS FAILED - Review failures above")
        failed_members = [r['member'] for r in all_results if not r['success']]
        print(f"   Failed components: {', '.join(failed_members)}")
    
    print()
    print("=" * 80)
    print("INDIVIDUAL TEST INSTRUCTIONS FOR TEAM MEMBERS:")
    print("=" * 80)
    print()
    print("Member 1 (Failover): python tests/test_member1_failover.py")
    print("Member 2 (Storage):  python tests/test_member2_storage.py")
    print("Member 3 (TimeSync): python tests/test_member3_timesync.py")
    print("Member 4 (Consensus): python tests/test_member4_consensus.py")
    print()
    print("Each member should run their test file to verify their component works!")
    print("=" * 80)
    
    return all(r['success'] for r in all_results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
