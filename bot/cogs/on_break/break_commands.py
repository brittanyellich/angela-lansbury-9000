from datetime import datetime, timezone, time
import asyncio
import calendar

import sentry_sdk
from nextcord import slash_command, Interaction, SlashOption, Member, TextChannel, Role
from nextcord.ext import commands, tasks

from bot.config import Config
from bot.utils.constants import TESTING_GUILD_ID
from bot.utils import messages
from db.helpers import on_break_helper, guild_config_helper


class BreakCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.post_break_status.start()

    # Every day at 5AM Pacific Time
    @tasks.loop(time=time(hour=12, minute=0, second=0, tzinfo=timezone.utc))
    async def post_break_status(self):
        if not self.bot.is_ready():
            return
        
        # Announce every X days someone has been on a break (30 maybe?)

    @post_break_status.error
    async def post_break_status_error(self, e):
        print(e)
        sentry_sdk.capture_exception(e)
        await asyncio.sleep(60)
        self.post_break_status.restart()

    ##############################
    # Admin Slash Commands
    ##############################

    @slash_command(name='break-admin',
                   description='Break admin commands',
                   guild_ids=[TESTING_GUILD_ID])
    async def break_admin(self, interaction: Interaction):
        pass

    @break_admin.subcommand(name='config', description='Configure break settings')
    async def break_config(self, interaction: Interaction,
                                on_break_role: Role = SlashOption(name='on_break_role', 
                                                                description='Role to set users to when they are on a break.')):
        if on_break_role is not None:
            config = guild_config_helper.update_guild_config(interaction.guild_id, break_role_id=on_break_role.id)
            if not config:
                return await interaction.send(f'An error occurred when updating the mod channel.')
        await interaction.send('Successfully updated break config!', ephemeral=True)
    
    @break_admin.subcommand(name='list', description='List of users currently on a break')
    async def on_break_list(self, interaction: Interaction):
        on_break_users = on_break_helper.list_on_break_users(interaction.guild_id)
        if len(on_break_users) == 0:
            # Search for users with the on break role and add them to "On Break"
            embed = messages.info(f'No users currently on a break')
            return await interaction.send(embed=embed, ephemeral=True)
        embed = messages.info(
            f'Current users on a break')
        guild = self.bot.get_guild(interaction.guild_id)
        if guild is None:
            return await interaction.send("Something weird happened", ephemeral=True)
        for user in on_break_users:
            member = guild.get_member(user[0].user_id)
            if member is None:
                # Can't find member, skip this user
                continue
            embed.add_field(name=member.display_name,
                            value=f'On break since: {user[0].went_on_break_at}')
        await interaction.send(embed=embed)

    @break_admin.subcommand(name='on', description='Send a user on a break')
    async def on_break_admin_add(self, interaction: Interaction,
                                user: Member = SlashOption(name='user', description='User to send on a break')):
        success = on_break_helper.add_user_on_break(interaction.guild_id, user.id)
        if not success:
            return await interaction.send(f'An error occurred when adding user to a break: {user.display_name}.', ephemeral=True)
        await interaction.send(f'Successfully added user to a break', ephemeral=True)

    @break_admin.subcommand(name='off', description='Remove a user from a break')
    async def on_break_admin_remove(self, interaction: Interaction,
                                user: Member = SlashOption(name='user', description='User to be removed from a break')):
        success = on_break_helper.remove_user_from_break(interaction.guild_id, user.id)
        if not success:
            return await interaction.send(f'An error occurred when removing user from a break: {user.display_name}.', ephemeral=True)
        await interaction.send(f'Successfully remove user from a break', ephemeral=True)

    ##############################
    # Regular Slash Commands
    ##############################

    @slash_command(name='break',
                   description='Break commands',
                   guild_ids=[TESTING_GUILD_ID])
    async def break_commands(self, interaction: Interaction):
        pass

    @break_commands.subcommand(name='on', description='Go on a break')
    async def on_break_add(self, interaction: Interaction):
        return await interaction.send('Not implemented yet', ephemeral=True)

    @break_commands.subcommand(name='off', description='Come back from a break')
    async def on_break_remove(self, interaction: Interaction):
        return await interaction.send('Not implemented yet', ephemeral=True)
