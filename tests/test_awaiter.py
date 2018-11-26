from unittest.mock import ANY

from aiounittest import AsyncTestCase
from discord import Object

from drutils.awaiter import AdvancedAwaiter
from .utils import get_mock_coro

TEST_TEXT = "ABCDEF"
TEST_RESPONSE = "DEFABC"
TEST_MESSAGE_ID = 3
TEST_USER_ID = 2
TEST_CHANNEL_ID = 1
TEST_TIMEOUT = 100


class AwaiterTest(AsyncTestCase):

    def setUp(self):
        super().setUp()
        self.ctx = Object(id=0)
        self.bot = Object(id=0)
        self.message = Object(id=TEST_MESSAGE_ID)
        self.message.content = TEST_RESPONSE
        self.user = Object(id=TEST_USER_ID)
        self.message.author = self.user
        self.bot.wait_for = get_mock_coro(self.message)
        self.channel = Object(id=TEST_CHANNEL_ID)
        self.channel.send = get_mock_coro(None)
        self.ctx.bot = self.bot
        self.ctx.channel = self.channel
        self.ctx.guild = None
        self.ctx.author = self.user

    async def test_text(self):
        awaiter = AdvancedAwaiter.from_context(self.ctx, timeout=TEST_TIMEOUT)
        text = await awaiter.text(TEST_TEXT)
        self.assertEqual(text, TEST_RESPONSE)
        self.bot.wait_for.assert_called_once_with('message', check=ANY, timeout=TEST_TIMEOUT)
        self.assertEqual(self.channel.send.call_args[1]['embed'].description, TEST_TEXT)
