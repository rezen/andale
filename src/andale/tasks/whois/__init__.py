import sys
import whois

TAGS = ["domain", "whois", "api", "api-external"]
CACHE = 1200  # How many seconds to cache result
SCHEMA = r"""
type: object
properties:
    domain:
        type: string
        format: hostname
required: 
    - domain
"""

RETURNS = r"""

"""


# @todo need a way to specify use local db record otherwise pull
# fresh copy
def task(domain):
    record = whois.whois(domain)
    return {a: record[a] for a in record}
