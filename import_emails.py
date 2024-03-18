# program that combines functionality of all subprograms here:
#
#   1. convert mbox file to csv (if mbox file extension) - ASSUME MBOX FOR NOW
#   2. clean up email data
#   3. api call to create emails
#
# program is called from command line as such:
#   % python3 import_emails.py <email file name>

# maybe look into argparse, https://docs.python.org/3/library/argparse.html

import sys
import subprocess
from filter_emails import cleanEmailData
from email_api import callEmailAPI

def main():
    # get emails file from command line
    if len(sys.argv) < 2:   # ensure enough arguments are passed
        raise AssertionError("Not enough arguments specified")

    rawEmailFilename = sys.argv[1]

    # 1. convert emails from mbox to json using mbox-to-json package
    subprocess.run(["mbox-to-json", rawEmailFilename, "-c"])

    # get name of outputted csv file for input to second step
    csvEmailFilename = rawEmailFilename.split(".")[0] + ".csv"

    print(f"\nMbox file converted to csv file type: {csvEmailFilename} - ready for data cleanup...\n")

    # 2. clean up email data
    # generate output file name, for input to third step
    cleanedDataFilename = csvEmailFilename.split('.')[0] + "-output.csv"
    cleanEmailData(csvEmailFilename, cleanedDataFilename)

    print("\nEmail data cleaned, ready to be written to database...\n")

    # 3. api call to create emails
    callEmailAPI(cleanedDataFilename)


if __name__ == "__main__":
    main()