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
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, seconds: int = None, *, reason=None):
    role = discord.utils.get(ctx.guild.roles, name="muted")
    if not role:
        await ctx.send("```❌ | 'muted' role missing. Create it first!```")
        return
    try:
        await member.add_roles(role, reason=reason)
        if seconds:
            await ctx.send(f"```✅ | Muted 🤐 {member} for {seconds}s | Reason: {reason or 'No reason provided.'}```")
            await asyncio.sleep(seconds)
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"```✅ | Auto-unmuted 🔊 {member} after {seconds}s```")
        else:
            await ctx.send(f"```✅ | Muted 🤐 {member} indefinitely | Reason: {reason or 'No reason provided.'}```")
    except Exception as e:
        await ctx.send(f"```❌ | Failed to mute {member} | Error: {e}```")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="muted")
    if not role:
        await ctx.send("```❌ | 'muted' role missing.```")
        return
    if role in member.roles:
        try:
            await member.remove_roles(role)
            await ctx.send(f"```✅ | Unmuted 🔊 {member}```")
        except Exception as e:
            await ctx.send(f"```❌ | Failed to unmute {member} | Error: {e}```")
    else:
        await ctx.send(f"```⚠️ | {member} is not muted.```")

@bot.command()
@commands.has_permissions(administrator=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
    try:
        await channel.send(f"📢 **Announcement:** {message}")
        await ctx.send(f"```✅ | Announcement sent to {channel.mention}```")
    except Exception as e:
        await ctx.send(f"```❌ | Failed to send announcement | Error: {e}```")

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def vanity(ctx, member: discord.Member, *, nickname):
    try:
        await member.edit(nick=nickname)
        await ctx.send(f"```✅ | Nickname changed ✏️ for {member} to '{nickname}'```")
    except Exception as e:
        await ctx.send(f"```❌ | Failed to change nickname | Error: {e}```")

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
# Custom Help
!ban <member> [reason] - Ban a member.
!unban <user#1234> - Unban a user.
!kick <member> [reason] - Kick a member.
!giverole <member> <role> - Give a role.
!takerole <member> <role> - Remove a role.
!mute <member> [seconds] [reason] - Mute a member.
!unmute <member> - Unmute a member.
!announce <#channel> <message> - Send announcement.
!vanity <member> <nickname> - Change nickname.
!warn <member> [reason] - Warn a member.
!warnings [member] - Show warnings count.
!roles - List all roles.
!giveaway <seconds> <prize> - Start a giveaway.
```"""
    await ctx.send(help_text)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
