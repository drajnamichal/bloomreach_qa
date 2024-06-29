import os
import base64
import requests
import pytest
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

API_URL = os.getenv("API_URL")
API_KEY_ID = os.getenv("API_KEY_ID")
API_KEY_SECRET = os.getenv("API_KEY_SECRET")
CUSTOMER_ID = os.getenv("CUSTOMER_ID")

auth_header = f"Basic {base64.b64encode(f'{API_KEY_ID}:{API_KEY_SECRET}'.encode()).decode()}"

def fetch_csrf_token_and_cookies(survey_link):
    response = requests.get(survey_link)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch survey link: {response.status_code}")
    soup = BeautifulSoup(response.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
    session_cookie = response.cookies.get('session')
    return csrf_token, session_cookie

def get_survey_link():
    headers = {
        "accept": "application/json",
        "authorization": auth_header,
        "Content-Type": "application/json"
    }
    payload = {
        "customer_ids": {"registered": CUSTOMER_ID},
        "properties": ["survey link"]
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json().get('properties', {}).get('survey link')

def submit_survey(survey_link, answers, csrf_token, session_cookie):
    headers = {
        "Referer": survey_link,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    cookies = {
        "session": session_cookie
    }
    answers['csrf_token'] = csrf_token
    response = requests.post(survey_link, headers=headers, data=answers, cookies=cookies)
    if response.status_code == 200:
        return {"status": "success", "response": response.text}
    else:
        return {"status": "failed", "response": response.text}

def fetch_tracked_events():
    headers = {
        "accept": "application/json",
        "authorization": auth_header,
        "Content-Type": "application/json"
    }
    payload = {
        "customer_ids": {"registered": CUSTOMER_ID}
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json().get('events', [])

def wait_for_events(initial_count, expected_count, timeout=30, poll_interval=5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        events = fetch_tracked_events()
        if len(events) >= initial_count + expected_count:
            return events
        time.sleep(poll_interval)
    return fetch_tracked_events()

@pytest.fixture
def survey_setup():
    survey_link = get_survey_link()
    csrf_token, session_cookie = fetch_csrf_token_and_cookies(survey_link)
    return survey_link, csrf_token, session_cookie

@pytest.fixture
def initial_event_count():
    events = fetch_tracked_events()
    return len(events)

def test_happy_path_full_response(survey_setup, initial_event_count):
    survey_link, csrf_token, session_cookie = survey_setup
    print(f"Initial event count before test_happy_path_full_response: {initial_event_count}")
    answers = {
        "question-0": "Blue",
        "question-1": "Pop",
        "question-2": "3",
        "question-3": "titanic"
    }
    result = submit_survey(survey_link, answers, csrf_token, session_cookie)
    assert "Survey successfully submitted" in result["response"], "Survey submission failed"
    events = wait_for_events(initial_event_count, 4)
    final_event_count = len(events)
    print(f"Final event count after test_happy_path_full_response: {final_event_count}")
    assert final_event_count >= initial_event_count + 4, "Not all events were tracked"

    # Assert event structure for the last 4 events
    for event in events[-4:]:
        assert event["type"] == "survey", "Event type is not 'survey'"
        assert "timestamp" in event, "Timestamp is missing"
        assert "properties" in event, "Properties are missing"
        props = event["properties"]
        assert "answer" in props, "Answer is missing in properties"
        assert "question" in props, "Question is missing in properties"
        assert "question_id" in props, "Question ID is missing in properties"
        assert "question_index" in props, "Question index is missing in properties"
        assert "survey_id" in props, "Survey ID is missing in properties"
        assert "survey_name" in props, "Survey name is missing in properties"

def test_happy_path_minimum_response(survey_setup, initial_event_count):
    survey_link, csrf_token, session_cookie = survey_setup
    print(f"Initial event count before test_happy_path_minimum_response: {initial_event_count}")
    answers = {
        "question-0": "Green",
        "question-1": "Jazz",
        "question-2": "4"
    }
    result = submit_survey(survey_link, answers, csrf_token, session_cookie)
    assert "Survey successfully submitted" in result["response"], "Survey submission failed"
    events = wait_for_events(initial_event_count, 3)
    final_event_count = len(events)
    print(f"Final event count after test_happy_path_minimum_response: {final_event_count}")
    assert final_event_count >= initial_event_count + 3, "Not all events were tracked"

    # Assert event structure for the last 4 events
    for event in events[-4:]:
        assert event["type"] == "survey", "Event type is not 'survey'"
        assert "timestamp" in event, "Timestamp is missing"
        assert "properties" in event, "Properties are missing"
        props = event["properties"]
        assert "answer" in props, "Answer is missing in properties"
        assert "question" in props, "Question is missing in properties"
        assert "question_id" in props, "Question ID is missing in properties"
        assert "question_index" in props, "Question index is missing in properties"
        assert "survey_id" in props, "Survey ID is missing in properties"
        assert "survey_name" in props, "Survey name is missing in properties"

def test_missing_required_field(survey_setup, initial_event_count):
    survey_link, csrf_token, session_cookie = survey_setup
    print(f"Initial event count before test_missing_required_field: {initial_event_count}")
    answers = {
        "question-1": "Pop",
        "question-2": "3",
        "question-3": "titanic"
    }
    result = submit_survey(survey_link, answers, csrf_token, session_cookie)
    assert "Survey successfully submitted" not in result["response"], "Survey was incorrectly accepted"
    events = wait_for_events(initial_event_count, 0)
    final_event_count = len(events)
    print(f"Final event count after test_missing_required_field: {final_event_count}")
    assert final_event_count == initial_event_count, "Unexpected events were tracked"

# Task 2 - Additional test scenarios:

# 1. Error handling for invalid CSRF token:
#    - Scenario: Test submitting the survey with an invalid CSRF token to verify that the submission is rejected, and an appropriate error message is returned.
#    - Expected outcome: The survey submission should fail, returning an error response indicating that the CSRF token is invalid, and no events should be tracked.

# 2. Multiple selection for music genres:
#    - Scenario: Submit the survey with various combinations of music genre selections (one, several, all, or none).
#    - Expected outcome: The survey should be submitted successfully, and the events should accurately reflect the selected genres.

# 3. Text Field Input Variations:
#    - Scenario: Submit the survey with various types of input for the favorite movie question, including very long titles, titles with special characters or potential script injections.
#    - Expected outcome: The survey should handle all input types correctly.
