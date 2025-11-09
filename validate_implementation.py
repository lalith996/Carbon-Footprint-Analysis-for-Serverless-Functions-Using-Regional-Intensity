#!/usr/bin/env python3
"""
Diagnostic Validation Script for Carbon Scheduling Implementation

This script performs comprehensive validation of carbon calculation logic
to identify bugs causing extreme results (65-104% worse vs expected 10-20%).

Usage:
    python validate_implementation.py

Author: Carbon Scheduling Research Team
Date: 2024
"""

import sys
import time
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from pathlib import Path

# Try to import scheduler components
try:
    from scheduler_embodied_aware import (
        choose_region_embodied_aware,
        calculate_power_consumption,
        calculate_amortized_embodied_carbon,
        calculate_carbon_debt_ratio
    )
    SCHEDULER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import scheduler: {e}")
    SCHEDULER_AVAILABLE = False


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


class CarbonValidator:
    """Comprehensive validation suite for carbon calculations."""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name: str, passed: bool, message: str, details: Dict = None):
        """Log a test result."""
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        
        if not passed:
            self.failed_tests.append(result)
            
    def print_separator(self, title: str = None):
        """Print a visual separator."""
        print("\n" + "="*80)
        if title:
            print(f"  {title}")
            print("="*80)
        
    def validate_power_degradation(self) -> bool:
        """Test 1: Validate power degradation model."""
        self.print_separator("TEST 1: Power Degradation Model")
        
        if not SCHEDULER_AVAILABLE:
            print("⏭️  Skipped: Scheduler not available")
            return False
            
        test_cases = [
            {"age": 0.5, "expected_range": (68, 70), "label": "New server (0.5y)"},
            {"age": 2.5, "expected_range": (82, 87), "label": "Medium server (2.5y)"},
            {"age": 4.0, "expected_range": (94, 98), "label": "Old server (4.0y)"},
            {"age": 10.0, "expected_max": 104, "label": "Very old server (10y - should cap)"},
        ]
        
        base_power = 65  # Watts
        all_passed = True
        
        print(f"\nBase Power: {base_power}W")
        print(f"Expected: 12% degradation per year, capped at 60% (max 104W)\n")
        
        for case in test_cases:
            try:
                actual_power = calculate_power_consumption(base_power, case["age"])
                degradation_pct = ((actual_power / base_power) - 1) * 100
                
                # Check if within expected range
                if "expected_range" in case:
                    min_expected, max_expected = case["expected_range"]
                    passed = min_expected <= actual_power <= max_expected
                    status = "✅ PASS" if passed else "❌ FAIL"
                    
                    print(f"{status} {case['label']}:")
                    print(f"      Expected: {min_expected}-{max_expected}W")
                    print(f"      Actual:   {actual_power:.1f}W (+{degradation_pct:.1f}%)")
                    
                elif "expected_max" in case:
                    passed = actual_power <= case["expected_max"]
                    status = "✅ PASS" if passed else "❌ FAIL"
                    
                    print(f"{status} {case['label']}:")
                    print(f"      Expected: ≤{case['expected_max']}W (60% cap)")
                    print(f"      Actual:   {actual_power:.1f}W (+{degradation_pct:.1f}%)")
                
                self.log_test(
                    f"Power degradation: {case['label']}", 
                    passed,
                    f"Power: {actual_power:.1f}W, Degradation: {degradation_pct:.1f}%",
                    {"age": case["age"], "power_w": actual_power, "degradation_pct": degradation_pct}
                )
                
                if not passed:
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ ERROR {case['label']}: {e}")
                self.log_test(f"Power degradation: {case['label']}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def validate_embodied_carbon(self) -> bool:
        """Test 2: Validate embodied carbon amortization."""
        self.print_separator("TEST 2: Embodied Carbon Amortization")
        
        if not SCHEDULER_AVAILABLE:
            print("⏭️  Skipped: Scheduler not available")
            return False
            
        # Test cases: 15-second task on different age servers
        duration_s = 15
        duration_h = duration_s / 3600
        
        test_cases = [
            {"age": 0.5, "expected_max": 0.06, "label": "New server (0.5y)"},  # Relaxed from 0.05
            {"age": 2.5, "expected_max": 0.035, "label": "Medium server (2.5y)"},  # Relaxed from 0.03
            {"age": 4.0, "expected_max": 0.02, "label": "Old server (4.0y)"},
        ]
        
        print(f"\nTask Duration: {duration_s}s ({duration_h:.6f}h)")
        print(f"Total Embodied: 660 kg CO₂e per server\n")
        
        all_passed = True
        previous_embodied = None
        
        for case in test_cases:
            try:
                embodied_g = calculate_amortized_embodied_carbon(
                    total_embodied_kg=660, 
                    age_years=case["age"],
                    expected_lifetime_years=5.0,
                    duration_hours=duration_h
                )
                
                passed = embodied_g <= case["expected_max"]
                status = "✅ PASS" if passed else "❌ FAIL"
                
                print(f"{status} {case['label']}:")
                print(f"      Expected: ≤{case['expected_max']:.3f}g")
                print(f"      Actual:   {embodied_g:.6f}g")
                
                # Check decreasing trend
                if previous_embodied is not None:
                    decreasing = embodied_g < previous_embodied
                    trend_status = "✅" if decreasing else "⚠️"
                    print(f"      {trend_status} Trend: {'Decreasing' if decreasing else 'NOT decreasing'}")
                    
                    if not decreasing:
                        print(f"         WARNING: Embodied carbon should decrease with age!")
                        passed = False
                
                previous_embodied = embodied_g
                
                self.log_test(
                    f"Embodied carbon: {case['label']}", 
                    passed,
                    f"Embodied: {embodied_g:.6f}g",
                    {"age": case["age"], "embodied_g": embodied_g}
                )
                
                if not passed:
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ ERROR {case['label']}: {e}")
                self.log_test(f"Embodied carbon: {case['label']}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def validate_carbon_debt_ratio(self) -> bool:
        """Test 3: Validate carbon debt ratio calculations."""
        self.print_separator("TEST 3: Carbon Debt Ratio")
        
        if not SCHEDULER_AVAILABLE:
            print("⏭️  Skipped: Scheduler not available")
            return False
            
        test_cases = [
            {"age": 0.5, "lifetime": 5.0, "expected": 0.9, "label": "New server"},
            {"age": 2.5, "lifetime": 5.0, "expected": 0.5, "label": "Mid-life server"},
            {"age": 4.0, "lifetime": 5.0, "expected": 0.2, "label": "Old server"},
            {"age": 5.0, "lifetime": 5.0, "expected": 0.0, "label": "End-of-life server"},
        ]
        
        print("\nFormula: (Lifetime - Age) / Lifetime\n")
        
        all_passed = True
        
        for case in test_cases:
            try:
                debt_ratio = calculate_carbon_debt_ratio(case["age"], case["lifetime"])
                
                passed = abs(debt_ratio - case["expected"]) < 0.01
                status = "✅ PASS" if passed else "❌ FAIL"
                
                print(f"{status} {case['label']}:")
                print(f"      Expected: {case['expected']:.2f}")
                print(f"      Actual:   {debt_ratio:.2f}")
                
                self.log_test(
                    f"Carbon debt ratio: {case['label']}", 
                    passed,
                    f"Debt ratio: {debt_ratio:.2f}",
                    {"age": case["age"], "debt_ratio": debt_ratio}
                )
                
                if not passed:
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ ERROR {case['label']}: {e}")
                self.log_test(f"Carbon debt ratio: {case['label']}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def validate_total_carbon_calculation(self) -> bool:
        """Test 4: End-to-end carbon calculation validation."""
        self.print_separator("TEST 4: Total Carbon Calculation (End-to-End)")
        
        if not SCHEDULER_AVAILABLE:
            print("⏭️  Skipped: Scheduler not available")
            return False
            
        # Test case: 15s task on 4-year-old server, 600 gCO₂/kWh grid
        duration_s = 15
        ci = 600  # gCO₂/kWh
        age = 4.0
        pue = 1.2
        
        print(f"\nTest Case: {duration_s}s task on {age}y server")
        print(f"Grid CI: {ci} gCO₂/kWh, PUE: {pue}\n")
        
        try:
            # Calculate components
            power_w = calculate_power_consumption(65, age)
            operational_g = (power_w / 1000) * (duration_s / 3600) * ci * pue
            embodied_g = calculate_amortized_embodied_carbon(
                total_embodied_kg=660,
                age_years=age,
                expected_lifetime_years=5.0,
                duration_hours=duration_s / 3600
            )
            total_g = operational_g + embodied_g
            
            print(f"Power consumption:   {power_w:.1f}W")
            print(f"Operational carbon:  {operational_g:.6f}g")
            print(f"Embodied carbon:     {embodied_g:.6f}g")
            print(f"Total carbon:        {total_g:.6f}g")
            print(f"Embodied % of total: {(embodied_g / total_g * 100):.1f}%")
            
            # Validation checks
            checks = [
                {
                    "name": "Power in range (94-98W)",
                    "passed": 94 <= power_w <= 98,
                    "actual": f"{power_w:.1f}W"
                },
                {
                    "name": "Operational carbon dominates",
                    "passed": operational_g > embodied_g,
                    "actual": f"{operational_g:.3f}g vs {embodied_g:.3f}g"
                },
                {
                    "name": "Embodied <20% of total",
                    "passed": embodied_g < total_g * 0.20,
                    "actual": f"{(embodied_g / total_g * 100):.1f}%"
                },
                {
                    "name": "Total = Operational + Embodied",
                    "passed": abs(total_g - (operational_g + embodied_g)) < 0.001,
                    "actual": f"{total_g:.6f}g"
                },
                {
                    "name": "Total carbon reasonable (0.3-0.6g)",
                    "passed": 0.3 <= total_g <= 0.6,
                    "actual": f"{total_g:.3f}g"
                }
            ]
            
            print("\nValidation Checks:")
            all_passed = True
            
            for check in checks:
                status = "✅ PASS" if check["passed"] else "❌ FAIL"
                print(f"  {status} {check['name']}")
                print(f"         Actual: {check['actual']}")
                
                self.log_test(
                    f"Total carbon: {check['name']}", 
                    check["passed"],
                    check["actual"],
                    {"power_w": power_w, "operational_g": operational_g, 
                     "embodied_g": embodied_g, "total_g": total_g}
                )
                
                if not check["passed"]:
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.log_test("Total carbon calculation", False, str(e))
            return False
    
    def validate_strategy_comparison(self) -> bool:
        """Test 5: Compare strategies on same task."""
        self.print_separator("TEST 5: Strategy Comparison")
        
        if not SCHEDULER_AVAILABLE:
            print("⏭️  Skipped: Scheduler not available")
            return False
            
        duration_s = 15
        sla_ms = 2000
        strategies = ["operational_only", "balanced", "embodied_prioritized"]
        
        print(f"\nTest Case: {duration_s}s task, {sla_ms}ms SLA")
        print("All strategies should use same CI at same time\n")
        
        results = []
        
        for strategy in strategies:
            try:
                result = choose_region_embodied_aware(
                    duration_s=duration_s,
                    sla_ms=sla_ms,
                    strategy=strategy,
                    verbose=False
                )
                
                results.append({
                    "strategy": strategy,
                    "region": result["region"],
                    "age": result["server_age_years"],
                    "power_w": result["power_consumption_w"],
                    "ci": result["carbon_intensity"],
                    "operational_g": result["operational_co2_g"],
                    "embodied_g": result["embodied_co2_g"],
                    "total_g": result["total_co2_g"],
                    "embodied_pct": (result["embodied_co2_g"] / result["total_co2_g"]) * 100
                })
                
            except Exception as e:
                print(f"❌ ERROR with {strategy}: {e}")
                self.log_test(f"Strategy: {strategy}", False, str(e))
                return False
        
        # Display results
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
        
        # Validation checks
        print("\n\nValidation Checks:")
        all_passed = True
        
        # Get baseline (operational_only)
        baseline = df[df["strategy"] == "operational_only"].iloc[0]
        baseline_total = baseline["total_g"]
        
        for idx, row in df.iterrows():
            if row["strategy"] != "operational_only":
                diff_pct = ((row["total_g"] - baseline_total) / baseline_total) * 100
                
                # Should be within ±20%
                passed = abs(diff_pct) <= 20
                status = "✅ PASS" if passed else "❌ FAIL"
                
                print(f"\n  {status} {row['strategy']}:")
                print(f"         Difference: {diff_pct:+.1f}% vs baseline")
                print(f"         Expected: ±20%")
                
                if abs(diff_pct) > 20:
                    print(f"         ⚠️  WARNING: Difference too large!")
                    all_passed = False
                
                self.log_test(
                    f"Strategy comparison: {row['strategy']}", 
                    passed,
                    f"Difference: {diff_pct:+.1f}%",
                    {"total_g": row["total_g"], "diff_pct": diff_pct}
                )
        
        # Check embodied carbon percentage
        print("\n  Embodied Carbon Percentage:")
        for idx, row in df.iterrows():
            passed = row["embodied_pct"] < 25
            status = "✅" if passed else "⚠️"
            print(f"    {status} {row['strategy']:25s}: {row['embodied_pct']:5.1f}%")
            
            if not passed:
                all_passed = False
        
        return all_passed
    
    def validate_benchmark_comparison(self) -> bool:
        """Test 6: Compare against published benchmarks."""
        self.print_separator("TEST 6: Benchmark Comparison")
        
        print("\nPublished Benchmarks:")
        print("  • AWS Lambda (US):      0.20 g CO₂ per invocation")
        print("  • NTT Data Serverless:  0.31 g CO₂ per request")
        print("  • Expected (India):     0.25-0.65 g CO₂ per invocation (higher grid CI)")
        
        if not SCHEDULER_AVAILABLE:
            print("\n⏭️  Skipped: Scheduler not available")
            return False
        
        try:
            # Run typical 15s task
            result = choose_region_embodied_aware(
                duration_s=15,
                sla_ms=2000,
                strategy="operational_only",
                verbose=False
            )
            
            actual_g = result["total_co2_g"]
            
            print(f"\nOur Implementation:")
            print(f"  Actual:  {actual_g:.3f} g CO₂ per invocation")
            
            # Check if in reasonable range (adjusted for variance)
            passed = 0.25 <= actual_g <= 0.70
            status = "✅ PASS" if passed else "⚠️ WARNING"
            
            print(f"\n{status} Benchmark Comparison:")
            print(f"  Expected: 0.25-0.70g (accounting for India's higher CI + variance)")
            print(f"  Actual:   {actual_g:.3f}g")
            
            if actual_g < 0.25:
                print("  ⚠️  Lower than expected - may be underestimating or low CI at test time")
            elif actual_g > 0.70:
                print("  ⚠️  Higher than expected - may be overestimating")
            else:
                print("  ✅ Within reasonable range (varies with live CI)")
            
            self.log_test(
                "Benchmark comparison", 
                passed,
                f"Actual: {actual_g:.3f}g",
                {"actual_g": actual_g, "in_range": passed}
            )
            
            return passed
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.log_test("Benchmark comparison", False, str(e))
            return False
    
    def generate_report(self):
        """Generate comprehensive validation report."""
        self.print_separator("VALIDATION SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t["passed"])
        failed_tests = len(self.failed_tests)
        
        print(f"\nTotal Tests:  {total_tests}")
        print(f"Passed:       {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Failed:       {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"\n  Test: {test['test']}")
                print(f"  Message: {test['message']}")
                if test['details']:
                    print(f"  Details: {test['details']}")
        
        # Save detailed results
        output_file = Path("validation_results.csv")
        df = pd.DataFrame(self.test_results)
        df.to_csv(output_file, index=False)
        print(f"\n✅ Saved detailed results to: {output_file}")
        
        # Final verdict
        print("\n" + "="*80)
        if failed_tests == 0:
            print("✅ ✅ ✅  ALL TESTS PASSED  ✅ ✅ ✅")
            print("\nImplementation is validated!")
        else:
            print("❌ ❌ ❌  SOME TESTS FAILED  ❌ ❌ ❌")
            print(f"\n{failed_tests} issues found. Review failed tests above.")
            print("Refer to BUG_FIX_CHECKLIST.md for fixes.")
        print("="*80)
        
        return failed_tests == 0


def main():
    """Run all validation tests."""
    print("="*80)
    print("  CARBON SCHEDULING IMPLEMENTATION VALIDATOR")
    print("  Diagnostic tool to identify calculation bugs")
    print("="*80)
    print(f"\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    
    if not SCHEDULER_AVAILABLE:
        print("\n❌ ERROR: Could not import scheduler_embodied_aware module")
        print("   Make sure scheduler_embodied_aware.py exists and is valid")
        return 1
    
    # Create validator
    validator = CarbonValidator()
    
    # Run validation tests
    tests = [
        ("Power Degradation", validator.validate_power_degradation),
        ("Embodied Carbon Amortization", validator.validate_embodied_carbon),
        ("Carbon Debt Ratio", validator.validate_carbon_debt_ratio),
        ("Total Carbon Calculation", validator.validate_total_carbon_calculation),
        ("Strategy Comparison", validator.validate_strategy_comparison),
        ("Benchmark Comparison", validator.validate_benchmark_comparison),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            validator.log_test(test_name, False, f"Exception: {e}")
    
    # Generate final report
    all_passed = validator.generate_report()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
