#!/usr/bin/env python3
"""
Wildlife Conservation Backend Test Script
Run this script to test your FastAPI backend setup
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

async def test_endpoint(client: httpx.AsyncClient, endpoint: str, method: str = "GET", data: dict = None) -> Dict[str, Any]:
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        print(f"🔍 Testing {method} {endpoint}...")
        
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        result = {
            "endpoint": endpoint,
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
            "response_time": response.elapsed.total_seconds(),
        }
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
        
        if result["success"]:
            print(f"   ✅ {response.status_code} - OK")
        else:
            print(f"   ❌ {response.status_code} - ERROR")
            print(f"   Response: {result['response']}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ FAILED - {str(e)}")
        return {
            "endpoint": endpoint,
            "success": False,
            "error": str(e)
        }

async def main():
    """Main test function"""
    print("🦁 Wildlife Conservation Backend Test Suite")
    print("=" * 60)
    
    test_results = []
    
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
        # Test basic endpoints
        basic_tests = [
            "/",
            "/health",
            "/api/v1/health/",
            "/api/v1/health/database",
            "/api/v1/health/kobo",
        ]
        
        print("\n📋 Testing Basic Endpoints...")
        print("-" * 40)
        
        for endpoint in basic_tests:
            result = await test_endpoint(client, endpoint)
            test_results.append(result)
        
        # Test API endpoints
        api_tests = [
            "/api/v1/forms/",
        ]
        
        print("\n📋 Testing API Endpoints...")
        print("-" * 40)
        
        for endpoint in api_tests:
            result = await test_endpoint(client, endpoint)
            test_results.append(result)
        
        # Test API documentation
        print("\n📋 Testing API Documentation...")
        print("-" * 40)
        
        doc_result = await test_endpoint(client, "/docs")
        test_results.append(doc_result)
        
        openapi_result = await test_endpoint(client, "/openapi.json")
        test_results.append(openapi_result)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in test_results if r.get("success", False)]
    failed_tests = [r for r in test_results if not r.get("success", False)]
    
    print(f"✅ Successful: {len(successful_tests)}")
    print(f"❌ Failed: {len(failed_tests)}")
    print(f"📈 Success Rate: {len(successful_tests) / len(test_results) * 100:.1f}%")
    
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"   - {test['endpoint']}: {test.get('error', 'Unknown error')}")
    
    # Detailed results
    if successful_tests:
        print("\n✅ SUCCESSFUL TESTS:")
        for test in successful_tests:
            response_info = ""
            if isinstance(test.get("response"), dict):
                if "status" in test["response"]:
                    response_info = f"(Status: {test['response']['status']})"
                elif "forms" in test["response"]:
                    form_count = test["response"].get("count", 0)
                    response_info = f"({form_count} forms found)"
            
            print(f"   - {test['endpoint']}: {test['status_code']} {response_info}")
    
    # Configuration check
    print("\n🔧 CONFIGURATION CHECK:")
    print("-" * 30)
    
    try:
        from app.config import settings
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ Debug Mode: {settings.debug}")
        print(f"✅ Database URL: {'Set' if settings.database_url else 'Not set'}")
        print(f"✅ Kobo API Token: {'Set' if settings.kobo_api_token else 'Not set'}")
        print(f"✅ Secret Key: {'Set' if settings.secret_key else 'Not set'}")
        print(f"✅ Kobo Server: {settings.kobo_server_url}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 30)
    
    if len(successful_tests) == len(test_results):
        print("🎉 All tests passed! Your backend is ready.")
        print("📱 Next steps:")
        print("   1. Create test forms in Kobo Toolbox")
        print("   2. Test form fetching through the API")
        print("   3. Start building your frontend")
        print("   4. Test end-to-end data flow")
    else:
        print("🔧 Some tests failed. Please check:")
        print("   1. Ensure the FastAPI server is running (uvicorn app.main:app --reload)")
        print("   2. Check your .env file configuration")
        print("   3. Verify database and Kobo API credentials")
        print("   4. Check the error messages above")
    
    # API Examples
    print("\n📖 API USAGE EXAMPLES:")
    print("-" * 30)
    print("# Get all forms:")
    print("curl http://localhost:8000/api/v1/forms/")
    print()
    print("# Get specific form:")
    print("curl http://localhost:8000/api/v1/forms/{form_id}")
    print()
    print("# Check health:")
    print("curl http://localhost:8000/health")
    print()
    print("# Interactive docs:")
    print("http://localhost:8000/docs")

if __name__ == "__main__":
    print("Starting backend tests...")
    print("Make sure your FastAPI server is running:")
    print("uvicorn app.main:app --reload")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if the server is running: http://localhost:8000")
        print("2. Verify your conda environment is activated")
        print("3. Check your .env file configuration")
        print("4. Review server logs for errors")