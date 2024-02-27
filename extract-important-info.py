# use csv files instead of json to reduce memory bloat; we're reading in non-nested tabular values

# requires https://github.com/PS1607/mbox-to-json to help conversion from mbox to json

# fields we want to import:
#   - X-Gmail-Labels (tells us if message is categorized as Sent)
#   - Date (date and time message was sent)
#   - From (email of sender)
#   - To (if email is in Sent category, the people who receive the email)
#   - CC (cc'ed people)
#   - Subject (email subject)
#   - Body (email body)
#   - X-GM-THRID (unique thread identifier, compiles messages together into threads)
#   - Message-ID (unique id for this particular message)
#   - In-Reply-To (message ID of email you're responding to)


# column fields for hubspot
#   - email address (that connects to contact)
#   - Email Subject
#   - Email Body
#   - Email Direction
#   - any applicable custom properties

import re
import pandas as pd
from email.header import Header, decode_header, make_header

keys=['X-Gmail-Labels', 'Date', 'From', 'To', 'Cc', 'Subject', 'Body', 'X-GM-THRID', 'Message-ID', 'In-Reply-To']


def extractEmails(emailCol):
    # if cell is empty (NaN/null in pandas), skip cell
    if pd.isnull(emailCol):
        return

    # use regex to find all valid email strings within the 
    validEmails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', emailCol)

    # if multiple emails, should be delimited by ';' character as per hubspot formatting documentation
    return ";".join(validEmails)


def getDates(dateCol):
    # clean up date to be in format of: day.month.year hh:mm
    # current dates come into sheet with format of, e.g. "Fri, 15 Dec 2023 16:40:42 -0800"
    dateComponents = dateCol.split()
    newDate = f"{dateComponents[1]}.{dateComponents[2]}.{dateComponents[3]} {dateComponents[4][0:5]}"

    # update date
    return newDate


def getNonDomainEmails(fromData, toData, ccData):
    combinedData = list()

    # convert data into lists and only add non-insidemaps domain emails to final list
    if 'insidemaps' not in fromData:
        combinedData.append(fromData.rstrip())

    toData = toData.split(";")
    for address in toData:
        if 'insidemaps' not in address:
            combinedData.append(address.rstrip())

    if not pd.isnull(ccData):
        ccData = ccData.split(";")
        for address in ccData:
            if 'insidemaps' not in address:
                combinedData.append(address.rstrip())

    return combinedData

def main():
    # read input file for all data
    emails = pd.read_csv('./practice-mail.csv')

    # *******BEGIN CLEANING DATA*******

    # filter data only from specified key fields
    emails = emails[keys]

    # clean up "X-Gmail-Labels" to include only 'Incoming' (from 'Inbox') or 'Outgoing' (from 'Sent')
    emails['X-Gmail-Labels'] = emails['X-Gmail-Labels'].map(lambda x: 'Incoming' if 'Inbox' in x else 'Outgoing')

    # clean up date to be in format of: day.month.year hh:mm
    emails['Date'] = emails['Date'].map(lambda x: getDates(x))

    # clean up "To", "From", and "CC" fields to only include email, not name
    # can be multiple "To" and "CC" emails, should only have one "From"
    emails['To'] = emails['To'].map(lambda x: extractEmails(x))
    emails['From'] = emails['From'].map(lambda x: extractEmails(x))
    emails['Cc'] = emails['Cc'].map(lambda x: extractEmails(x))

    # *******START ASSIGNING ACTIVITY TO RELEVANT EMAILS/CONTACTS********

    # create and add values new column, values being a list of all relevant emails (non insidemaps domain) to later expand on
    emails['Activity-Assigned-To'] = ""
    for index, row in emails.iterrows():
        emails.at[index, 'Activity-Assigned-To'] = getNonDomainEmails(row['From'], row['To'], row['Cc'])
    
    # duplicate rows based on list within 'Activity-Assigned-To' using pd.explode
    # emails = emails.explode('Activity-Assigned-To')

    #   bug to fix; check line 168 on spreadsheet
    # decode email headers if they are encoded
    emails['Subject'] = emails['Subject'].map(lambda x: str(make_header(decode_header(x))))

    # drop all rows in which activity-assigned-to is NaN
    emails = emails[emails['Activity-Assigned-To'].notna()]

    # *******WRITE CLEANED DATA********

    # write cleaned and assigned data to output file
    emails.to_csv('./practice-output.csv', index=False)

if __name__ == "__main__":
    main()