import json
import os
import time

import requests
from bs4 import BeautifulSoup

import constants


def fetch_buildId():
    response_initial = requests.get(constants.LOGIN_PAGE_URL, allow_redirects=True)
    soup = BeautifulSoup(response_initial.text, "html.parser")
    script_element = soup.find("script", id="__NEXT_DATA__")
    if not script_element:
        return False, "Failed to find the script element with id '__NEXT_DATA__'."

    script_data = json.loads(script_element.string)
    return True, script_data.get("buildId", "")


def get_access_token():
    # load form access token file, if exists test it with a /me request
    # if not exists or not valid, fetch new token and save it
    if os.path.exists(constants.ACCESS_TOKEN_FILE):
        with open(constants.ACCESS_TOKEN_FILE, "r") as f:
            access_token = f.read()

        if access_token:
            if test_me(access_token):
                print("Token loaded from file.")
                return True, access_token
            else:
                print("Token loaded from file is invalid.")

    otp = input("Enter OTP: ")
    headers = {"Content-Type": "application/json"}
    data = {
        "username": constants.ACADEMY_USERNAME,
        "password": constants.ACADEMY_PASSWORD,
        "otp": otp,
    }
    response_login = requests.post(constants.LOGIN_API_URL, headers=headers, json=data)

    if response_login.status_code != 201:
        error_message = (
            f"Login request failed with status code {response_login.status_code}."
        )
        try:
            error_details = response_login.json().get("error", "")
            error_message += f" Details: {error_details}"
        except:
            pass  # If there's an error parsing the JSON, we'll just use the generic error message.
        return False, error_message

    response_json = response_login.json()
    access_token = response_json.get("access_token", "")
    if not access_token:
        return False, "Obtained response but access token was not found."

    with open(constants.ACCESS_TOKEN_FILE, "w") as f:
        f.write(access_token)

    return True, access_token


def test_me(bearer_token):
    headers = {"Authorization": f"Bearer {bearer_token}"}
    response = requests.get(constants.ME_URL, headers=headers)
    return response.status_code == 200


def fetch_next_token(access_token, buildId):
    url_get = constants.NEXT_TOKEN_URL.format(buildId)
    headers_get = {"Cookie": f"token={access_token}"}
    response_get = requests.get(url_get, headers=headers_get, allow_redirects=True)

    if response_get.status_code != 200:
        error_message = f"Fetching the next token failed with status code {response_get.status_code}."
        try:
            error_details = response_get.json().get("error", "")
            error_message += f" Details: {error_details}"
        except:
            pass  # If there's an error parsing the JSON, we'll just use the generic error message.
        return False, error_message

    download_data = response_get.json()
    next_token = download_data.get("pageProps", {}).get("token", "")
    if not next_token:
        return False, "Obtained response but next token was not found."

    return True, next_token


def auth():
    # Fetch BuildId
    success, buildId = fetch_buildId()
    if not success:
        print(buildId)  # This would print the error message in this context.
        exit(1)
    print("BuildId fetched successfully.")

    time.sleep(1)

    # Get Access Token
    success, access_token = get_access_token()
    if not success:
        # In case of failure, the access_token variable will contain the error message.
        print(access_token)
        exit(1)
    print("Successfully logged in and obtained access token.")

    time.sleep(1)

    # Fetch Next Token
    success, bearer_token = fetch_next_token(access_token, buildId)
    if not success:
        # In case of failure, the bearer_token variable will contain the error message.
        print(bearer_token)
        exit(1)
    print("Next token fetched successfully.")

    return bearer_token
