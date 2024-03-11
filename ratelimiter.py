# simple rate limiter for api calls
# while hubspot says they're a 10 calls/sec rate limit, it isn't consistent
# so <=5 calls/sec is a safe bet, adjust as needed
# typically 4 for companies, 3 for contacts and email

from ratelimit import limits, sleep_and_retry

# rate limiter info (calls per second)
CALLS = 3
RATE_LIMIT = 1

# empty function just to check for calls to API (wrappers)
@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
def checkLimit():
    ''' Empty function just to check for calls to API '''
    return