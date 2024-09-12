import sys
import json
import hashlib
from urllib.parse import urlparse
import asyncio
import aiohttp

TAGS = ["http", "network"]

SCHEMA = r"""
url:
    type: string
    format: uri
    pattern: "https?:\/\/.*"
    required: true
    
method:
    type: string
    enum: [get, post, delete, put, head]
    default: get
    required: true
port:
    type: integer
data:
    type: string
headers:
    type: object
params: 
    type: object
"""


async def task(
    ctx,
    url=None,
    method="get",
    port=None,
    data=None,
    headers={},
    params=None,
    timeout=5,
):
    if isinstance(url, str):
        url = urlparse(url if url.startswith("http") else "https://{}".format(url))

    async with aiohttp.ClientSession() as session:
        async with session.request(
            method, url.geturl(), data=data, headers=headers, timeout=timeout
        ) as response:
            try:
                ip, port = response.connection.transport.get_extra_info("peername")
            except:
                ip, port = [None, None]

            text = await response.text()
            hash_of_body = "md5:" + hashlib.md5(str(text).encode()).hexdigest()
            # body_ref = ctx.storage.put("http." + hash_of_body, text)
            # ctx.artifacts.add_reference(body_ref)
            return {
                "method": method,
                "path": url.path,
                "port": port,
                "host": url.netloc,
                "data": data,
                "params": url.params,
                "ip": ip,
                "headers": dict(response.headers),
                "status_code": response.status,
                "redirects": len(response.history),
                "size": len(text),
                "hash_of_body": hash_of_body,
                "meta": {
                    "driver": "aiohttp",
                },
            }
