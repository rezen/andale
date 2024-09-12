import os
import io
import os.path
from libnmap.parser import NmapParser
from libnmap.reportjson import ReportEncoder
from tasks.command import task_async as exec

DEFAULT_PORTS = [
    "443",
    "80",
    "22",
    "3306",
]
TAGS = ["nmap", "network", "port-scan", "duration-medium"]

OPTIONS = r"""
hosts:
    type: list
    items:
        type: string
        anyOf:
            - format: ipv4
            - format: ipv6
            - format: hostname
args:
    type: list
    items:
        type: string

top_ports:
    type: integer
    default: 100

ports:
    type: list
    default: []
    items:
        type: string

scripts:
    type: list
    items:
        type: object
        properties:
            name: 
                type: string
            args:
                type: string
                default: ''
"""

RETURN = r"""
{
    "hosts":[
        {
            "address": "162.144.32.142",
            "status": "up",
            "hostnames": "ready2hire.org server.ready2hire.org",
            "mac_addr": null,
            "services": [
                {
                    "id": "tcp.21",
                    "port": "21",
                    "protocol": "tcp",
                    "banner": "product: Pure-FTPd",
                    "service": "ftp",
                    "state": "open",
                    "reason": "syn-ack",
                    "scripts": []
                }
            ]
        }
    ]
}
"""


async def task(ctx, hosts=[], ports=[22, 80, 443], top_ports=None, scripts=[]):
    command = [
        "nmap",
        "-sV",
    ]

    if top_ports:
        command = command + ["--top-ports", top_ports]

    if ports:
        # @todo ensure only numbers and ranges
        command = command + ["-p", ",".join(str(p) for p in ports)]

    # @todo verify hosts
    command = command + ",".join(hosts)

    if scripts:
        for script in scripts:
            args = None
            if isinstance(script, str):
                name = script
            else:
                # @todo sanitize name
                name = script.get("name")
                args = script.get("args")
            command = command + [f"--script={name}"]
    command = command + ["-oX", "-"]

    response = await exec(ctx, command)
    response.pop("stdout", None)
    response.pop("stderr", None)

    workspace = ctx.workspace_path
    with io.open(os.path.join(workspace, "stdout.log"), "r") as fh:
        data = NmapParser.parse(fh.read())

    results = []
    for host in data.hosts:
        tmp = {k: v for k, v in host.get_dict().items() if not k.startswith("Nmap")}
        tmp["services"] = [
            {**s.get_dict(), **{"scripts": s.scripts_results}} for s in host.services
        ]
        results.append(tmp)

    return {**{"hosts": results}, **response}
