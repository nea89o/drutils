import asyncio
import inspect
import string
from collections import defaultdict
from typing import Any, Optional, List

import discord
from discord import Message, Guild, PartialEmoji, Embed, Color, Reaction, User, Role, TextChannel
from discord.abc import Messageable
from discord.ext.commands import Bot, Paginator, Context

_NoneType = type(None)


async def await_if(func, *args, **kwargs):
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


def keeper(keep):
    table = defaultdict(_NoneType)
    table.update({ord(c): c for c in keep})
    return table


NUMBER_EMOJIS = [str(num) + '\U000020e3' for num in range(1, 10)] + ['\U0001f51f']
digit_keeper = keeper(string.digits)
YES_ANSWERS = ['yes', 'y']
NO_ANSWERS = ['n', 'no']
YES_REACTION = '\N{WHITE HEAVY CHECK MARK}'
NO_REACTION = '\N{CROSS MARK}'


class AwaitException(BaseException):
    pass


class AwaitCanceled(AwaitException):
    pass


class AwaitTimedOut(AwaitException):
    pass


class AdvancedAwaiter:
    def __init__(self, bot: Bot, channel: Messageable, guild: Optional[Guild], user: User, timeout: Optional[int]):
        self.bot = bot
        self.channel = channel
        self.guild = guild
        self.author = user
        self.timeout = timeout

    @classmethod
    def from_context(cls, ctx: Context, timeout: Optional[int] = None):
        return cls(ctx.bot, ctx.channel, ctx.guild, ctx.author, timeout)

    @classmethod
    def from_message(cls, bot: Bot, mes: Message, timeout: Optional[int] = None):
        return cls(bot, mes.channel, mes.guild, mes.author, timeout)

    @classmethod
    def in_direct_message(cls, bot: Bot, user: User, timeout: Optional[int] = None):
        return cls(bot, user, None, user, timeout)

    def check_author(self, mes: Message):
        if mes.author.id != self.author.id:
            return False
        return mes.channel == self.channel or (self.guild is None and mes.guild is None)

    async def by_converter(self, text, check, converter) -> Any:
        obj = None
        while obj is None or not await await_if(check, obj):
            try:
                res = await self(text)
                obj = await await_if(converter, res)
            except AwaitException:
                raise
            except BaseException as e:
                print(e)
        return obj

    async def __call__(self, text, check=lambda mes: True) -> Message:
        await self.channel.send(
            embed=Embed(
                color=Color.blurple(),
                description=text))

        try:
            mes = await self.bot.wait_for('message', check=lambda mes: self.check_author(mes) and check(mes),
                                          timeout=self.timeout)
            if mes.content.lower() == "@cancel@":
                raise AwaitCanceled
            return mes
        except asyncio.TimeoutError:
            raise AwaitTimedOut

    async def converted_emoji(self, text: str, converter=lambda x: x, check=lambda x: True):
        thing = None
        while thing is None or not check(thing):
            try:
                ret = await self.emoji_reaction(text)
                thing = await await_if(converter, ret)
            except AwaitException:
                raise
            except BaseException as e:
                print(e)
        return thing

    async def emoji_reaction(self, text: str) -> PartialEmoji:
        mes = await self.channel.send(
            embed=Embed(
                color=Color.blurple(),
                description=text))

        def check(reaction: Reaction, user: User):
            message = reaction.message
            if self.author.id != user.id:
                return False
            return mes.id == message.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=self.timeout)
            return reaction
        except asyncio.TimeoutError:
            raise AwaitTimedOut

    async def guild_role(self, text: str, check=lambda role: True, list_ids=False) -> Role:
        async def converter(mes: Message):
            return discord.utils.get(self.guild.roles,
                                     id=int(mes.content.translate(digit_keeper)))

        if list_ids:
            guild = self.guild
            paginator = Paginator()
            for role in guild.roles:
                paginator.add_line(role.name + ' ' + str(role.id))

            for page in paginator.pages:
                await self.channel.send(
                    embed=Embed(
                        color=Color.blurple(),
                        description=page))
        return await self.by_converter(
            text,
            check=check,
            converter=converter)

    async def emoji_choice(self, text: str, choices: List[str]):
        emoji = ''
        while emoji not in choices:
            mes = await self.channel.send(
                embed=Embed(
                    color=Color.blurple(),
                    description=text))
            for choice in choices:
                await mes.add_reaction(choice)

            def check(reaction: Reaction, user: User):
                message = reaction.message
                if user.id != self.author.id:
                    return False
                return message.id == mes.id

            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=self.timeout)
                emoji = str(reaction.emoji)
            except asyncio.TimeoutError:
                raise AwaitTimedOut
        return emoji

    async def choice(self, text: str, choices: List[Any]):
        emojis = NUMBER_EMOJIS[:len(choices)]
        emoji = await self.emoji_choice(text + '\n' + '\n'.join(
            map(' '.join, zip(choices, emojis))
        ), emojis)
        return choices[emojis.index(emoji)]

    async def emoji_yes_no(self, text: str) -> bool:
        emoji = await self.emoji_choice(text, [YES_REACTION, NO_REACTION])
        return emoji == YES_REACTION

    async def text(self, text: str):
        return (await self(text)).content

    async def guild_channel(self, text: str, check=lambda channel: True, writable=False) -> object:
        async def converter(mes: Message):
            return discord.utils.get(self.guild.channels,
                                     id=int(mes.content.translate(digit_keeper)))

        async def all_checks(channel: TextChannel):
            if writable and not channel.permissions_for(self.bot.user).send_messages:
                return False
            return await await_if(check, channel)

        return await self.by_converter(
            text,
            check=all_checks,
            converter=converter)

    async def as_message(self, text: str, check=lambda mes: True, in_channel: TextChannel = None) -> Message:
        if in_channel is None:
            in_channel = self.channel

        async def converter(mes: Message):
            return await in_channel.get_message(mes.content)

        return await self.by_converter(text, check=check, converter=converter)

    async def yes_no_question(self, text: str) -> bool:
        response = ''
        while response not in (YES_ANSWERS + NO_ANSWERS):
            response = (await self.text(text)).lower()
            pass
        return response in YES_ANSWERS
