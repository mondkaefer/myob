import os
import sys
import util
import time
import myob_selenium
import myob_v0
import json
from optparse import OptionParser
from selenium import webdriver
import chromedriver_binary


memo_blacklist: list = []
contact_map_file = './memo_to_contact_map.txt'
contacts_file = './myob_contacts.json'

# parse command-line options
usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-i", "--payment_file", metavar="FILE", dest="payments_file", help="input file with payments")
parser.add_option("--verify_only",
                  action="store_true", dest="verify_only", default=False,
                  help="only verify that all payments can be mapped but do not create any invoices")
(options, args) = parser.parse_args()
if not options.payments_file:
    parser.error('No input file with payments specified')

assert os.path.isfile(contact_map_file), f'contact map file {contact_map_file} does not exist'
assert os.path.isfile(options.payments_file), f'payments file {options.payments_file} does not exist'

# load contacts from file or fetch them from myob
if os.path.isfile(contacts_file):
    print(f'reading myob contacts from file {contacts_file}')
    with open(contacts_file) as json_file:
        contacts = json.load(json_file)
else:
    print(f'downloading contacts from myob')
    contacts = myob_v0.get_contacts()
    print(f'storing myob contacts in file {contacts_file}')
    with open(contacts_file, 'w') as json_file:
        json.dump(contacts, json_file)

# read data from bank feed csv
header, payments = util.read_bank_feed_csv(options.payments_file, memo_blacklist)

dana_payments = [p for p in payments if p['payment_type'] == util.PaymentType.DANA]

if len(dana_payments) == 0:
    print('No dana records to process. Exiting...')
    sys.exit(0)

contact_dict = {}
for c in contacts:
    contact_dict[c['name']] = c

contact_map = util.read_contact_map(contact_map_file)

# verify integrity
print('verifying contacts can be mapped for all dana payments')
for dp in dana_payments:
    if dp['Memo/Description'] not in contact_map:
        print(f'--> cannot find contact for memo "{dp["Memo/Description"]}"')
        sys.exit(1)
    contact_name = contact_map[dp['Memo/Description']]
    if contact_name not in contact_dict:
        print(f'--> cannot find contact with name {contact_name}')
        sys.exit(1)
    dp['display_name'] = contact_name

print(f'found {len(dana_payments)} dana payments')

if options.verify_only:
    sys.exit(0)

driver = webdriver.Chrome()
driver.execute_script("window.onbeforeunload = function() {};")
myob_selenium.log_in(driver)

for dp in dana_payments:
    try:
        (day, month, year) = dp['Date'].split('-')
    except ValueError:
        (day, month, year) = dp['Date'].split('/')
    # date_of_issue = f'{day.zfill(2)}/{month.zfill(2)}/20{year}'
    date_of_issue = f'{day.zfill(2)}/{month.zfill(2)}/{year}'
    myob_selenium.go_to_invoices_page(driver)
    print(f'Creating invoice for {contact_map[dp["Memo/Description"]]} (${dp["Amount"]}, {date_of_issue})')
    invoice_number = myob_selenium.create_new_invoice(driver, date_of_issue, dp['Amount'],
                                                      contact_map[dp["Memo/Description"]])
    print(f'Going to transaction page')
    myob_selenium.go_to_transactions_page(driver)
    tmp_match_string = dp['Memo/Description']
    if tmp_match_string.startswith('AP#'):
        other_match_string = tmp_match_string.split(' ')[0].replace('#', '')
    else:
        other_match_string = 'NOT_SURE_WHAT_TO_DO'
    print(f'Trying to match transaction to invoice {invoice_number}')
    myob_selenium.match_transaction(driver, date_of_issue, dp['OP Bank Account Number'],
                                    other_match_string, invoice_number)

driver.quit()
print(f'Done.')
