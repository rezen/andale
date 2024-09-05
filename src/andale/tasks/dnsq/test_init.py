from andale.tasks.dnsq import Input, task
import pytest


@pytest.mark.asyncio()
async def test_task():
    res = await task({}, "sendgrid.com", "txt")
    assert len(res) > 1
    assert res[0]['type'] == "TXT"
