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


import pandas as pd

keys=['X-Gmail-Labels', 'Date', 'From', 'To', 'Cc', 'Subject', 'Body', 'X-GM-THRID', 'Message-ID', 'In-Reply-To']


# *********TBD ON IF 'DELIVERED-TO' IS IMPORTANT FIELD****************

def extractEmails(emailCol):
    # if cell is empty (NaN/null in pandas), skip cell
    if pd.isnull(emailCol):
        return

    # first split data into email list
    contacts = emailCol.split(",")

    # loop through contacts and grab emails from in between "<" and ">" separators
    for i in range(len(contacts)):
        contacts[i] = contacts[i][contacts[i].find("<") + 1 : contacts[i].find(">")]
    
    # if multiple emails, should be delimited by ';' character as per hubspot formatting documentation
    return ";".join(contacts)


def getDates(dateCol):
    # clean up date to be in format of: day.month.year hh:mm
    # current dates come into sheet with format of, e.g. "Fri, 15 Dec 2023 16:40:42 -0800"
    dateComponents = dateCol.split()
    newDate = f"{dateComponents[1]}.{dateComponents[2]}.{dateComponents[3]} {dateComponents[4][0:5]}"

    # update date
    return newDate


# NEXT TO DO: NEED TO ASSIGN ACTIVITY TO A SPECIFIC CONTACT
# steps to take:
#   - create a new column "Activity-Assigned-To" and assign each instance of email data to all non-insidemaps emails involved

def getNonDomainEmails():
    return

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

    # *******END CLEANING DATA*******

    # *******START ASSIGNING ACTIVITY TO RELEVANT EMAILS/CONTACTS********

    #for index, row in emails.iterrows():

    # *******END ASSIGNING ACTIVITY TO RELEVANT EMAILS/CONTACTS********

    # write cleaned and assigned data to output file
    emails.to_csv('./practice-output.csv', index=False)

if __name__ == "__main__":
    main()