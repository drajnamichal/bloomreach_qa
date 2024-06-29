import base64
import requests
import pytest
import time
from bs4 import BeautifulSoup

# API URL and credentials
api_url = "https://gqa.api.gdev.exponea.com/data/v2/projects/6f521150-d92d-11ed-a284-de49e5a76b0b/customers/export-one"
api_key_id = "fbiiqlwwf5gnnuxns77fkxfkoysnl6f0nhf21xixykxxsiia9c341x4ewr4w30nb"
api_key_secret = "fypwdlyoi2sou87lvmtl80nmf68y6hxfngigssul62ojsf2qxmneiag3xo4wnpfg"
customer_id = "customer735290"

# Encode credentials
auth_header = f"Basic {base64.b64encode(f'{api_key_id}:{api_key_secret}'.encode()).decode()}"

def fetch_csrf_token_and_cookies(survey_link):
    response = requests.get(survey_link)
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
        "customer_ids": {"registered": customer_id},
        "properties": ["survey link"]
    }
    response = requests.post(api_url, json=payload, headers=headers)
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
    return {"status": "success", "response": response.text} if response.status_code == 200 else {"status": "failed", "response": response.text}

def fetch_tracked_events():
    headers = {
        "accept": "application/json",
        "authorization": auth_header,
        "Content-Type": "application/json"
    }
    payload = {
        "customer_ids": {"registered": customer_id}
    }
    response = requests.post(api_url, json=payload, headers=headers)
    events = response.json().get('events', [])
    return events

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
#    - Scenario: Submit the survey with various types of input for the favorite movie question, including very long titles, titles with special characters 
#                or potential script injections
#    - Expected outcome: The survey should handle all input types correctly