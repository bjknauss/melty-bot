from dynaconf import settings

from discord.ext import commands
from discord.ext.commands import bot


class MeltyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))


melty_bot = MeltyBot(settings.COMMAND_PREFIX, owner=settings.OWNER)


@melty_bot.command(aliases=['reload', 'reload_exts'])
@commands.is_owner()
async def reload_all_extensions(ctx: commands.Context):  # pylint: disable=no-self-argument
    '''Reloads bot extensions.'''
    bot: MeltyBot = ctx.bot
    exts = [ext for ext in bot.extensions]
    failed = False

    for ext in exts:
        try:
            bot.reload_extension(ext)
        except Exception as e:
            failed = True
            print(f"Error while loading extension {ext}!")
            print(e)

    if not failed:
        await ctx.send(f'Reloaded {len(exts)} extensions.')
    else:
        await ctx.send('Something went wrong while loading extensions!')
