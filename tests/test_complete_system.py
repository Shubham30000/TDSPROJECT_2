#!/usr/bin/env python3
"""
IMPROVED: Better timing and quiz-specific validation
"""

import httpx
import time
import json
import sys

BASE_URL = "http://localhost:7860"
MOCK_SERVER = "http://localhost:8000"

# Expected answers for each quiz
EXPECTED_ANSWERS = {
    "quiz-csv": 2750,
    "quiz-api": 4500,
    "quiz-scrape": "ALPHA123BETA",
    "quiz-viz": lambda x: isinstance(x, str) and x.startswith("data:image/png;base64,"),
    "quiz-chain-1": 30,
    "quiz-chain-2": 100,
}


def wait_for_submission(quiz_url: str, max_wait: int = 30) -> dict | None:
    """Wait for a specific quiz submission to appear"""
    print(f"⏳ Waiting up to {max_wait}s for submission...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = httpx.get(f"{MOCK_SERVER}/submissions", timeout=5.0)
            submissions = response.json().get("submissions", [])
            
            # Find submission for this quiz
            for sub in reversed(submissions):  # Check most recent first
                if quiz_url in sub.get("url", ""):
                    return sub
            
            time.sleep(1)
        except Exception as e:
            print(f"⚠️  Error checking submissions: {e}")
            time.sleep(1)
    
    return None


def validate_answer(quiz_type: str, actual_answer):
    """Validate if answer matches expected"""
    expected = EXPECTED_ANSWERS.get(quiz_type)
    
    if expected is None:
        return True, "No validation rule"
    
    if callable(expected):
        # Custom validation function
        if expected(actual_answer):
            return True, "Custom validation passed"
        return False, "Custom validation failed"
    
    # Direct comparison
    if actual_answer == expected or str(actual_answer) == str(expected):
        return True, f"Match: {expected}"
    
    return False, f"Expected {expected}, got {actual_answer}"


def test_quiz(quiz_name: str, quiz_url: str, wait_time: int = 30):
    """Test a single quiz with proper validation"""
    print(f"\n{'='*70}")
    print(f"🧪 TESTING: {quiz_name}")
    print(f"{'='*70}\n")
    
    # Extract quiz type from URL
    quiz_type = quiz_url.split("/")[-1]
    
    payload = {
        "email": "test@mail.com",
        "secret": "something_random_12345",
        "url": quiz_url
    }
    
    try:
        print(f"📤 Sending request to {BASE_URL}/receive_request")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = httpx.post(
            f"{BASE_URL}/receive_request",
            json=payload,
            timeout=30.0
        )
        
        print(f"📥 Response: {response.status_code}")
        print(f"📄 Body: {response.json()}")
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            return False
        
        print("✅ Request accepted!")
        
        # Wait for submission
        submission = wait_for_submission(quiz_url, max_wait=wait_time)
        
        if not submission:
            print(f"❌ No submission found after {wait_time}s")
            return False
        
        print(f"\n📊 Submission received:")
        print(f"   URL: {submission.get('url')}")
        print(f"   Answer: {submission.get('answer')}")
        
        # Validate answer
        is_valid, message = validate_answer(quiz_type, submission.get('answer'))
        
        if is_valid:
            print(f"✅ PASS: {message}")
            return True
        else:
            print(f"❌ FAIL: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Test exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all quiz tests with proper sequencing"""
    print("\n" + "="*70)
    print("🚀 COMPREHENSIVE QUIZ SOLVER TESTS - IMPROVED")
    print("="*70)
    
    # Check servers
    print("\n🔍 Checking servers...")
    
    try:
        httpx.get(f"{BASE_URL}/", timeout=5.0)
        print(f"✅ Main server: {BASE_URL}")
    except:
        print(f"❌ Main server not running")
        print("   Start: python receive_request_enhanced.py")
        return
    
    try:
        httpx.get(f"{MOCK_SERVER}/", timeout=5.0)
        print(f"✅ Mock server: {MOCK_SERVER}")
    except:
        print(f"❌ Mock server not running")
        print("   Start: python mock_quiz_server_complete.py")
        return
    
    # Reset
    print("\n🔄 Resetting submissions...")
    try:
        httpx.get(f"{MOCK_SERVER}/reset", timeout=5.0)
        print("✅ Reset complete")
    except:
        print("⚠️  Reset failed")
    
    # Define tests
    tests = [
        ("CSV Analysis", f"{MOCK_SERVER}/quiz-csv", 30),
        ("API Data", f"{MOCK_SERVER}/quiz-api", 20),
        ("Web Scraping", f"{MOCK_SERVER}/quiz-scrape", 20),
        ("Visualization", f"{MOCK_SERVER}/quiz-viz", 30),
        ("Multi-Step Chain", f"{MOCK_SERVER}/quiz-chain-1", 40),
    ]
    
    results = []
    
    for test_name, test_url, wait_time in tests:
        success = test_quiz(test_name, test_url, wait_time)
        results.append((test_name, success))
        time.sleep(3)  # Pause between tests
    
    # Summary
    print("\n" + "="*70)
    print("📊 FINAL RESULTS")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n✓ Passed: {passed}/{total}")
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ System working perfectly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("💡 Check server logs for details")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        quiz_name = sys.argv[1]
        quiz_url = f"{MOCK_SERVER}/quiz-{quiz_name}"
        test_quiz(quiz_name.upper(), quiz_url, wait_time=30)
    else:
        run_all_tests()