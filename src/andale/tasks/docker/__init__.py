"""
Docker tasks can only be followed if in swarm
"""
import os
import os.path
import pathlib
import docker
import aiodocker
import asyncio
from docker.types import LogConfig
import platform
from shared.template import render_recursive
from shared.mods import hooks


client = docker.from_env()

TAGS = ["docker", "container", "api"]


def configure():
    pass


SCHEMA = r"""
---
name:
  type: string
image:
  type: string
  required: true
entrypoint:
  type: string
command:
  type: array
  items:
    type: string
  required: true
env:
  type: object
files:
  type: object
mount:
  type: object
"""


def task(
    self,
    image=None,
    command=None,
    entrypoint=None,
    name=None,
    env={},
    working_dir=None,
    files={},
    mount={},
):
    task_id = self.id
    workspace = self.workspace_path
    # @todo some containers have http endpoints for status/metrics
    config = {
        "image": image,
        "command": command,
        "entrypoint": entrypoint,
        "log_config": LogConfig(
            type=LogConfig.types.JSON,
            config={
                "max-size": "1g",
            },
        ),
        "auto_remove": False,
        "environment": env,
        "working_dir": "/data/workspace",
        "volumes": {
            "{{ data_dir }}/_mount/nuclei-templates": {
                "bind": "/root/nuclei-templates"
            },
            "{{ data_dir }}/_mount/wpscan": {"bind": "/wpscan/.wpscan/"},
            workspace: {
                "bind": "/data/workspace/",
            },
        },
        "labels": {
            "duration": "1h",
            "task_id": "{}".format(task_id),
        },
        "detach": True,
    }

    config = render_recursive(config, {})

    # Ensure local volumes exist
    for local in config.get("volumes", {}):
        pathlib.Path(os.path.dirname(local)).mkdir(parents=True, exist_ok=True)

    swarm = client.info().get("Swarm", {})
    node_id = swarm.get("NodeID")
    node_addr = swarm.get("NodeAddr")
    cluster_id = swarm.get("Cluster", {}).get("ID")

    try:
        config = hooks.filter("docker.config", config)
        container = client.containers.create(**config)
    except Exception as err:
        return {"error": err}

    container.start()
    cid = container.id
    hooks.action("docker.started", container.id)
    # Run while container is going
    # container.exec_run(cmd, stdout=True, stderr=True, stdin=False, tty=False, privileged=False, user='', detach=False, stream=False, socket=False, environment=None, workdir=None, demux=False)

    # Record output
    loop = asyncio.new_event_loop()
    loop.set_debug(True)
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        asyncio.wait(
            [
                _record_output(workspace, cid, stdout=True),
                _record_output(workspace, cid, stderr=True),
            ]
        )
    )
    loop.close()

    print("Waiting for container")
    details = container.wait()
    print("Container exited")
    container.remove()

    return {
        "cid": cid,
        "node": platform.node(),
        "system": platform.system(),
        "meta": {
            "node_id": node_id,
            "node_addr": node_addr,
            "cluster_id": cluster_id,
        },
        "exit_code": details["StatusCode"],
    }


async def _record_output(workspace, cid, **kwargs):
    channel = "stdout" if "stdout" in kwargs else "stderr"
    output = os.path.join(workspace, f"{channel}.log")
    docker = aiodocker.Docker()
    container = await docker.containers.get(cid)
    stream = container.log(
        stdout=("stdout" in kwargs), stderr=("stderr" in kwargs), logs=True, follow=True
    )

    fh = open(output, "w")
    try:
        async for log in stream:
            log = hooks.filter("docker.log", log, cid, channel)
            fh.write(log)
            print(log)
    except Exception as err:
        pass
    fh.close()
    await docker.close()


def teardown(env):
    pass
