# Scraping sold listings from StubHub for Barry's Tickets
#
# @author Bardia Barahman
# Last edit: 6/12/2018
#
# Status: Complete.
# Description: Reads event id #'s from a .txt file and outputs
#              csv files for each event.
# Version 2.0

import requests
import pprint
import logging
import pandas as pd
import datetime as dt
import json

# logger = logging.getLogger("root")
# logging.basicConfig(
#     format = "\033[1;32m%(levelname)s: \033[1;30;m %(message)s",
#     level = logging.DEBUG
# )

HEADERS = { 'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0' }

PAYLOAD = { 'username': 'stubhub2@barrystickets.com',
            'password': 'I1Peace2!'}

# ------
# UPDATE THIS FIELD EACH SESSION!
# ------
PARAMS = { 'si' : '0563EEE3B5574ECEA162EC9243544A42'}
# The number of results you want each time you run the program (change accordingly)
rows = 100
# The path for the .txt file containing the eventID's
file = '/Users/bardiabarahman/Desktop/Internship/event_IDs.txt'


# Function that takes the .txt file and returns a list of the event id's
def read_integers(filename):
    with open(filename) as f:
        return [int(x) for x in f]

# create a session
sesh = requests.Session()

# Url to login to StubHub page (INIT)
url_LOGIN = 'https://iam.stubhub.com/session/token/init'

# make a login POST request, using the session
try:
    r = sesh.post(url_LOGIN, params=PARAMS, data=PAYLOAD, headers=HEADERS)
    if 'error' in r.text:
        print('Request failed.')
        print('Please correctly update the session id (si) parameter.')
        exit()
except requests.exceptions.HTTPError as h:
    print ("Http Error: ", h)
except requests.exceptions.ConnectionError as c:
    print ("Error Connecting (Possibly bad URL): ", c)


event_IDs = read_integers(file)
for eventID in event_IDs:

    # Sold listings for a certain eventID!
    url_SOLD = 'https://www.stubhub.com/shape/accountmanagement/sales/v1/event/'+str(eventID)+'?eventId='+str(eventID)+'&start=0&rows='+str(rows)+'&sectionId=&sort=SALEDATE Desc&priceType=listprice&&shstore=1'
    # subsequent requests using the session will automatically handle cookies
    try:
        s = sesh.get(url_SOLD)
    except requests.exceptions.HTTPError as h:
        print ("Http Error: ", h)
    except requests.exceptions.ConnectionError as c:
        print ("Error Connecting (Possibly bad URL): ", c)
        print("Did you correctly enter the event ID?")


    if 'blocked' in s.text:
        print('--------------------------------------')
        print('| BLOCKED by anti-robot software. :/ |')
        print('--------------------------------------')
        print (s.headers.get("content-type", "unknown"))
        exit()
    else:
        print('Retrieving sold listings for event ID: ' +str(eventID))
        soldInv = s.json()
        inv = soldInv['sales']['sale']
        if soldInv['sales']['numFound'] == 0:
            print('No sold listings. Did you correctly enter the event ID?')
            exit()

    # The event
    url_EVENT = 'https://www.stubhub.com/shape/catalog/events/v3/'+str(eventID)
    # Getting the event name from a different json endpoint
    try:
        e = sesh.get(url_EVENT)
        eventName = e.json()['name']
    except requests.exceptions.ConnectionError as ce:
        print ("Error Connecting (Possibly bad URL): ", ce)

    #Creating a pandas dataframe
    df = pd.DataFrame(inv)
    df['Price Sold'] = df.apply(lambda x: x['displayPricePerTicket']['amount'], axis=1)
    df['transactionDate'] = df['transactionDate'].apply(lambda x: dt.datetime.strptime(x,'%Y-%m-%dT%H:%M:%S.%fZ'))
    df['Transaction Date'] = df['transactionDate']
    df['Event Name'] = eventName
    df['Section ID'] = df['sectionId']
    df['Section Name'] = df['section']
    df['Seat Numbers'] = df['seats']
    df['Row'] = df['rows']
    df['Quantity'] = df['quantity']
    my_col = [
        'Transaction Date',
        'Event Name',
        'Section ID',
        'Section Name',
        'Row',
        'Seat Numbers',
        'Quantity',
        'Price Sold',
        'deliveryOption'
    ]
    final_df = df[my_col].copy()

    #Cleaning up the final dataframe
    final_df.loc[final_df.deliveryOption == 'EXTERNAL_TRANSFER', 'deliveryOption'] = 'Mobile Ticket'
    final_df.loc[final_df.deliveryOption == 'MOBILE_TICKET', 'deliveryOption'] = 'Mobile Ticket'

    #Returning the df into a CSV file
    csv_file_name = "%s.csv" % eventID
    final_df.to_csv(csv_file_name, index = False)

print('Task finished at ' + str(dt.datetime.now()))
