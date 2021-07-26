import boto3
import json

# @todo wrapper has callback
def task(self, name, payload, **kwargs):
    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName=name,
        InvocationType='Event',
        LogType='None',
        Payload=json.dump(payload, default=str),
    )

def install(env):
    pass

def teardown(env):
    pass

def configure():
    pass
    # specify subnets regions, account, etc
