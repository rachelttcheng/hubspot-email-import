# simple rate limiter for api calls
# while hubspot says they're a 10 calls/sec rate limit, it isn't consistent and can hit limit even with rate of 5/sec,
# so 3 calls/sec is a safe bet

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