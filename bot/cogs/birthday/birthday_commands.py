from datetime import datetime, timezone, time
import asyncio

import sentry_sdk
from nextcord import slash_command, Interaction, SlashOption, Member, TextChannel
from nextcord.ext import commands, tasks

from bot.utils import messages
from db.helpers import birthday_helper


class BirthdayCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.post_birthdays.start()

    # Every day at 5AM Pacific Time
    @tasks.loop(time=time(hour=12, minute=0, second=0, tzinfo=timezone.utc))
    async def post_birthdays(self):
        if not self.bot.is_ready():
            return

        birthdays_by_guild_id = birthday_helper.get_todays_birthdays()
        for guild_id, birthdays in birthdays_by_guild_id.items():
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                # Can't find guild, skip posting these birthdays
                continue
            birthday_channel_id = birthday_helper.get_birthday_channel_id(guild_id)
            if birthday_channel_id is None:
                # No birthday channel set, skip posting these birthdays
                continue
            channel = self.bot.get_channel(birthday_channel_id)
            if channel is None:
                # Can't find channel, skip posting these birthdays
                continue
            # Assemble birthday message
            message = messages.birthday_message()
            for birthday in birthdays:
                member = guild.get_member(birthday.user_id)
                if member is None:
                    # Can't find member, skip this birthday
                    continue
                message = messages.birthday_entry(message, birthday, member)
            message = messages.get_special_birthday_fields(message)
            await channel.send(embed=message)

    @post_birthdays.error
    async def post_birthdays_error(self, e):
        print(e)
        sentry_sdk.capture_exception(e)
        await asyncio.sleep(60)
        self.post_birthdays.restart()

    ##############################
    # Admin Slash Commands
    ##############################

    @slash_command(name='birthday-admin',
                   description='Birthday commands')
    async def birthday_admin(self, interaction: Interaction):
        pass

    @birthday_admin.subcommand(name='config', description='Configure birthday settings')
    async def birthday_config(self, interaction: Interaction,
                              channel: TextChannel = SlashOption(name='channel',
                                                                 description='Channel to post birthday messages in.')):
        success = birthday_helper.update_settings(interaction.guild_id, channel.id)
        if not success:
            return await interaction.send(f'An error occurred when updating birthday settings.', ephemeral=True)
        await interaction.send('Successfully updated birthday settings!', ephemeral=True)

    ##############################
    # Regular Slash Commands
    ##############################

    @slash_command(name='birthday',
                   description='Birthday commands',
                   force_global=True)
    async def birthday(self, interaction: Interaction):
        pass

    @birthday.subcommand(name='add', description='Add a birthday')
    async def birthday_add(self, interaction: Interaction,
                           name: str = SlashOption(name='name', description='Name of person celebrating a birthday'),
                           date: str = SlashOption(name='date', description='Date of birthday (YYYY/MM/DD)')):
        # Get date from added date, validate, and add to the database. Return an error if the name already exists or the date is invalid.
        try:
            dt = datetime.strptime(date, '%Y/%m/%d')
            success = birthday_helper.add_birthday(interaction.guild_id, interaction.user.id, name.lower(), dt.month,
                                                   dt.day, dt.year)
            if success:
                await interaction.send(f'Birthday added: `{name} | {dt.strftime("%b %d, %Y")}`', ephemeral=True)
            else:
                await interaction.send(f'Birthday already exists for {name.title()}. '
                                       f'Try a different name, or remove the existing birthday first.',
                                       ephemeral=True)
        except ValueError:
            return await interaction.send('Please provide a date in the format YYYY/MM/DD', ephemeral=True)

    @birthday.subcommand(name='list', description='List birthdays')
    async def birthday_list(self, interaction: Interaction,
                            user: Member = SlashOption(name='user',
                                                       description='User to list birthdays for.'), ):
        birthdays = birthday_helper.list_birthdays(interaction.guild_id, user.id)
        if len(birthdays) == 0:
            embed = messages.info(f'No stored birthdays found for {user.name}. Use `/birthday add` to add a birthday.')
            icon_url = user.avatar.url if user.avatar else None
            embed.set_author(name=user.name, icon_url=icon_url)
            return await interaction.send(embed=embed, ephemeral=True)
        embed = messages.info(
            f'Current birthdays stored for {user.name}. Use `/birthday remove` to remove a stored birthday.')
        icon_url = user.avatar.url if user.avatar else None
        embed.set_author(name=user.name, icon_url=icon_url)
        for birthday in birthdays:
            embed.add_field(name=birthday[0].name.title(),
                            value=f'{birthday[0].month}/{birthday[0].day}/{birthday[0].year}')
        await interaction.send(embed=embed)

    @birthday.subcommand(name='remove', description='Remove a birthday')
    async def birthday_remove(self, interaction: Interaction,
                              name: str = SlashOption(name='name', description='Name of birthday to remove')):
        success = birthday_helper.delete_birthday(interaction.guild_id, interaction.user.id, name.lower())
        if not success:
            return await interaction.send(f'An error occurred when deleting birthday {name.title()} '
                                          f'associated with user {interaction.user.display_name}.', ephemeral=True)
        await interaction.send('Successfully deleted birthday!', ephemeral=True)
