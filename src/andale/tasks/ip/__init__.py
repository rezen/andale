import sys
from ipwhois import IPWhois


TAGS = ["ip", "whois", "api", "api-external"]

SCHEMA = r"""
type: object
properties:
    ip:
        type: string
        anyOf:
            - format: ipv4
            - format: ipv6
        required: true
"""

CACHE = 1200  # How many seconds to cache result


def task(ip):
    entity = IPWhois(ip)
    return entity.lookup_rdap(depth=1)
