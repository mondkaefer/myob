import os
import sys
import util
import myob_v0
import json
from optparse import OptionParser

memo_blacklist: list = []
invoice_template_file = './templates/dana_invoice_post_v0.tpl'
contact_map_file = './memo_to_contact_map.txt'
contacts_file = './myob_contacts.json'

# parse command-line options
usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-i", "--payment_file", metavar="FILE", dest="payments_file", help="input file with payments")
parser.add_option("--verify_only",
                  action="store_true", dest="verify_only", default=False,
                  help="only verify that all payments can be mapped but do not create any invoices")
parser.add_option("--no_dryrun",
                  action="store_false", dest="dryrun", default=True,
                  help="actually create invoices")
(options, args) = parser.parse_args()
if not options.payments_file:
    parser.error('No input file with payments specified')

audit_file = f'{options.payments_file}.audit.csv'

assert os.path.isfile(invoice_template_file), f'invoice template {invoice_template_file} does not exist'
assert os.path.isfile(contact_map_file), f'contact map file {contact_map_file} does not exist'
assert os.path.isfile(options.payments_file), f'payments file {options.payments_file} does not exist'

if len(memo_blacklist) > 0:
    reply = str(input('Found a blacklist. Want to continue (y/<any key>): ')).lower().strip()
    if len(reply) == 0 or reply[0] != 'y':
        sys.exit(0)

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
    dp['contact_uid'] = contact_dict[contact_map[dp['Memo/Description']]]['uid']

print(f'found {len(dana_payments)} dana payments')

if options.verify_only:
    sys.exit(0)

print('getting item "Dana" from myob')
dana_item = myob_v0.get_item_by_name('Dana')

# create an invoice for each record and save it in audit log
with open(audit_file, 'w') as f:
    f.write(f'Memo/Description,Contact,Amount,Date,Invoice{os.linesep}')
    for dp in dana_payments:
        try:
            (day, month, year) = dp['Date'].split('-')
            date = f'20{year}-{month}-{day}'
        except ValueError:
            (day, month, year) = dp['Date'].split('/')
            date = f'20{year}-{month}-{day}'
        date_with_time = f'{date}T00:00:00'
        invoice_number = myob_v0.get_next_invoice_number()
        param_dict = {
            '__INVOICE_NUMBER__': invoice_number,
            '__DATE__': date_with_time,
            '__CONTACT_UID__': f'{dp["contact_uid"]}',
            '__AMOUNT__': float(dp['Amount']),
            '__DESCRIPTION__': f'{dana_item["description"]}',
            '__UNIT_OF_MEASURE__': f'{dana_item["unitOfMeasure"]}',
            '__ITEM_UID__': f'{dana_item["uid"]}',
            '__ACCOUNT__': f'{dana_item["saleAccount"]["uid"]}',
            '__TAX_TYPE_UID__': f'{dana_item["saleTaxType"]["uid"]}'
        }
        print(f'creating invoice for {contact_map[dp["Memo/Description"]]} (${dp["Amount"]}, {date}, {invoice_number})')
        myob_v0.create_invoice(invoice_template_file, param_dict, dryrun=options.dryrun)
        audit_record = f'{dp["Memo/Description"]},{contact_map[dp["Memo/Description"]]},' \
                       f'{dp["Amount"]},{date},{invoice_number}{os.linesep}'
        f.write(audit_record)

print(f'Done. Audit record written to {audit_file}')
