import discord
from discord.ext import commands, tasks
import asyncio
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

warnings_db = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

# Ban command
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"```✅ {member} has been banned.\nReason: {reason if reason else 'No reason provided.'}```")
    except Exception as e:
        await ctx.send(f"```❌ Failed to ban {member}: {e}```")

# Unban command
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, user: str):
    banned_users = await ctx.guild.bans()
    name, discrim = user.split("#")
    for ban_entry in banned_users:
        user_obj = ban_entry.user
        if (user_obj.name, user_obj.discriminator) == (name, discrim):
            await ctx.guild.unban(user_obj)
            await ctx.send(f"```✅ Unbanned {user_obj}.```")
            return
    await ctx.send(f"```❌ User {user} not found in banned list.```")

# Kick command
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"```✅ {member} has been kicked.\nReason: {reason if reason else 'No reason provided.'}```")
    except Exception as e:
        await ctx.send(f"```❌ Failed to kick {member}: {e}```")

# Give role
@bot.command()
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, member: discord.Member, *, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        return await ctx.send(f"```❌ Role '{role_name}' not found.```")
    try:
        await member.add_roles(role)
        await ctx.send(f"```✅ Given role '{role.name}' to {member}.```")
    except Exception as e:
        await ctx.send(f"```❌ Could not add role: {e}```")

# Take role
@bot.command()
@commands.has_permissions(manage_roles=True)
async def takerole(ctx, member: discord.Member, *, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        return await ctx.send(f"```❌ Role '{role_name}' not found.```")
    try:
        await member.remove_roles(role)
        await ctx.send(f"```✅ Removed role '{role.name}' from {member}.```")
    except Exception as e:
        await ctx.send(f"```❌ Could not remove role: {e}```")

# Mute command
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, seconds: int = 0, *, reason=None):
    role = discord.utils.get(ctx.guild.roles, name="muted")
    if not role:
        try:
            role = await ctx.guild.create_role(name="muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, speak=False, send_messages=False, read_message_history=True, read_messages=False)
        except Exception as e:
            return await ctx.send(f"```❌ Could not create muted role: {e}```")
    if role in member.roles:
        return await ctx.send(f"```❌ {member} is already muted.```")
    try:
        await member.add_roles(role, reason=reason)
        await ctx.send(f"```✅ {member} has been muted for {seconds} seconds.\nReason: {reason if reason else 'No reason provided.'}```")
        if seconds > 0:
            await asyncio.sleep(seconds)
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"```✅ {member} has been unmuted after {seconds} seconds.```")
    except Exception as e:
        await ctx.send(f"```❌ Failed to mute: {e}```")

# Unmute command
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="muted")
    if not role or role not in member.roles:
        return await ctx.send(f"```❌ {member} is not muted.```")
    try:
        await member.remove_roles(role)
        await ctx.send(f"```✅ {member} has been unmuted.```")
    except Exception as e:
        await ctx.send(f"```❌ Failed to unmute: {e}```")

# Announce command
@bot.command()
@commands.has_permissions(manage_messages=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
    try:
        await channel.send(f"📢 **Announcement:** {message}")
        await ctx.send(f"```✅ Announcement sent to {channel.mention}.```")
    except Exception as e:
        await ctx.send(f"```❌ Failed to send announcement: {e}```")

# Vanity (nickname change)
@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def vanity(ctx, member: discord.Member, *, nickname):
    try:
        await member.edit(nick=nickname)
        await ctx.send(f"```✅ Changed nickname for {member} to '{nickname}'.```")
    except Exception as e:
        await ctx.send(f"```❌ Failed to change nickname: {e}```")

# Warn command
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    if member.id not in warnings_db:
        warnings_db[member.id] = []
    warnings_db[member.id].append(reason if reason else "No reason provided")
    await ctx.send(f"```⚠️ {member} has been warned.\nReason: {reason if reason else 'No reason provided.'}```")

# Warnings command
@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    warns = warnings_db.get(member.id, [])
    if warns:
        warn_list = "\n".join(f"{i+1}. {w}" for i, w in enumerate(warns))
        await ctx.send(f"```Warnings for {member} ({len(warns)} total):\n{warn_list}```")
    else:
        await ctx.send(f"```{member} has no warnings.```")

# Roles command
@bot.command()
async def roles(ctx):
    roles = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    roles_list = "\n".join(roles) if roles else "No roles found."
    await ctx.send(f"```Roles in this server:\n{roles_list}```")

# Giveaway command (basic)
@bot.command()
@commands.has_permissions(manage_messages=True)
async def giveaway(ctx, seconds: int, *, prize):
    embed = discord.Embed(title="🎉 Giveaway!", description=f"Prize: {prize}\nReact with 🎉 to enter!\nEnds in {seconds} seconds.")
    giveaway_message = await ctx.send(embed=embed)
    await giveaway_message.add_reaction("🎉")

    await asyncio.sleep(seconds)

    message = await ctx.channel.fetch_message(giveaway_message.id)
    users = set()
    for reaction in message.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    users.add(user)
    if users:
        winner = random.choice(list(users))
        await ctx.send(f"🎉 Congratulations {winner.mention}! You won the giveaway for **{prize}**!")
    else:
        await ctx.send("No valid entries for the giveaway.")

# Custom help command (already removed default above)
@bot.command()
async def help(ctx):
    help_text = (
        "```"
        "Available Commands:\n"
        "• !ban <member> [reason] - Ban a member.\n"
        "• !unban <user#1234> - Unban a user.\n"
        "• !kick <member> [reason] - Kick a member.\n"
        "• !giverole <member> <role> - Give a role.\n"
        "• !takerole <member> <role> - Remove a role.\n"
        "• !mute <member> [seconds] [reason] - Mute a member with muted role.\n"
        "• !unmute <member> - Unmute a member.\n"
        "• !announce <#channel> <message> - Send announcement.\n"
        "• !vanity <member> <nickname> - Change nickname.\n"
        "• !warn <member> [reason] - Warn a member.\n"
        "• !warnings [member] - Show warnings count.\n"
        "• !roles - List all roles.\n"
        "• !giveaway <seconds> <prize> - Start a giveaway.\n"
        "```"
    )

    await ctx.send(help_text)

# Run the bot with your token from environment variable DISCORD_BOT_TOKEN
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
