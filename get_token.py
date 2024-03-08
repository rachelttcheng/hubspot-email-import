def fetchToken():

    with open('access-token.txt', 'r') as file:
        token = file.readline().strip()  # read first line and remove leading/trailing whitespace

    return token