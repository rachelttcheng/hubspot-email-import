# simple rate limiter for api calls

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