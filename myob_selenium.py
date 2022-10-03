import util
import time
import pyotp
from secureconfig import SecureConfig
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

config = SecureConfig().decrypt(util.secure_config_file)

def log_in(driver):
    driver.get('https://essentials.myob.co.nz/')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserName")))
    element = driver.find_element_by_id("UserName")
    element.send_keys(config['myob_username'])
    driver.find_element_by_xpath('//button[text()="Next "]').click()
    element = driver.find_element_by_id("Password")
    element.send_keys(config['myob_password'])
    driver.find_element_by_xpath('//button[text()="Sign in"]').click()
    element = driver.find_element_by_id("Token")
    totp = pyotp.TOTP(config['myob_ga_secret'])
    element.send_keys(totp.now())
    driver.find_element_by_xpath('//button[text()="Verify"]').click()


#@util.wait_for_enter_before_execution
@util.wait_before_execution(wait_s=4)
def go_to_invoices_page(driver):
    text = 'Sales'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//*[text()='{text}']")))
    driver.find_element_by_xpath(f'//*[text()="{text}"]').click()
    text = 'Invoices'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//*[text()='{text}']")))
    driver.find_element_by_xpath(f'//*[text()="{text}"]').click()


def create_new_invoice(driver, date, amount, contact_display_name):
    id = 'createButton'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, id)))
    element = driver.find_element_by_id(id)
    while not (element.is_displayed() and element.is_enabled()):
        time.sleep(1)
    element.click()
    id = 'itemId'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, id)))
    driver.find_element_by_id(id).send_keys('Dana\n')
    id = 'issueDate'
    element = driver.find_element_by_id(id)
    element.clear()
    element.send_keys(f'{date}\n')
    id = 'invoiceNumber'
    invoice_number = driver.find_element_by_id(id).get_attribute('value')
    id = 'contactId'
    driver.find_element_by_id(id).send_keys(f'{contact_display_name}\n')
    id = 'unitPrice'
    element = driver.find_element_by_id(id)
    element.clear()
    element.send_keys(f'{amount}\n')
    id = 'save'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, id)))
    driver.find_element_by_id(id).click()
    return invoice_number


#@util.wait_for_enter_before_execution
@util.wait_before_execution(wait_s=4)
def go_to_transactions_page(driver):
    text = 'Banking'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//*[text()='{text}']")))
    driver.find_element_by_xpath(f'//*[text()="{text}"]').click()
    text = 'Bank transactions'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//*[text()='{text}']")))
    driver.find_element_by_xpath(f'//*[text()="{text}"]').click()


#@util.wait_for_enter_before_execution
@util.wait_before_execution(wait_s=3)
def match_transaction(driver, date_string: str, bank_account: str, other_match_string: str,
                      invoice_number: str):
    id = 'processed'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, id)))
    select = Select(driver.find_element_by_id(id))
    select.select_by_visible_text('Unallocated transactions')
    id = 'from'
    element = driver.find_element_by_id(id)
    element.clear()
    element.send_keys(f'{date_string}\n')
    id = 'to'
    element = driver.find_element_by_id(id)
    element.clear()
    element.send_keys(f'{date_string}\n')
    time.sleep(1)
    match_string = bank_account
    try:
        button = driver.find_element_by_xpath(f"//span[contains(text(), '{match_string}')]/following::button[@class='btn btn-default btn-xs actions-button']")
    except NoSuchElementException:
        match_string = other_match_string
        button = driver.find_element_by_xpath(f"//span[contains(text(), '{match_string}')]/following::button[@class='btn btn-default btn-xs actions-button']")
    button.click()
    time.sleep(0.5)
    try:
        checkbox = driver.find_element_by_xpath(f"//td[contains(text(), '{invoice_number}')]/preceding::input[@type='checkbox'][1]")
        checkbox.click()
    except NoSuchElementException:
        print('--> Cannot match - please match manually <--')

    id = 'saveButton'
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, id)))
    driver.find_element_by_id(id).click()

