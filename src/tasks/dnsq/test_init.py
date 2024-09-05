from . import Input, task
import pytest


@pytest.mark.asyncio
async def test_task():
    res = await task({}, "mail.google.com", "txt")
    assert len(res) > 1