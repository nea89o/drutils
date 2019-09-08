import ast
import os
import re

import discord
from discord import Embed, Color

REPLACEMENTS = {
    re.compile(r'<@!?(?P<id>[0-9]+)>'): '(guild.get_member({id}) if guild is not None else client.get_user({id}))',
    re.compile(r'<#(?P<id>[0-9]+)>'): '(discord.utils.get(all_channels, id={id}))',
    re.compile(r'<@&(?P<id>[0-9]+)>'): '(discord.utils.get(all_roles, id={id}))',

}


async def handle_eval(message: discord.Message, client: discord.Client, to_eval: str,
                      strip_codeblock: bool = False, **kwargs):
    channel = message.channel
    author = message.author

    all_channels = []
    all_roles = []
    for guild in client.guilds:
        all_channels += guild.channels
        all_roles += guild.roles

    variables = {
        'message': message,
        'author': author,
        'channel': channel,
        'all_channels': all_channels,
        'all_roles': all_roles,
        'client': client,
        'discord': discord,
        'os': os,
        'print': (lambda *text: client.loop.create_task(channel.send(' '.join(text)))),
        'guild': channel.guild if hasattr(channel, 'guild') else None,
    }
    variables.update(kwargs)

    lines = to_eval.strip().split('\n')
    if strip_codeblock:
        if lines[0].startswith("```"):
            lines = lines[1:]
            lines[-1] = ''.join(lines[-1].rsplit('```', 1))

    block = '\n'.join(' ' + line for line in lines)
    code = ("async def code({variables}):\n"
            "{block}").format(variables=', '.join(variables.keys()), block=block)

    for regex, replacement in REPLACEMENTS.items():
        code = re.sub(regex, lambda match: replacement.format(**match.groupdict()), code)

    try:
        module = ast.parse(code)
    except Exception as e:
        await message.channel.send(
            embed=Embed(color=Color.red(), description="Syntax Error: `%s`" % str(e)))
        return

    last = module.body[0].body[-1]
    if isinstance(last, ast.Expr):
        module.body[0].body[-1] = ast.copy_location(ast.Return(last.value), last)

    _globals, _locals = {}, {}
    try:
        code = compile(module, '<string>', 'exec')
        exec(code, _globals, _locals)
    except Exception as e:
        await message.channel.send(
            embed=discord.Embed(color=discord.Color.red(), description="Compiler Error: `%s`" % (str(e))))
        return
    result = {**_globals, **_locals}
    try:
        result = await result["code"](**variables)
    except Exception as e:
        await message.channel.send(
            embed=discord.Embed(color=discord.Color.red(), description="Runtime Error: `%s`" % (str(e))))
        return

    return await channel.send(
        embed=Embed(
            color=Color.red(),
            description="📥 Evaluation success: ```py\n%r\n```" % result))
