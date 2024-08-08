import discord
from discord.ext import commands
from discord.ext.commands import Cog
import datetime
import asyncio
import typing
import random
import emoji
from helpers.checks import ismod, isadmin, ismanager
from helpers.datafiles import add_userlog
from helpers.placeholders import random_msg
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, author_embed, mod_embed, quote_embed
import io
import re


class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.check_if_target_is_staff = self.check_if_target_is_staff
        self.bot.modqueue = {}

    def check_if_target_is_staff(self, target):
        return any(
            r
            == self.bot.pull_role(
                target.guild, get_config(target.guild.id, "staff", "modrole")
            )
            or r
            == self.bot.pull_role(
                target.guild, get_config(target.guild.id, "staff", "adminrole")
            )
            for r in target.roles
        )

    @commands.bot_has_permissions(kick_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["boot"])
    async def kick(self, ctx, target: discord.Member, *, reason: str = ""):
        """This kicks a user.

        Giving a `reason` will send the reason to the user.

        - `target`
        The target to kick.
        - `reason`
        The reason for the kick. Optional."""
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I cannot kick Staff members.")

        add_userlog(ctx.guild.id, target.id, ctx.author, reason, "kicks")

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"**You were kicked** from `{ctx.guild.name}`."
        if reason:
            dm_message += f'\n*The given reason is:* "{reason}".'
        dm_message += "\n\nYou are able to rejoin."
        failmsg = ""

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents kick issues in cases where user blocked bot
            # or has DMs disabled
            failmsg = "\nI couldn't DM this user to tell them."
            pass
        except discord.HTTPException:
            # Prevents kick issues on bots
            pass

        await target.kick(reason=f"[Kick peformed by {ctx.author} ] {reason}")
        await ctx.send(f"**{target.mention}** was KICKED.{failmsg}")

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command(aliases=["yeet"])
    async def ban(self, ctx, target: discord.User, *, reason: str = ""):
        """This bans a user.

        Giving a `reason` will send the reason to the user.

        - `target`
        The target to ban.
        - `reason`
        The reason for the ban. Optional."""
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            add_userlog(ctx.guild.id, target.id, ctx.author, reason, "bans")
        else:
            add_userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "bans",
            )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        failmsg = ""
        if ctx.guild.get_member(target.id) is not None:
            dm_message = f"**You were banned** from `{ctx.guild.name}`."
            if reason:
                dm_message += f'\n*The given reason is:* "{reason}".'
            dm_message += "\n\nThis ban does not expire"
            dm_message += (
                f", but you may appeal it here (although you must wait 2 weeks minimum before attempting to appeal):\n{get_config(ctx.guild.id, 'staff', 'appealurl')}"
                if get_config(ctx.guild.id, "staff", "appealurl")
                else "."
            )
            try:
                await target.send(dm_message)
            except discord.errors.Forbidden:
                # Prevents ban issues in cases where user blocked bot
                # or has DMs disabled
                failmsg = "\nI couldn't DM this user to tell them."
                pass
            except discord.HTTPException:
                # Prevents ban issues on bots
                pass

        await ctx.guild.ban(
            target, reason=f"[Ban performed by {ctx.author}] {reason}", delete_message_days=0
        )
        await ctx.send(f"**{target.mention}** is now BANNED.\n{failmsg}")

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["bandel"])
    async def dban(
        self, ctx, day_count: int, target: discord.User, *, reason: str = ""
    ):
        """This bans a user with X days worth of messages deleted.

        Giving a `reason` will send the reason to the user.

        - `day_count`
        The days worth of messages to delete.
        - `target`
        The target to kick.
        - `reason`
        The reason for the kick. Optional."""
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if day_count < 0 or day_count > 7:
            return await ctx.send(
                "Message delete day count must be between 0 and 7 days."
            )

        if reason:
            add_userlog(ctx.guild.id, target.id, ctx.author, reason, "bans")
        else:
            add_userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "bans",
            )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        failmsg = ""
        if ctx.guild.get_member(target.id) is not None:
            dm_message = f"**You were banned** from `{ctx.guild.name}`."
            if reason:
                dm_message += f'\n*The given reason is:* "{reason}".'
            appealmsg = (
                f", but you may appeal it here (although you must wait 2 weeks minimum before attempting to appeal):\n{get_config(ctx.guild.id, 'staff', 'appealurl')}"
                if get_config(ctx.guild.id, "staff", "appealurl")
                else "."
            )
            dm_message += f"\n\nThis ban does not expire{appealmsg}"
            try:
                await target.send(dm_message)
            except discord.errors.Forbidden:
                # Prevents ban issues in cases where user blocked bot
                # or has DMs disabled
                failmsg = "\nI couldn't DM this user to tell them."
                pass
            except discord.HTTPException:
                # Prevents ban issues on bots
                pass

        await target.ban(
            reason=f"[Ban performed by {ctx.author}] {reason}",
            delete_message_days=day_count,
        )
        await ctx.send(
            f"**{target.mention}** is now BANNED.\n{day_count} days of messages were deleted.\n{failmsg}"
        )

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def massban(self, ctx, *, targets: str):
        """This mass bans user IDs.

        You can get IDs with `pls dump` if they're banned from
        a different server with the bot. Otherwise, good luck.
        This won't DM them.

        - `targets`
        The target to ban."""
        msg = await ctx.send(f"**MASSBAN IN PROGRESS**")
        targets_int = [int(target) for target in targets.strip().split(" ")]

        for target in targets_int:
            target_user = await self.bot.fetch_user(target)
            target_member = ctx.guild.get_member(target)
            if target == ctx.author.id:
                await ctx.send(
                    random_msg("warn_targetself", authorname=ctx.author.name)
                )
                continue
            elif target == self.bot.user:
                await ctx.send(random_msg("warn_targetbot", authorname=ctx.author.name))
                continue
            elif target_member and self.check_if_target_is_staff(target_member):
                await ctx.send(f"(re: {target}) I cannot ban Staff members.")
                continue

            add_userlog(
                ctx.guild.id,
                target,
                ctx.author,
                f"Part of a massban. [[Jump]({ctx.message.jump_url})]",
                "bans",
            )

            await ctx.guild.ban(
                target_user,
                reason=f"[Ban performed by {ctx.author}] Massban",
                delete_message_days=0,
            )

        await msg.edit(content=f"All {len(targets_int)} users are now BANNED.")

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def unban(self, ctx, target: discord.User, *, reason: str = ""):
        """This unbans a user.

        The `reason` won't be sent to the user.

        - `target`
        The target to unban.
        - `reason`
        The reason for the unban. Optional."""

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.unban(target, reason=f"[Unban performed by {ctx.author}] {reason}")
        await ctx.send(f"{safe_name} is now UNBANNED.")

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["silentban"])
    async def sban(self, ctx, target: discord.User, *, reason: str = ""):
        """This bans a user silently.

        In this case, the `reason` will only be sent to the logs and not DMed to them.

        - `target`
        The target to ban.
        - `reason`
        The reason for the ban. Optional."""
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            add_userlog(ctx.guild.id, target.id, ctx.author, reason, "bans")
        else:
            add_userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "bans",
            )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.ban(
            target, reason=f"[Ban performed by {ctx.author}] {reason}", delete_message_days=0
        )
        await ctx.send(f"{safe_name} is now silently BANNED.")

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=["clear"])
    async def purge(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of messages.

        Please see the sister subcommands as well, in the [documentation](https://3gou.0ccu.lt/as-a-moderator/basic-functionality/#purging).
        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel
        if limit >= 1000000:
            return await ctx.reply(
                content=f"Your purge limit of `{limit}` is too high. Are you trying to `purge from {limit}`?",
                mention_author=False,
            )
        deleted = len(await channel.purge(limit=limit))
        await ctx.send(f"<a:bunnytrashjump:1256812177768185878> `{deleted}` messages purged.", delete_after=5)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command()
    async def bots(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of bot messages.

        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        def is_bot(m):
            return any((m.author.bot, m.author.discriminator == "0000"))

        deleted = len(await channel.purge(limit=limit, check=is_bot))
        await ctx.send(f"<a:bunnytrashjump:1256812177768185878> `{deleted}` bot messages purged.", delete_after=5)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command(name="from")
    async def _from(
        self,
        ctx,
        target: discord.User,
        limit=50,
        channel: discord.abc.GuildChannel = None,
    ):
        """This clears a given number of user messages.

        Defaults to 50 messages in the current channel. Max of one million.

        - `target`
        The user to purge messages from.
        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        def is_mentioned(m):
            return target.id == m.author.id

        deleted = len(await channel.purge(limit=limit, check=is_mentioned))
        await ctx.send(f"<a:bunnytrashjump:1256812177768185878> `{deleted}` messages from {target} purged.", delete_after=5)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command(name="with")
    async def _with(
        self,
        ctx,
        string: str,
        limit=50,
        channel: discord.abc.GuildChannel = None,
    ):
        """This clears a given number of specific messages.

        Defaults to 50 messages in the current channel. Max of one million.

        - `string`
        Messages containing this will be deleted.
        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        def contains(m):
            return string in m.content

        deleted = len(await channel.purge(limit=limit, check=contains))
        await ctx.send(
            f"<a:bunnytrashjump:1256812177768185878> `{deleted}` messages containing `{string}` purged.", delete_after=5
        )

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command(aliases=["emoji"])
    async def emotes(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of emotes.

        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of emotes to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        emote_re = re.compile(r":[A-Za-z0-9_]+:", re.IGNORECASE)

        def has_emote(m):
            return any(
                (
                    emoji.emoji_count(m.content),
                    emote_re.findall(m.content),
                )
            )

        deleted = len(await channel.purge(limit=limit, check=has_emote))
        await ctx.send(f"<a:bunnytrashjump:1256812177768185878> `{deleted}` emotes purged.", delete_after=5)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command()
    async def embeds(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of messages with embeds.

        This includes stickers, by the way, but not emoji.
        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        def has_embed(m):
            return any((m.embeds, m.attachments, m.stickers))

        deleted = len(await channel.purge(limit=limit, check=has_embed))
        await ctx.send(f"<a:bunnytrashjump:1256812177768185878> `{deleted}` embeds purged.", delete_after=5)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command(aliases=["reactions"])
    async def reacts(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of reactions.

        This does NOT delete their messages! Just the reactions!
        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of reactions to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        deleted = 0
        async for msg in channel.history(limit=limit):
            if msg.reactions:
                deleted += 1
                await msg.clear_reactions()
        await ctx.send(f"<a:bunnytrashjump:1256812177768185878> `{deleted}` reactions purged.", delete_after=5)

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["slow"])
    async def slowmode(self, ctx, channel: discord.abc.GuildChannel = None, seconds: int = 5):
        """This makes the bot set a channel's slowmode.
        
        - `channel`
        The channel to manage slowmode for. Optional, will target to the current channel by default.
        - `seconds`
        The time (in seconds) to set slowmode for. Optional, will be five seconds by default."""
        if not channel:
            channel = ctx.channel
        success = await channel.edit(slowmode_delay=seconds)

        if success and seconds > 1:
            return ctx.reply(f"Slowmode set succesfully in {channel} to {seconds} seconds(s).")
        elif success and seconds == 0:
            return ctx.reply(f"Slowmode disabled in {channel}.")
        
    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command(aliases=["send"])
    async def speak(
        self,
        ctx,
        channel: discord.abc.GuildChannel,
        text: str,
    ):
        """This makes the bot repeat some text in a specific channel.

        If you manage the bot, it can even run commands.

        - `channel`
        The channel to post the text in.
        - `text`
        The text to repeat."""
        output = await channel.send(text)
        if ctx.author.id in self.bot.config.managers:
            output.author = ctx.author
            newctx = await self.bot.get_context(output)
            newctx.message.author = ctx.guild.me
            await self.bot.invoke(newctx)
        await ctx.reply("👍", mention_author=False)

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command()
    async def reply(
        self,
        ctx,
        message: discord.Message,
        *,
        text: str,
    ):
        """This makes the bot reply to a message.

        If you manage the bot, it can even run commands.

        - `message`
        The message to reply to. Message link preferred.
        - `text`
        The text to repeat."""
        output = await message.reply(content=f"{text}", mention_author=False)
        if ctx.author.id in self.bot.config.managers:
            output.author = ctx.author
            newctx = await self.bot.get_context(output)
            newctx.message.author = ctx.guild.me
            await self.bot.invoke(newctx)
        await ctx.reply("👍", mention_author=False)

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command()
    async def react(
        self,
        ctx,
        message: discord.Message,
        emoji: str,
    ):
        """This makes the bot react to a message with an emoji.

        It can't react with emojis it doesn't have access to.

        - `message`
        The message to reply to. Message link preferred.
        - `emoji`
        The emoji to react with."""
        emoji = discord.PartialEmoji.from_str(emoji)
        await message.add_reaction(emoji)
        await ctx.reply("👍", mention_author=False)

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command()
    async def typing(
        self,
        ctx,
        channel: discord.abc.GuildChannel,
        duration: int,
    ):
        """This makes the bot type in a channel for some time.

        There's not much else to it.

        - `channel`
        The channel or thread to type in.
        - `duration`
        The length of time to type for."""
        await ctx.reply("👍", mention_author=False)
        async with channel.typing():
            await asyncio.sleep(duration)


async def setup(bot):
    await bot.add_cog(Mod(bot))
