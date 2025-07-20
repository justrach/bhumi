#!/usr/bin/env python3
"""
Comprehensive integration tests for all Bhumi providers with optimized MAP-Elites
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from test_utils import (
    TestEnvironment, 
    TestResult, 
    run_comprehensive_test,
    check_performance_optimization
)

class IntegrationTestRunner:
    """Orchestrates comprehensive integration testing"""
    
    def __init__(self):
        TestEnvironment.load_env_file()
        self.available_providers = TestEnvironment.get_available_providers()
        self.all_results = []
        self.start_time = time.time()
    
    def print_banner(self):
        """Print test banner"""
        print("🚀 Bhumi Integration Test Suite")
        print("=" * 50)
        print(f"⚡ Testing optimized MAP-Elites system")
        print(f"🧪 Available providers: {', '.join(self.available_providers)}")
        
        # Show optimization status
        optimization = check_performance_optimization()
        print(f"📊 MAP-Elites optimization: {'✅ ACTIVE' if optimization['optimized'] else '❌ INACTIVE'}")
        if optimization['optimized']:
            print(f"   • Archive: {Path(optimization.get('archive_path', 'unknown')).name}")
            print(f"   • Loading: 3x faster with Satya + orjson")
        print()
    
    def print_provider_summary(self, provider: str, results: List[TestResult]):
        """Print summary for a provider"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        
        print(f"\n📋 {provider.upper()} Summary:")
        print(f"   Tests: {passed_tests}/{total_tests} passed")
        
        # Group by test type
        test_types = {}
        for result in results:
            if result.test_name not in test_types:
                test_types[result.test_name] = []
            test_types[result.test_name].append(result)
        
        for test_type, type_results in test_types.items():
            type_passed = sum(1 for r in type_results if r.success)
            type_total = len(type_results)
            status = "✅" if type_passed == type_total else "❌" if type_passed == 0 else "⚠️"
            print(f"   {status} {test_type}: {type_passed}/{type_total}")
            
            # Show details for failed tests
            for result in type_results:
                if not result.success:
                    model = result.details.get('model', 'unknown')
                    print(f"     └─ {model}: {result.message}")
    
    def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON report for CI systems"""
        report = {
            "timestamp": time.time(),
            "duration": time.time() - self.start_time,
            "providers_tested": len(self.available_providers),
            "total_tests": len(self.all_results),
            "passed_tests": sum(1 for r in self.all_results if r.success),
            "optimization_active": check_performance_optimization()["optimized"],
            "providers": {}
        }
        
        # Group results by provider
        for result in self.all_results:
            provider = result.provider
            if provider not in report["providers"]:
                report["providers"][provider] = {
                    "tests": [],
                    "total": 0,
                    "passed": 0
                }
            
            report["providers"][provider]["tests"].append({
                "name": result.test_name,
                "success": result.success,
                "message": result.message,
                "duration": result.duration,
                "model": result.details.get("model", "unknown")
            })
            
            report["providers"][provider]["total"] += 1
            if result.success:
                report["providers"][provider]["passed"] += 1
        
        return report
    
    def print_final_summary(self):
        """Print final test summary"""
        total_tests = len(self.all_results)
        passed_tests = sum(1 for r in self.all_results if r.success)
        total_duration = time.time() - self.start_time
        
        print(f"\n" + "=" * 50)
        print(f"🏁 Test Suite Complete")
        print(f"⏱️  Duration: {total_duration:.2f}s")
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed")
        print(f"🎯 Success rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"🎉 ALL TESTS PASSED! 🎉")
            print(f"✅ Bhumi integration fully working with optimized MAP-Elites")
        else:
            failed_tests = total_tests - passed_tests
            print(f"⚠️  {failed_tests} tests failed")
            
            # Show failed provider summary
            failed_by_provider = {}
            for result in self.all_results:
                if not result.success:
                    provider = result.provider
                    if provider not in failed_by_provider:
                        failed_by_provider[provider] = 0
                    failed_by_provider[provider] += 1
            
            for provider, count in failed_by_provider.items():
                print(f"   • {provider}: {count} failures")
    
    async def run_all_tests(self) -> bool:
        """Run tests for all available providers"""
        if not self.available_providers:
            print("❌ No API keys found! Please set environment variables.")
            print("📝 Copy env.example to .env and add your API keys")
            return False
        
        self.print_banner()
        
        # Test each provider
        for provider in self.available_providers:
            print(f"🧪 Testing {provider.upper()}...")
            
            try:
                results = await run_comprehensive_test(provider)
                self.all_results.extend(results)
                self.print_provider_summary(provider, results)
                
            except Exception as e:
                print(f"💥 {provider.upper()} test suite failed: {e}")
                # Add failure result
                self.all_results.append(TestResult(
                    provider=provider,
                    test_name="provider_suite",
                    success=False,
                    message=f"Test suite failed: {e}",
                    duration=0.0,
                    details={"error": str(e)}
                ))
            
            # Delay between providers
            await asyncio.sleep(2)
        
        self.print_final_summary()
        
        # Save JSON report
        report = self.generate_json_report()
        report_path = Path("test_results.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Detailed report saved to {report_path}")
        
        # Return success status
        total_tests = len(self.all_results)
        passed_tests = sum(1 for r in self.all_results if r.success)
        return passed_tests == total_tests

async def main():
    """Main test function"""
    runner = IntegrationTestRunner()
    
    try:
        success = await runner.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 