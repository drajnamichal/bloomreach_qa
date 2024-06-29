# Bloomreach Survey API Testing

This project contains automated API tests for Bloomreach's Survey feature, as part of a QA Engineer assignment.

## Overview

The test suite interacts with Bloomreach's Survey API to validate various scenarios, including submitting surveys and verifying event tracking. It uses pytest as the testing framework and requests for making HTTP calls.

## Assignment Details

### Task 1: Automated API Tests

Implement automated API tests for the following scenarios:

1. Happy Path (at least 2 test cases):
   - Submit a survey with all required questions answered.
   - Verify that events are tracked asynchronously for each answered question.
   - Check that tracked events contain all required information.

2. Error Situation (1 test case):
   - Submit a survey with a missing required field.
   - Verify that an error message is returned and no events are tracked.

### Task 2: Additional Test Scenarios

Define at least 3 additional test scenarios (implementation not required).

## Prerequisites

- Python 3.x
- pip (Python package installer)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/drajnamichal/bloomreach_qa.git
   cd bloomreach_qa
   ```

2. Install the required packages

## Configuration

Create a `.env` file in the project directory and add the following variables:

- `API_URL`
- `API_KEY_ID`
- `API_KEY_SECRET`
- `CUSTOMER_ID`

## Running the Tests

To run all tests:

```
pytest test_survey_api.py
```

To run a specific test:

```
pytest test_survey_api.py::test_happy_path_full_response
```

## Test Scenarios

1. `test_happy_path_full_response`: Tests a complete survey submission with all questions answered.
2. `test_happy_path_minimum_response`: Tests a survey submission with only the required questions answered.
3. `test_missing_required_field`: Tests the API's response when a required field is missing.

## Additional Test Scenarios (Defined, not implemented)

1. Error handling for invalid CSRF token
2. Multiple selection for music genres
3. Text field input variations

## Key Functions

- `fetch_csrf_token_and_cookies`: Retrieves CSRF token and session cookie from the survey page.
- `get_survey_link`: Fetches the survey link from the API.
- `submit_survey`: Submits the survey with given answers.
- `fetch_tracked_events`: Retrieves tracked events for the customer.
- `wait_for_events`: Waits for a specified number of events to be tracked.

## Implementation Steps

1. Use the Customer Export Endpoint to find the survey link for the customer.
2. Analyze the survey submission request in a browser to simulate it in the test.
3. Use the Customer Export Endpoint to verify event tracking after survey submission.

## Documentation

For more details on the Customer Export Endpoint, refer to:
https://documentation.bloomreach.com/engagement/reference/export-a-customer-2