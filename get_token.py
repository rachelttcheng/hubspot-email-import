# fetches secure token located in separate txt file within same folder as program to be used for API calls

def fetchToken():

    with open('access-token.txt', 'r') as file:
        token = file.readline().strip()  # read first line and remove leading/trailing whitespace

    return token