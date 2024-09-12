"""
Command tasks can only be followed if in swarm
https://github.com/prateeknischal/webtail
"""
import io
import os
import os.path
import asyncio
import platform
import aiofiles
from shared.mods import hooks

TAGS = ['command']

async def _record_process(ctx, process, output_dir, attr):  
    stream = getattr(process, attr)
    file = f"{attr}.log"
    async with aiofiles.open(os.path.join(output_dir, file), 'wb') as fh:
        while True:
            line = await stream.readline()
            if line:
                print(line)
                # @todo hook for 
                ctx.hooks.action(f"process.{attr}.readline", process)
                await fh.write(line)
            else:
                break

SCHEMA = r"""
exec:
    type: array
    items: 
        type: string
    minItems: 1
env:
    type: object
timeout:
    type: integer
input:
    type: string
"""
async def task_async(ctx, exec=[], env={}, timeout=None, input=None):
    env = {**os.environ.copy(), **env}
    output_dir = ctx.workspace_path
    pid = None
    
    # @todo check if command exists
    if exec[0].startswith("/"):
        pass
    else:
        # check for command existence
    try:
        process = await asyncio.create_subprocess_exec(
            *exec,
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE,
            group=None, 
            user=None,
        )
        pid = process.pid
        print("Started: %s, pid=%s" % (exec, process.pid), flush=True)
    except Exception as err:
        return {
            'error': err,
        }

    hooks.action(f"process.started", process)

    await asyncio.wait([
        _record_process(ctx, process, output_dir, 'stdout'),
        _record_process(ctx, process, output_dir, 'stderr')
    ])

    exit_code = await process.wait()
    return {
        'pid': pid,
        'node': platform.node(),
        'system': platform.system(),
        'exec': exec,
        'exit_code': exit_code,
    }

