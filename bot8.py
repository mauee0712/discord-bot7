import discord
from discord.ext import commands, tasks
import asyncio
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # disable default help

# In-memory warnings storage: {guild_id: {user_id: [reasons]}}
warnings_db = {}

# Helper to get role by name, mention, or ID
def get_role_by_argument(guild, role_arg):
    # By ID if digit
    if role_arg.isdigit():
        return guild.get_role(int(role_arg))
    # By mention format <@&ID>
    if role_arg.startswith("<@&") and role_arg.endswith(">"):
        role_id = role_arg[3:-1]
        if role_id.isdigit():
            return guild.get_role(int(role_id))
    # By name (case-insensitive)
    return discord.utils.find(lambda r: r.name.lower() == role_arg.lower(), guild.roles)

# ---------- COMMANDS ----------

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# Ban command
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"```✅ {member} has been banned.\nReason: {reason or 'No reason provided.'}```")
    except Exception as e:
        await ctx.send(f"```❌ Could not ban {member}.\nError: {e}```")

# Unban command
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user: str):
    banned_users = await ctx.guild.bans()
    name, discriminator = user.split("#")
    for ban_entry in banned_users:
        banned_user = ban_entry.user
        if (banned_user.name, banned_user.discriminator) == (name, discriminator):
            await ctx.guild.unban(banned_user)
            await ctx.send(f"```✅ Unbanned {banned_user}.```")
            return
    await ctx.send(f"```❌ User {user} not found in ban list.```")

# Kick command
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"```✅ {member} has been kicked.\nReason: {reason or 'No reason provided.'}```")
    except Exception as e:
        await ctx.send(f"```❌ Could not kick {member}.\nError: {e}```")

# Giverole command
@bot.command()
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, member: discord.Member, *, role_arg):
    role = get_role_by_argument(ctx.guild, role_arg)
    if not role:
        await ctx.send(f"```❌ Role `{role_arg}` not found.```")
        return
    try:
        await member.add_roles(role)
        await ctx.send(f"```✅ Given role `{role.name}` to {member}.```")
    except discord.Forbidden:
        await ctx.send("```❌ I don't have permission to assign that role.```")
    except Exception as e:
        await ctx.send(f"```❌ Error: {e}```")

# Takerole command
@bot.command()
@commands.has_permissions(manage_roles=True)
async def takerole(ctx, member: discord.Member, *, role_arg):
    role = get_role_by_argument(ctx.guild, role_arg)
    if not role:
        await ctx.send(f"```❌ Role `{role_arg}` not found.```")
        return
    try:
        await member.remove_roles(role)
        await ctx.send(f"```✅ Removed role `{role.name}` from {member}.```")
    except discord.Forbidden:
        await ctx.send("```❌ I don't have permission to remove that role.```")
    except Exception as e:
        await ctx.send(f"```❌ Error: {e}```")

# Mute command (adds 'muted' role, with optional duration in seconds)
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, seconds: int = None, *, reason=None):
    role = discord.utils.get(ctx.guild.roles, name="muted")
    if not role:
        await ctx.send("```❌ 'muted' role does not exist. Please create it first.```")
        return
    try:
        await member.add_roles(role, reason=reason)
        if seconds:
            await ctx.send(f"```✅ {member} has been muted for {seconds} seconds.\nReason: {reason or 'No reason provided.'}```")
            await asyncio.sleep(seconds)
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"```✅ {member} has been automatically unmuted after {seconds} seconds.```")
        else:
            await ctx.send(f"```✅ {member} has been muted indefinitely.\nReason: {reason or 'No reason provided.'}```")
    except Exception as e:
        await ctx.send(f"```❌ Could not mute {member}.\nError: {e}```")

# Unmute command
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="muted")
    if not role:
        await ctx.send("```❌ 'muted' role does not exist.```")
        return
    if role in member.roles:
        try:
            await member.remove_roles(role)
            await ctx.send(f"```✅ {member} has been unmuted.```")
        except Exception as e:
            await ctx.send(f"```❌ Could not unmute {member}.\nError: {e}```")
    else:
        await ctx.send(f"```⚠️ {member} is not muted.```")

# Announce command (send message to a specific channel)
@bot.command()
@commands.has_permissions(administrator=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
    try:
        await channel.send(f"📢 **Announcement:** {message}")
        await ctx.send(f"```✅ Announcement sent to {channel.mention}```")
    except Exception as e:
        await ctx.send(f"```❌ Could not send announcement.\nError: {e}```")

# Vanity command (change nickname)
@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def vanity(ctx, member: discord.Member, *, nickname):
    try:
        await member.edit(nick=nickname)
        await ctx.send(f"```✅ Changed nickname of {member} to '{nickname}'.```")
    except Exception as e:
        await ctx.send(f"```❌ Could not change nickname.\nError: {e}```")

# Warn command
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    guild_warns = warnings_db.setdefault(ctx.guild.id, {})
    user_warns = guild_warns.setdefault(member.id, [])
    user_warns.append(reason)
    await ctx.send(f"```⚠️ {member} has been warned.\nReason: {reason}\nTotal warnings: {len(user_warns)}```")

# Warnings command (show number of warnings)
@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    guild_warns = warnings_db.get(ctx.guild.id, {})
    user_warns = guild_warns.get(member.id, [])
    if user_warns:
        reasons = "\n".join(f"{i+1}. {r}" for i, r in enumerate(user_warns))
        await ctx.send(f"```⚠️ {member} has {len(user_warns)} warnings:\n{reasons}```")
    else:
        await ctx.send(f"```✅ {member} has no warnings.```")

# Roles command - lists all roles in the server (excluding @everyone)
@bot.command()
async def roles(ctx):
    roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    roles_list = ", ".join(roles) if roles else "No roles found."
    await ctx.send(f"```📋 Roles in this server:\n{roles_list}```")

# Giveaway command (simple timed giveaway)
giveaways = {}

@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx, seconds: int, *, prize):
    if seconds <= 0:
        await ctx.send("```❌ Duration must be greater than 0 seconds.```")
        return
    embed = discord.Embed(title="🎉 Giveaway!", description=f"Prize: {prize}\nReact with 🎉 to enter!", color=discord.Color.gold())
    giveaway_message = await ctx.send(embed=embed)
    await giveaway_message.add_reaction("🎉")

    giveaways[giveaway_message.id] = {
        "prize": prize,
        "host": ctx.author,
        "ended": False
    }

    await asyncio.sleep(seconds)

    giveaway_message = await ctx.channel.fetch_message(giveaway_message.id)  # Refresh message
    users = set()
    for reaction in giveaway_message.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if user != bot.user:
                    users.add(user)

    if users:
        winner = None
        try:
            winner = random.choice(list(users))
            await ctx.send(f"🎉 Congratulations {winner.mention}! You won the giveaway for **{prize}**!")
        except Exception:
            await ctx.send(f"🎉 Giveaway ended! No valid winner found.")
    else:
        await ctx.send("🎉 Giveaway ended! No one participated.")

    giveaways[giveaway_message.id]["ended"] = True

# Custom help command
bot.remove_command('help')

@bot.command()
async def help(ctx):
    help_text = """```
Available Commands:

!ban <member> [reason]           - Ban a member.
!unban <user#1234>               - Unban a user.
!kick <member> [reason]          - Kick a member.
!giverole <member> <role>        - Give a role to a member.
!takerole <member> <role>        - Remove a role from a member.
!mute <member> [seconds] [reason] - Mute a member with 'muted' role.
!unmute <member>                 - Unmute a member.
!announce <#channel> <message>   - Send an announcement.
!vanity <member> <nickname>      - Change a member's nickname.
!warn <member> [reason]          - Warn a member.
!warnings [member]               - Show warnings for a member.
!roles                          - List all roles in the server.
!giveaway <seconds> <prize>      - Start a giveaway.

Use commands responsibly!
```"""
    await ctx.send(help_text)
