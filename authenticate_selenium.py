import os
import time
import json
import requests
import pyotp
import util
from secureconfig import SecureConfig
from datetime import datetime, timedelta
from dateutil import parser
import urllib.parse as urlparse
from urllib.parse import parse_qs
from selenium.webdriver.common.by import By


def datetime_converter(o):
    if isinstance(o, datetime):
        return o.__str__()


def authenticate(driver):
    config = SecureConfig().decrypt(util.secure_config_file)

    # log in to myob using 2-factor authentication
    encoded_redirect_url = urlparse.quote(config['redirect_url'])
    login_url = f'https://secure.myob.com/oauth2/account/authorize?' \
                f'client_id={config["myob_client_id"]}&' \
                f'redirect_uri={encoded_redirect_url}&' \
                f'response_type=code&' \
                f'scope=CompanyFile'
    driver.get(login_url)
    element = driver.find_element(By.ID, "UserName")
    element.send_keys(config['myob_username'])
    driver.find_element(By.XPATH, '//button[text()="Next "]').click()
    element = driver.find_element(By.ID, "Password")
    element.send_keys(config['myob_password'])
    driver.find_element(By.XPATH, '//button[text()="Sign in"]').click()
    element = driver.find_element(By.ID, "Token")
    totp = pyotp.TOTP(config['myob_ga_secret'])
    element.send_keys(totp.now())
    driver.find_element(By.XPATH, '//button[text()="Verify"]').click()

    # get code from redirect_url
    while True:
        if driver.current_url.startswith(config['redirect_url']):
            break
        time.sleep(0.5)

    parsed = urlparse.urlparse(driver.current_url)
    code = parse_qs(parsed.query)['code'][0]

    # get access token
    url = 'https://secure.myob.com/oauth2/v1/authorize/'
    payload = {
        'code': code,
        'client_id': config['myob_client_id'],
        'client_secret': config['myob_client_secret'],
        'redirect_uri': config['redirect_url'],
        'scope': 'CompanyFile',
        'grant_type': 'authorization_code'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(url, data=payload, headers=headers)
    auth_tokens = r.json()

    with open(config['token_file'], "w") as f:
        data = {'access_token': auth_tokens['access_token'],
                'expires_at': datetime.now() + timedelta(seconds=(int(auth_tokens['expires_in']) - 60))}
        print(f"{json.dumps(data, default=datetime_converter)}", file=f)

    return driver


def get_access_token(driver):
    config = SecureConfig().decrypt(util.secure_config_file)
    if os.path.isfile(config['token_file']):
        with open(config['token_file'], "r") as f:
            data = json.load(f)
            if datetime.now() > parser.parse(data['expires_at']):
                authenticate(driver)
                return get_access_token(driver)
            else:
                return data['access_token']
    else:
        authenticate(driver)
        url = 'https://essentials.myob.co.nz/LA.CO.NZ/app.htm#businesses/179995/invoices/new'
        driver.get(url)
        return get_access_token(driver)
