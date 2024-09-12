import json
import sys
import dns.asyncquery
import dns.asyncresolver
import dns.message

import dns.rdatatype
import dns.rdataclass
import asyncio
from pydantic import BaseModel, Field, constr
from typing import Literal, Dict, List, get_args

TAGS = ["dns", "domain", "network"]

RECORD_TYPES = Literal[
    "a", "cname", "mx", "ns", "ptr", "soa", "srv", "txt", "any", "caa"
]


class Input(BaseModel):
    domain: str = Field(pattern=r"^[a-zA-Z0-9.-]+$")
    rtype: RECORD_TYPES = Field(default="a")
    name_server: str = Field(pattern=r"^[a-zA-Z0-9.-]+$", default="8.8.8.8")


SCHEMA = r"""
domain:
    type: string
    required: true
    format: hostname
rtype:
    type: string
    required: true
    default: a
    enum:
        - a
        - cname
        - mx
        - ns
        - ptr
        - soa
        - srv
        - txt
        - any
        - caa
name_server:
    type: string
    format: ip-address
"""


async def task(ctx, domain, rtype="a", name_server="8.8.8.8"):
    rtype = rtype.lower()
    # A nicetie to get all the records
    if rtype == "all":
        tasks = [task(ctx, domain, o, name_server) for o in get_args(RECORD_TYPES)]
        return [r for r in await asyncio.gather(*tasks) if r]

    if rtype.lower() not in get_args(RECORD_TYPES):
        rtype = "ANY"

    print(domain, rtype, name_server)

    ADDITIONAL_RDCLASS = 65535
    request = dns.message.make_query(
        domain, dns.rdatatype.from_text(rtype.upper() if rtype else "ANY")
    )
    request.flags |= dns.flags.AD
    request.find_rrset(
        request.additional,
        dns.name.root,
        ADDITIONAL_RDCLASS,
        dns.rdatatype.OPT,
        create=True,
        force_unique=True,
    )

    response = await dns.asyncquery.udp(request, name_server)
    results = []
    for reply in response.answer:
        for rd in reply:
            answer = {attr: getattr(rd, attr) for attr in type(rd).__slots__}
            answer["type"] = dns.rdatatype.to_text(reply.rdtype)
            results.append(answer)
    return results
