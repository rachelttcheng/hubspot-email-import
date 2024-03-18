# use csv files instead of json to reduce memory bloat; we're reading in non-nested tabular values

# requires https://github.com/PS1607/mbox-to-json to help conversion from mbox to csv
# run command:  % mbox-to-json <filename/path> -c
#   - c flag is to convert to csv instead of json

# fields we want to import:
#   - X-Gmail-Labels (tells us if message is categorized as Sent)
#   - Date (date and time message was sent)
#   - From (email of sender)
#   - To (if email is in Sent category, the people who receive the email)
#   - CC (cc'ed people)
#   - Subject (email subject)
#   - Body (email body)


# column fields for hubspot
#   - email address (that connects to contact)
#   - Email Subject
#   - Email Body
#   - Email Direction
#   - any applicable custom properties

import re
import pandas as pd
import email.utils
from datetime import datetime, timezone, timedelta
from email.header import decode_header, make_header

keys=['x-gmail-labels', 'date', 'from', 'to', 'cc', 'subject', 'body']


def extractEmails(emailCol):
    # if cell is empty (NaN/null in pandas), skip cell
    if pd.isnull(emailCol):
        return

    # use regex to find all valid email strings within the 
    validEmails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', emailCol)

    # if multiple emails, should be delimited by ';' character as per hubspot formatting documentation
    return ";".join(validEmails)


# needs to be in either Unix timestamp in milliseconds or UTC format
def getDates(dateCol):
    # current dates come into sheet with RFC 2822 format of, e.g. "Fri, 15 Dec 2023 16:40:42 <time offset>"
    # convert to unix timestamp in milliseconds
    dt_tuple = email.utils.parsedate_tz(dateCol)

    # ensure date is in valid format
    if dt_tuple is None:
        raise ValueError("Invalid RFC 2822 date format")

    # unpack non-timezone date elements and reconstruct into datetime object
    dt = datetime(*dt_tuple[:6])

    # check for timezone offset and handle
    if dt_tuple[9] is not None:
        tz_offset = timedelta(seconds=dt_tuple[9])
        dt -= tz_offset
    
    # convert to UTC
    dt = dt.replace(tzinfo=timezone.utc)
    
    # return unix timestamp in milliseconds, as a string
    return str(int(dt.timestamp() * 1000))


def getNonDomainEmails(fromData, toData, ccData):
    combinedData = set()

    # convert data into lists and only add non-insidemaps domain emails to final list
    if 'insidemaps' not in fromData:
        combinedData.add(fromData.rstrip())

    toData = toData.split(";")
    for address in toData:
        if 'insidemaps' not in address:
            combinedData.add(address.rstrip())

    if not pd.isnull(ccData):
        ccData = ccData.split(";")
        for address in ccData:
            if 'insidemaps' not in address:
                combinedData.add(address.rstrip())

    return list(combinedData)

def cleanEmailData(inputFilename, outputFilename):
    # assume inputFilename is within same folder as main program, in format "inputfilename.csv"
    emails = pd.read_csv(inputFilename)

    # *******BEGIN CLEANING DATA*******

    # filter data only from specified key fields; make sure headers aren't case sensitive by lowercasing them and remove duplicates
    emails.columns = emails.columns.str.lower()
    emails = emails.loc[:,~emails.columns.duplicated()]
    emails = emails[keys]

    # clean up "X-Gmail-Labels" to include only 'Incoming' (from 'Inbox') or 'Outgoing' (from 'Sent')
    emails['x-gmail-labels'] = emails['x-gmail-labels'].map(lambda x: 'Outgoing' if 'Sent' in x else 'Incoming')

    # clean up date to be in format of: day.month.year hh:mm
    emails['date'] = emails['date'].map(lambda x: getDates(x))

    # clean up "To", "From", "CC", and "In-Reply-To" fields to only include email, not name
    # can be multiple "To" and "CC" emails, should only have one "From" and "In-Reply-To"
    emails['to'] = emails['to'].map(lambda x: extractEmails(x))
    emails['from'] = emails['from'].map(lambda x: extractEmails(x))
    emails['cc'] = emails['cc'].map(lambda x: extractEmails(x))

    # *******START ASSIGNING ACTIVITY TO RELEVANT EMAILS/CONTACTS********

    # create and add values new column, values being a list of all relevant emails (non insidemaps domain) to later expand on
    emails['activity-assigned-to'] = ""
    for index, row in emails.iterrows():
        emails.at[index, 'activity-assigned-to'] = getNonDomainEmails(row['from'], row['to'], row['cc'])

    # drop all rows in which activity-assigned-to is NaN
    emails = emails[emails['activity-assigned-to'].notna()]
    
    # decode email headers if they are encoded
    emails['subject'] = emails['subject'].map(lambda x: str(make_header(decode_header(x))))

    # *******WRITE CLEANED DATA********

    # write cleaned and assigned data to output file
    emails.to_csv('./' + outputFilename, index=False)