from os import environ

from discord.ext.commands import Bot, Greedy, MemberConverter

from drutils import non_nullable

bot = Bot(command_prefix="!")


@bot.command()
async def converter_test(ctx, members: Greedy[non_nullable(MemberConverter)]):
    await ctx.send('\n'.join(member.name for member in members))


if __name__ == '__main__':
    bot.run(environ['TOKEN'])
