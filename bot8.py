import discord
from discord.ext import commands
import asyncio
import random
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

warnings_db = {}

def get_role_by_argument(guild, role_arg):
    if role_arg.isdigit():
        return guild.get_role(int(role_arg))
    if role_arg.startswith("<@&") and role_arg.endswith(">"):
        role_id = role_arg[3:-1]
        if role_id.isdigit():
            return guild.get_role(int(role_id))
    return discord.utils.find(lambda r: r.name.lower() == role_arg.lower(), guild.roles)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"```✅ | Banned 🚫 {member} | Reason: {reason or 'No reason provided.'}```")
    except Exception as e:
        await ctx.send(f"```❌ | Failed to ban {member} | Error: {e}```")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user: str):
    banned_users = await ctx.guild.bans()
    try:
        name, discriminator = user.split("#")
    except Exception:
        await ctx.send("```❌ | Invalid user format! Use Name#1234```")
        return
    for ban_entry in banned_users:
        banned_user = ban_entry.user
        if (banned_user.name, banned_user.discriminator) == (name, discriminator):
            await ctx.guild.unban(banned_user)
            await ctx.send(f"```✅ | Unbanned ✅ {banned_user}```")
            return
    await ctx.send(f"```❌ | User {user} not found in ban list.```")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"```✅ | Kicked 👢 {member} | Reason: {reason or 'No reason provided.'}```")
    except Exception as e:
        await ctx.send(f"```❌ | Failed to kick {member} | Error: {e}```")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, member: discord.Member, *, role_arg):
    role = get_role_by_argument(ctx.guild, role_arg)
    if not role:
        await ctx.send(f"```❌ | Role `{role_arg}` not found.```")
        return
    try:
        await member.add_roles(role)
        await ctx.send(f"```✅ | Given role 🎭 `{role.name}` to {member}```")
    except discord.Forbidden:
        await ctx.send("```❌ | Missing permission to assign role.```")
    except Exception as e:
        await ctx.send(f"```❌ | Error: {e}```")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def takerole(ctx, member: discord.Member, *, role_arg):
    role = get_role_by_argument(ctx.guild, role_arg)
    if not role:
        await ctx.send(f"```❌ | Role `{role_arg}` not found.```")
        return
    try:
        await member.remove_roles(role)
        await ctx.send(f"```✅ | Removed role 🎭 `{role.name}` from {member}```")
    except discord.Forbidden:
        await ctx.send("```❌ | Missing permission to remove role.```")
    except Exception as e:
        await ctx.send(f"```❌ | Error: {e}```")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    try:
        duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
        await member.timeout(until=duration, reason=reason)
        await ctx.send(f"```✅ | Timed out ⏱️ {member.mention} for **{minutes} minutes**. 📝 Reason: {reason}```")
    except Exception as e:
        await ctx.send(f"```❌ | Couldn't timeout {member.mention}. Error: {e}```")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.timeout(until=None, reason=reason)
        await ctx.send(f"```✅ | Removed timeout from ⏱️ {member.mention}. 📝 Reason: {reason}```")
    except Exception as e:
        await ctx.send(f"```❌ | Couldn't remove timeout from {member.mention}. Error: {e}```")

@bot.command()
@commands.has_permissions(administrator=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
    try:
        await channel.send(f"📢 **Announcement:** {message}")
        await ctx.send(f"```✅ | Announcement sent to {channel.mention}```")
    except Exception as e:
        await ctx.send(f"```❌ | Failed to send announcement | Error: {e}```")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def vanity(ctx):
    vanity_url = ctx.guild.vanity_url
    if vanity_url:
        await ctx.send(f"```✅ | Server Vanity URL: {vanity_url}```")
    else:
        await ctx.send("```❌ | This server does not have a vanity URL set.```")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    guild_warns = warnings_db.setdefault(ctx.guild.id, {})
    user_warns = guild_warns.setdefault(member.id, [])
    user_warns.append(reason)
    await ctx.send(f"```⚠️ | Warned ⚠️ {member}\nReason: {reason}\nTotal warnings: {len(user_warns)}```")

@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    guild_warns = warnings_db.get(ctx.guild.id, {})
    user_warns = guild_warns.get(member.id, [])
    if user_warns:
        reasons = "\n".join(f"{i+1}. {r}" for i, r in enumerate(user_warns))
        await ctx.send(f"```⚠️ | {member} has {len(user_warns)} warnings:\n{reasons}```")
    else:
        await ctx.send(f"```✅ | {member} has no warnings.```")

@bot.command()
async def roles(ctx):
    roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    roles_list = ", ".join(roles) if roles else "No roles found."
    await ctx.send(f"```📋 | Roles:\n{roles_list}```")

giveaways = {}

@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx, seconds: int, *, prize):
    if seconds <= 0:
        await ctx.send("```❌ | Duration must be > 0 seconds.```")
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

    giveaway_message = await ctx.channel.fetch_message(giveaway_message.id)
    users = set()
    for reaction in giveaway_message.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if user != bot.user:
                    users.add(user)

    if users:
        try:
            winner = random.choice(list(users))
            await ctx.send(f"```✅ | Gave 🤩 Winner!! 🥇 to {winner.display_name}```")
        except Exception:
            await ctx.send(f"```🎉 | Giveaway ended! No valid winner found.```")
    else:
        await ctx.send("```🎉 | Giveaway ended! No participants.```")

    giveaways[giveaway_message.id]["ended"] = True

@bot.command()
async def help(ctx):
    help_text = """```markdown
# 🤖 Discord Bot Commands

Moderation:
!ban <member> [reason]          - Ban a member
!unban <user#1234>              - Unban a user
!kick <member> [reason]         - Kick a member
!timeout <member> <minutes>     - Timeout a member
!untimeout <member>             - Remove timeout from a member
!warn <member> [reason]         - Warn a member
!warnings [member]              - Show a member’s warnings

Roles & Permissions:
!giverole <member> <role>       - Give a role to a user
!takerole <member> <role>       - Remove a role from a user

Server Management:
!announce <#channel> <message>  - Send an announcement
!vanity                         - Show the server's vanity URL
!roles                          - List all roles in the server

Fun & Community:
!giveaway <seconds> <prize>     - Start a giveaway

Help:
!help                           - Show this help message
```"""
    await ctx.send(help_text)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
