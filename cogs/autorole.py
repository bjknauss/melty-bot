from asyncio import sleep
import discord
from discord import Role, Guild, Member
from discord.ext.commands import Cog, Context, command, Greedy, Bot
from dbclient import db
from discord.ext import tasks
from discord.ext.tasks import Loop


def setup(bot: Bot):
    bot.add_cog(Autorole(bot))


def teardown(bot: Bot):
    cog = bot.get_cog('Autorole')
    cog.fix_autoroles_task.cancel()
    bot.remove_cog(cog)


class Autorole(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autorole_collection = db.autorole

        self.autoroles = {
            post['guild_id']: post['roles']
            for post in self.autorole_collection.find({})
        }

        self.fix_autoroles_task.start()  # pylint: disable=no-member

    def get_autoroles(self, guild: Guild):
        return [
            guild.get_role(role_id) for role_id in self.autoroles[guild.id]
        ]

    @Cog.listener()
    async def on_member_join(self, member: Member):
        roles = self.get_autoroles(member.guild)
        await member.add_roles(*roles,
                               reason="Autoroles added on member join.")

    @tasks.loop(hours=6.0)
    async def fix_autoroles_task(self):
        guilds = self.bot.guilds

        for guild in guilds:
            print(f"Fixing {guild.name} autoroles...")
            fixed_roles = await self.fix_autoroles_by_guild(guild)
            if len(fixed_roles) > 0:
                print(f'Fixed {len(fixed_roles)} in guild {guild.name}!')

    @fix_autoroles_task.before_loop
    async def before_fix_autoroles_task(self):
        await self.bot.wait_until_ready()

    @command()
    async def fix_autoroles(self, ctx: Context):
        fixed_roles = await self.fix_autoroles_by_guild(ctx.guild)

        await ctx.send(f"Fixed roles for {len(fixed_roles)} members!")

    async def fix_autoroles_by_guild(self, guild: Guild):
        roles = self.get_autoroles(guild)
        missing_roles = {
            member: [role for role in roles if role not in member.roles]
            for member in guild.members if not member.bot
        }
        missing_roles = {k: v for k, v in missing_roles.items() if len(v) > 0}

        for member, roles in missing_roles.items():
            await member.add_roles(*roles, reason="Fixing missed autoroles.")

        print(f"Fixed roles for {len(missing_roles)} members!")
        return missing_roles

    @command()
    async def list_autoroles(self, ctx):
        roles = [
            ctx.guild.get_role(role_id).name
            for role_id in self.autoroles[ctx.guild.id]
        ]
        await ctx.send('Current roles: {0}'.format(", ".join(roles)))

    @command()
    async def add_autoroles(self, ctx, roles: Greedy[Role]):
        guild_id = ctx.guild.id
        role_ids = [
            role.id for role in roles
            if role.id not in self.autoroles[guild_id]
        ]
        for role_id in role_ids:
            self.autoroles[guild_id].append(role_id)
        self.autorole_collection.update_one(
            {"guild_id": guild_id},
            {"$addToSet": {
                "roles": {
                    "$each": role_ids
                }
            }})
        print('Updated autoroles: {0}'.format(self.autoroles))
        await ctx.send('Added {0} roles!'.format(len(role_ids)))

    @command()
    async def remove_autoroles(self, ctx, roles: Greedy[Role]):
        guild_id = ctx.guild.id
        role_ids = [
            role.id for role in roles if role.id in self.autoroles[guild_id]
        ]
        self.autoroles[guild_id] = [
            role for role in self.autoroles[guild_id] if role not in role_ids
        ]

        self.autorole_collection.update_one(
            {"guild_id": guild_id}, {"$pull": {
                "roles": {
                    "$in": role_ids
                }
            }})

        print('Updated autoroles: {0}'.format(self.autoroles))
        await ctx.send(f'Removed {len(role_ids)} roles!')
