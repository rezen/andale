""" 
Some sample payloads
payload = "info\r\nquit\r\n"
payload = "480000000200000000000000d40700000000000061646d696e2e24636d6400000000000100000021000000026765744c6f670010000000737461727475705761726e696e67730000"
payload = "3a000000a741000000000000d40700000000000061646d696e2e24636d640000000000ffffffff130000001069736d6173746572000100000000"
payload = "envi\r\nquit\r\n" # 2181
"""  
import asyncio


TAGS = ['ip', 'tcp']

SCHEMA = r"""
host:
    type: string
    oneOf:
        - format: ip-address
        - format: hostname
port:
    type: integer

timeout:
    type: integer
"""

async def task(host, port, payload, encode=None, read_bytes=100, timeout=5):
    if encode in ["hex"]:
        payload = bytes.fromhex(payload)

    try:
        reader, writer = await asyncio.open_connection(host, port)
    except Exception as err:
        return {'error': str(err)}
    
    try:
        writer.write(payload.encode())
        await writer.drain()
    except Exception as err:
        return {'error': str(err)}

    # https://docs.python.org/3/library/asyncio-protocol.html#asyncio.BaseTransport.get_extra_info
    address = writer.get_extra_info('peername')
    print(writer.get_extra_info('peercert'))
    data = await reader.read(read_bytes)    
    writer.close()

    await writer.wait_closed()
    return {
        "address": address[0:2] if address else None,
        "response": data.decode()
    }


