import sys
from traceback import print_tb
from typing import Optional
from string import Template
from discord import Guild, Member, TextChannel
from discord.ext.commands import Cog, Context, command, Bot
from dbclient import db


def setup(bot: Bot):
    bot.add_cog(Welcome(bot))


def teardown(bot: Bot):
    cog = bot.get_cog('Welcome')
    bot.remove_cog(cog)


def template_dict(member: Member):
    return {
        "user": member.mention,
        "display_name": member.display_name,
        "guild": member.guild.name
    }


class WelcomeSettings:
    guild_id: int
    channel_id: int
    template: Template

    def __init__(self, **kwargs):
        self.guild_id = kwargs.get('guild_id')
        self._message = kwargs.get('message', '')
        self.channel_id = kwargs.get('channel_id')

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, msg):
        self._message = msg
        self.template = Template(msg)

    def get_channel(self, guild: Guild) -> Optional[TextChannel]:
        return guild.get_channel(self.channel_id)

    def get_welcome_message(self, member: Member):
        return self.template.substitute(template_dict(member))

    def has_message(self):
        if len(self.message) > 0:
            return True
        return False

    async def post_welcome_message(self, member: Member):
        channel = self.get_channel(member)

        if channel and self.has_message():
            msg = self.get_welcome_message(member)
            await channel.send(msg)


class Welcome(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.welcome_collection = db.welcome
        self.settings = {
            post['guild_id']: WelcomeSettings(**post)
            for post in self.welcome_collection.find({})
        }

    @Cog.listener()
    async def on_member_join(self, member: Member):
        guild = member.guild
        welcome_setting = self.settings[guild.id]
        if not welcome_setting:
            return

        await welcome_setting.post_welcome_message(member)

    @command()
    async def view_welcome_message(self, ctx: Context):
        welcome_settings = self.settings[ctx.guild.id]

        if not welcome_settings or not welcome_settings.template:
            await ctx.send('No welcome message set yet!')
        else:
            await welcome_settings.post_welcome_message(ctx.author)

    @command()
    async def view_welcome_variables(self, ctx: Context):
        await ctx.send(
            '''These are the substitutions available in the welcome message.
               Use a $ prefix to indicate the substitution.
               Example: Welcome to $guild!''')

        msg = ""
        for k, v in template_dict(ctx.author).items():
            msg += f'${k} = {v}\n'

        await ctx.send(msg)

    def save_welcome_settings(self, ws: WelcomeSettings):
        self.welcome_collection.update_one({"guild_id": ws.guild_id}, {
            "$set": {
                "message": ws.message,
                "channel_id": ws.channel_id
            },
            "$setOnInsert": {
                "guild_id": ws.guild_id
            }
        })
        self.settings[ws.guild_id] = ws

    @command(rest_is_raw=True)
    async def set_welcome_message(self, ctx: Context, *, message: str):
        print(f'welcome message = {message}')
        welcome_setting = self.settings[ctx.guild.id]
        if not welcome_setting:
            welcome_setting = WelcomeSettings(guild_id=ctx.guild.id,
                                              message=message)
        try:
            welcome_setting.get_welcome_message(ctx.author)
            self.save_welcome_settings(welcome_setting)

            await ctx.send('Updated welcome message!\nPreview:\n')
            await ctx.send(self.m_make_welcome_messageake_welcome_message(ctx))

        except KeyError:
            err_value = sys.exc_info()[1]
            await ctx.send(f'{err_value} is an invalid substitution!')
        except:
            err_type, err_message, err_traceback = sys.exc_info()
            print(err_type)
            print(err_message)
            print_tb(err_traceback)
            await ctx.send('Something is wrong with the message provided!')
