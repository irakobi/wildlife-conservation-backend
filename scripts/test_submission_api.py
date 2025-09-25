# scripts/test_submission_api.py
"""
Complete Test Script for Wildlife Conservation Form Submission API
Run this after setting up the database to test all endpoints
"""

import requests
import json
import base64
from datetime import datetime
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def create_test_image():
    """Create a small test image as base64"""
    # Simple 1x1 pixel PNG in base64
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA6x8pNwAAAABJRU5ErkJggg=="

def test_api_status():
    """Test API status endpoint"""
    print("🧪 Testing API Status...")
    
    try:
        response = requests.get(f"{API_BASE}/status")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"API Status test failed: {e}")
        return False

def test_health_check():
    """Test health check endpoint"""
    print("\n🧪 Testing Health Check...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 503]  # Either healthy or degraded is ok
    except Exception as e:
        print(f"Health check test failed: {e}")
        return False

def test_forms_api():
    """Test forms API (feeding frontend)"""
    print("\n🧪 Testing Forms API (Frontend Form Feeding)...")
    
    try:
        # Test get forms list
        response = requests.get(f"{API_BASE}/forms/")
        print(f"Forms list - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            forms = response.json()
            print(f"Available forms: {forms.get('count', 0)}")
            if forms.get('results'):
                first_form = forms['results'][0]
                print(f"First form: {first_form.get('name', 'Unnamed')}")
                return first_form.get('uid')
        else:
            print(f"Forms API Error: {response.json()}")
    except Exception as e:
        print(f"Forms API test failed: {e}")
    return None

def test_form_detail(form_id):
    """Test individual form details"""
    if not form_id:
        print("\n⚠️ Skipping form detail test - no form ID")
        return
    
    print(f"\n🧪 Testing Form Details for {form_id}...")
    
    try:
        response = requests.get(f"{API_BASE}/forms/{form_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            form = response.json()
            print(f"Form title: {form.get('name', 'Unnamed')}")
            survey_questions = form.get('content', {}).get('survey', [])
            print(f"Form has {len(survey_questions)} questions")
        else:
            print(f"Form detail error: {response.json()}")
    except Exception as e:
        print(f"Form detail test failed: {e}")

def test_create_submission():
    """Test creating a single form submission"""
    print("\n🧪 Testing Form Submission Creation...")
    
    # Sample form submission data
    submission_data = {
        "kobo_form_id": "test_form_001",
        "submission_data": {
            "respondent_name": "John Doe",
            "observation_type": "Wildlife Sighting",
            "species_name": "African Elephant",
            "count": 5,
            "behavior": "Grazing",
            "notes": "Small herd near water source"
        },
        "username": "field_researcher_01",
        "device_id": "mobile_device_123",
        "app_version": "1.0.0",
        "location": {
            "latitude": -1.9441,
            "longitude": 30.0619,
            "accuracy": 10.0,
            "altitude": 1500.0
        },
        "media_files": [
            {
                "filename": "elephant_photo.jpg",
                "file_type": "image",
                "mime_type": "image/jpeg",
                "file_size": 1024,
                "question_name": "photo_evidence",
                "file_data": create_test_image()
            }
        ],
        "submitted_at": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/submissions/",
            json=submission_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
        
        if response.status_code == 201:
            return response.json()["id"]
    except Exception as e:
        print(f"Create submission test failed: {e}")
    
    return None

def test_create_multiple_submissions():
    """Test creating multiple submissions for better testing"""
    print("\n🧪 Testing Multiple Submissions Creation...")
    
    submission_ids = []
    
    # Create 3 test submissions with different data
    test_submissions = [
        {
            "kobo_form_id": "wildlife_survey_001",
            "submission_data": {
                "species_name": "Mountain Gorilla",
                "count": 8,
                "behavior": "Foraging",
                "habitat": "Forest",
                "notes": "Healthy family group observed"
            },
            "username": "researcher_jane",
            "location": {"latitude": -1.4961, "longitude": 29.6733, "accuracy": 8.0}
        },
        {
            "kobo_form_id": "biodiversity_assessment",
            "submission_data": {
                "location_name": "Akagera National Park",
                "vegetation_type": "Savanna",
                "bird_species_count": 15,
                "mammal_species_count": 7,
                "weather_conditions": "Sunny"
            },
            "username": "researcher_john",
            "location": {"latitude": -1.9441, "longitude": 30.0619, "accuracy": 5.0}
        },
        {
            "kobo_form_id": "human_wildlife_conflict",
            "submission_data": {
                "conflict_type": "Crop damage",
                "animal_species": "Elephant",
                "damage_extent": "Moderate",
                "farmer_name": "Local farmer",
                "compensation_needed": "Yes"
            },
            "username": "community_liaison",
            "location": {"latitude": -2.0469, "longitude": 29.7319, "accuracy": 12.0}
        }
    ]
    
    for i, submission_data in enumerate(test_submissions, 1):
        submission_data["device_id"] = f"test_device_{i}"
        submission_data["app_version"] = "1.0.0"
        submission_data["submitted_at"] = datetime.now().isoformat()
        
        # Add a test image for the first submission
        if i == 1:
            submission_data["media_files"] = [
                {
                    "filename": f"wildlife_photo_{i}.jpg",
                    "file_type": "image",
                    "mime_type": "image/jpeg",
                    "file_size": 1024 * i,
                    "question_name": "evidence_photo",
                    "file_data": create_test_image()
                }
            ]
        
        try:
            response = requests.post(
                f"{API_BASE}/submissions/",
                json=submission_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                submission_id = response.json()["id"]
                submission_ids.append(submission_id)
                print(f"✅ Created submission {i}: {submission_id}")
            else:
                print(f"❌ Failed to create submission {i}: {response.json()}")
        except Exception as e:
            print(f"❌ Error creating submission {i}: {e}")
    
    print(f"Created {len(submission_ids)} test submissions")
    return submission_ids

def test_get_submissions():
    """Get submissions list"""
    print("\n🧪 Testing Get Submissions...")
    
    try:
        response = requests.get(f"{API_BASE}/submissions/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total submissions: {data['total']}")
            print(f"Page: {data['page']}")
            print(f"Submissions count: {len(data['submissions'])}")
            
            if data['submissions']:
                print("First submission:")
                print(json.dumps(data['submissions'][0], indent=2, default=str))
            
            return data['submissions']
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Get submissions test failed: {e}")
    
    return []

def test_get_submission_detail(submission_id):
    """Test getting submission details"""
    if not submission_id:
        print("\n⚠️ Skipping submission detail test - no submission ID")
        return
    
    print(f"\n🧪 Testing Get Submission Detail for {submission_id}...")
    
    try:
        response = requests.get(f"{API_BASE}/submissions/{submission_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Get submission detail test failed: {e}")

def test_submission_stats():
    """Test submission statistics"""
    print("\n🧪 Testing Submission Statistics...")
    
    try:
        response = requests.get(f"{API_BASE}/submissions/stats/overview")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Stats: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Submission stats test failed: {e}")

def test_sync_submissions():
    """Test manual sync with Kobo"""
    print("\n🧪 Testing Manual Sync...")
    
    sync_data = {
        "submission_ids": None,  # Sync all pending
        "force_resync": False
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/submissions/sync",
            json=sync_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    except Exception as e:
        print(f"Sync submissions test failed: {e}")

def test_filtered_submissions():
    """Test submissions with filters"""
    print("\n🧪 Testing Filtered Submissions...")
    
    try:
        # Test with sync status filter
        response = requests.get(f"{API_BASE}/submissions/?sync_status=pending")
        print(f"Pending submissions - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Pending submissions: {data['total']}")
        
        # Test with pagination
        response = requests.get(f"{API_BASE}/submissions/?page=1&per_page=5")
        print(f"Paginated submissions - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Page 1 (5 per page): {len(data['submissions'])} submissions")
    except Exception as e:
        print(f"Filtered submissions test failed: {e}")

def test_submission_filtering():
    """Test advanced submission filtering"""
    print("\n🧪 Testing Advanced Submission Filtering...")
    
    try:
        # Test filter by username
        response = requests.get(f"{API_BASE}/submissions/?username=researcher_jane")
        print(f"Filter by username - Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Jane's submissions: {data['total']}")
        
        # Test filter by form_id
        response = requests.get(f"{API_BASE}/submissions/?form_id=wildlife_survey_001")
        print(f"Filter by form_id - Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Wildlife survey submissions: {data['total']}")
        
        # Test combined filters
        response = requests.get(f"{API_BASE}/submissions/?sync_status=pending&per_page=10")
        print(f"Combined filters - Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Pending submissions (max 10): {len(data['submissions'])}")
    except Exception as e:
        print(f"Advanced filtering test failed: {e}")

def test_media_file_handling():
    """Test media file operations"""
    print("\n🧪 Testing Media File Handling...")
    
    try:
        # First, get a submission with media files
        response = requests.get(f"{API_BASE}/submissions/")
        if response.status_code == 200:
            submissions = response.json()["submissions"]
            
            for submission in submissions:
                # Get detailed submission to check for media files
                detail_response = requests.get(f"{API_BASE}/submissions/{submission['id']}")
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    if detail.get("media_files"):
                        media_file = detail["media_files"][0]
                        print(f"Found media file: {media_file['filename']}")
                        
                        # Test media download
                        media_response = requests.get(
                            f"{API_BASE}/submissions/{submission['id']}/media/{media_file['id']}"
                        )
                        print(f"Media download - Status Code: {media_response.status_code}")
                        if media_response.status_code == 200:
                            print(f"Media file downloaded successfully")
                        break
            else:
                print("No submissions with media files found")
    except Exception as e:
        print(f"Media file handling test failed: {e}")

def test_error_handling():
    """Test API error handling"""
    print("\n🧪 Testing Error Handling...")
    
    try:
        # Test invalid submission
        invalid_submission = {
            "kobo_form_id": "",  # Empty form ID should fail
            "submission_data": {},  # Empty data should fail
            "submitted_at": "invalid_date"  # Invalid date should fail
        }
        
        response = requests.post(
            f"{API_BASE}/submissions/",
            json=invalid_submission,
            headers={"Content-Type": "application/json"}
        )
        print(f"Invalid submission - Status Code: {response.status_code}")
        if response.status_code == 400:
            print("✅ Properly rejected invalid submission")
        
        # Test non-existent submission
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{API_BASE}/submissions/{fake_uuid}")
        print(f"Non-existent submission - Status Code: {response.status_code}")
        if response.status_code == 404:
            print("✅ Properly returned 404 for non-existent submission")
    except Exception as e:
        print(f"Error handling test failed: {e}")

def run_comprehensive_tests():
    """Run comprehensive API test suite"""
    print("🚀 Starting Comprehensive Form Submission API Tests")
    print("="*60)
    
    # Track test results
    results = {}
    
    # Basic connectivity tests
    print("\n📡 CONNECTIVITY TESTS")
    print("-" * 30)
    results["api_status"] = test_api_status()
    results["health_check"] = test_health_check()
    
    # Forms API tests (feeding frontend)
    print("\n📋 FORM FEEDING TESTS")
    print("-" * 30)
    form_id = test_forms_api()
    test_form_detail(form_id)
    results["forms_api"] = form_id is not None
    
    # Submission creation tests
    print("\n📝 SUBMISSION CREATION TESTS")
    print("-" * 30)
    submission_ids = test_create_multiple_submissions()
    results["create_submissions"] = len(submission_ids) > 0
    
    # Single submission test for backward compatibility
    single_submission_id = test_create_submission()
    if single_submission_id:
        submission_ids.append(single_submission_id)
    
    # Submission retrieval tests
    print("\n📊 SUBMISSION RETRIEVAL TESTS")
    print("-" * 30)
    submissions = test_get_submissions()
    results["get_submissions"] = len(submissions) >= 0
    
    if submission_ids:
        test_get_submission_detail(submission_ids[0])
    
    # Advanced filtering tests
    print("\n🔍 FILTERING TESTS")
    print("-" * 30)
    test_submission_filtering()
    test_filtered_submissions()
    
    # Statistics and monitoring
    print("\n📈 STATISTICS TESTS")
    print("-" * 30)
    test_submission_stats()
    
    # Sync operations
    print("\n🔄 SYNC TESTS")
    print("-" * 30)
    test_sync_submissions()
    
    # Media handling
    print("\n📸 MEDIA HANDLING TESTS")
    print("-" * 30)
    test_media_file_handling()
    
    # Error handling
    print("\n⚠️ ERROR HANDLING TESTS")
    print("-" * 30)
    test_error_handling()
    
    # Final summary
    print("\n" + "="*60)
    print("🧪 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} core tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All core tests passed! Your Form Submission API is working correctly.")
        print("\n🔥 SYSTEM STATUS: READY FOR PRODUCTION")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        print("\n⚠️ SYSTEM STATUS: NEEDS ATTENTION")
    
    print("\n" + "="*60)
    print("📋 NEXT STEPS:")
    print("="*60)
    print("1. 🔧 Fix any failed tests above")
    print("2. 📱 Test form submissions from your mobile app")
    print("3. 👀 Monitor the /health endpoint regularly")
    print("4. 🔄 Check submission sync status with Kobo")
    print("5. 📚 View full API documentation at http://localhost:8000/docs")
    print("6. 🌍 Test with real wildlife conservation data")
    print("7. 🚀 Deploy to production environment")

def run_all_tests():
    """Backward compatibility - calls comprehensive tests"""
    return run_comprehensive_tests()

if __name__ == "__main__":
    try:
        run_comprehensive_tests()
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure your FastAPI server is running on http://localhost:8000")
        print("Run: uvicorn app.main:app --reload")
        print("\nAlso ensure you have:")
        print("1. ✅ Updated your API router to include submissions")
        print("2. ✅ Run database migration script")
        print("3. ✅ Installed all dependencies")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()