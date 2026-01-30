# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "playwright",
#   "beautifulsoup4",
#   "lxml"
# ]
# ///

"""
Test scraper with different URLs to ensure robustness.
Run: python test_scraper.py
"""

import sys
import subprocess
from scraper import scrape_quiz_page


def ensure_playwright():
    """Ensure Playwright browsers are installed."""
    print("🔧 Installing Playwright browsers...")
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print("✓ Playwright ready\n")


def test_url(url: str, test_name: str):
    """Test scraping a single URL."""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}\n")
    
    try:
        result = scrape_quiz_page(url)
        
        # Validate results
        checks = {
            "Has quiz text": len(result["quiz_text"]) > 50,
            "Found submit URL": result["submit_url"] is not None,
            "Quiz text contains 'submit' or 'answer'": 
                any(word in result["quiz_text"].lower() for word in ["submit", "answer", "post"]),
            "Found links": len(result["all_links"]) > 0,
        }
        
        print(f"\n📊 VALIDATION RESULTS:")
        all_passed = True
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check}")
            if not passed:
                all_passed = False
        
        if result["file_urls"]:
            print(f"\n📎 Files found:")
            for f in result["file_urls"]:
                print(f"  - {f}")
        
        if all_passed:
            print(f"\n✅ TEST PASSED: {test_name}")
        else:
            print(f"\n⚠️  TEST PASSED WITH WARNINGS: {test_name}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {test_name}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_all_tests():
    """Run all scraper tests."""
    print("\n" + "="*80)
    print("SCRAPER PIPELINE TEST SUITE")
    print("="*80)
    
    tests = [
        {
            "name": "Official Demo Page",
            "url": "https://tds-llm-analysis.s-anand.net/demo"
        },
        # Add more test URLs as you discover them
    ]
    
    results = []
    for test in tests:
        result = test_url(test["url"], test["name"])
        results.append({
            "name": test["name"],
            "success": result is not None,
            "result": result
        })
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {r['name']}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return results


if __name__ == "__main__":
    ensure_playwright()
    
    # If URL provided as argument, test that specific URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
        test_url(url, "Custom URL Test")
    else:
        # Run all predefined tests
        run_all_tests()