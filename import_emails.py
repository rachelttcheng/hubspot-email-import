# program that combines functionality of all subprograms here:
#
#   1. api call to create companies
#   2. api call to create contacts
#   3. convert mbox file to csv (if mbox file extension)
#   4. clean up email data
#   5. api call to create emails
#
# program is called from command line as such:
#   % python3 import_emails.py <contact file name/path> <email file name/path>

# maybe look into argparse, https://docs.python.org/3/library/argparse.html

import sys

def main():
    # get contacts and emails files from command line
    if len(sys.argv) < 4:   # ensure enough arguments are passed
        raise AssertionError("Not enough arguments specified")

    contactsFilename = sys.argv[2]
    emailsFilename = sys.argv[3]

    # determine file type of emails file and use mbox-to-json if necessary


    # api call to create companies


    # api call to create contacts


    # clean up email data


    # api call to create emails

if __name__ == "__main__":
    main()