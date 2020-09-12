import os
import sys
import util
import myob_v0
import json
from datetime import datetime
from optparse import OptionParser

invoice_template_file = './templates/dana_invoice_post.tpl'
contacts_file = './myob_contacts.json'

# parse command-line options
usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-i", "--payment_file", metavar="FILE", dest="payments_file",
                  help="input file with payments")
parser.add_option("-d", "--date", metavar="DATE", dest="date",
                  help="date the money has been banked, in format YYYY-MM-DD")
parser.add_option("-t", "--expected_total", type="float", metavar="TOTAL", dest="expected_total",
                  help="expected total amount the payments have to sum up to")
parser.add_option("-v", "--verify_only", action="store_true", dest="verify_only", default=False,
                  help="only verify that all payments can be mapped but do not create any invoices")
parser.add_option("-n", "--no_dryrun", action="store_false", dest="dryrun", default=True,
                  help="actually create invoices")
(options, args) = parser.parse_args()

if not options.payments_file:
    parser.error('No input file with payments specified')
if not options.expected_total:
    parser.error('No expected total amount specified')
if not options.date:
    parser.error('No date specified')

try:
    date_object = datetime.strptime(options.date, '%Y-%m-%d').date()
except:
    parser.error('Specified date not valid')

audit_file = f'{options.payments_file}.audit.csv'

assert os.path.isfile(invoice_template_file), f'invoice template {invoice_template_file} does not exist'
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

# read payment data from csv
header, payments = util.read_cash_payments_csv(options.payments_file)

if len(payments) == 0:
    print('No records to process. Exiting...')
    sys.exit(0)

contact_dict = {}
for c in contacts:
    contact_dict[c['name']] = c

# verify integrity
total: float = 0.
print('verifying contacts can be mapped for all dana payments, and expected total sum is matched')
for p in payments:
    total += float(p['Amount'])
    if p['Contact'] not in contact_dict:
        print(f'--> cannot find contact with name {p["Contact"]}')
        sys.exit(1)
    if p['payment_type'] == util.PaymentType.OTHER:
        print(f'--> Unsupported payment type found: {str(p)}')
        sys.exit(1)
    p['contact_uid'] = contact_dict[p['Contact']]['uid']

print(f'found {len(payments)} payments')

if total != options.expected_total:
    print(f'Expected money to sum up to ${options.expected_total}, but got ${total}')
    sys.exit(1)

if options.verify_only:
    sys.exit(0)

print('getting required items from myob')
payment_types = set([p['payment_type'] for p in payments])
items: dict = {}
for pt in payment_types:
    items[pt] = myob_v0.get_item_by_name(util.ITEM_NAMES[pt])

# create an invoice for each record and save it in audit log
with open(audit_file, 'w') as f:
    f.write(f'Contact,Item,Amount,Date,Invoice{os.linesep}')
    for p in payments:
        date_with_time = f'{options.date}T00:00:00'
        invoice_number = myob_v0.get_next_invoice_number()
        tmp_item = items[p["payment_type"]]
        param_dict = {
            '__INVOICE_NUMBER__': invoice_number,
            '__DATE__': date_with_time,
            '__CONTACT_UID__': f'{p["contact_uid"]}',
            '__AMOUNT__': float(p['Amount']),
            '__DESCRIPTION__': f'{tmp_item["description"]}',
            '__UNIT_OF_MEASURE__': f'{tmp_item["unitOfMeasure"]}',
            '__ITEM_UID__': f'{tmp_item["uid"]}',
            '__ACCOUNT__': f'{tmp_item["saleAccount"]["uid"]}',
            '__TAX_TYPE_UID__': f'{tmp_item["saleTaxType"]["uid"]}'
        }
        print(f'creating invoice for {p["Contact"]} {p["Amount"]}, {options.date}, {invoice_number})')
        myob_v0.create_invoice(invoice_template_file, param_dict, dryrun=options.dryrun)
        audit_record = f'{p["Contact"]},{tmp_item["name"]},{p["Amount"]},{options.date},{invoice_number}{os.linesep}'
        f.write(audit_record)

print(f'Done. Audit records written to {audit_file}')
