import discord
from discord.ext import commands, tasks
from discord.utils import get
import asyncio
import datetime

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# In-memory warnings dictionary (user_id: count)
warnings = {}

# --- HELP COMMAND ---
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🤖 Bot Commands",
        description="Here are the commands you can use:",
        color=discord.Color.blurple()
    )
    
    embed.add_field(name="Moderation", value=(
        "`!ban <member> [reason]` - Ban a member\n"
        "`!unban <user#1234>` - Unban a user\n"
        "`!kick <member> [reason]` - Kick a member\n"
        "`!warn <member> [reason]` - Warn a member\n"
        "`!warnings [member]` - Show warnings count"
    ), inline=False)
    
    embed.add_field(name="Roles", value=(
        "`!give_role <member> <role>` - Give role\n"
        "`!take_role <member> <role>` - Remove role\n"
        "`!roles` - List all roles"
    ), inline=False)
    
    embed.add_field(name="Mute System", value=(
        "`!mute <member> [seconds] [reason]` - Mute with 'muted' role\n"
        "`!unmute <member>` - Unmute member"
    ), inline=False)
    
    embed.add_field(name="Utility", value=(
        "`!announce <#channel> <message>` - Send announcement\n"
        "`!vanity <member> <nickname>` - Change nickname\n"
        "`!giveaway <seconds> <prize>` - Start giveaway"
    ), inline=False)
    
    embed.set_footer(text="Use commands responsibly! 🤝")
    await ctx.send(embed=embed)

# --- BAN ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member} has been banned. Reason: {reason}")

# --- UNBAN ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')
    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f"✅ Unbanned {user.name}#{user.discriminator}")
            return
    await ctx.send("❌ User not found in ban list.")

# --- KICK ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member} has been kicked. Reason: {reason}")

# --- GIVE ROLE ---
@bot.command()
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, member: discord.Member, *, role_name):
    role = get(ctx.guild.roles, name=role_name)
    if not role:
        return await ctx.send("❌ Role not found.")
    await member.add_roles(role)
    await ctx.send(f"✅ {role.name} role given to {member}")

# --- TAKE ROLE ---
@bot.command()
@commands.has_permissions(manage_roles=True)
async def takerole(ctx, member: discord.Member, *, role_name):
    role = get(ctx.guild.roles, name=role_name)
    if not role:
        return await ctx.send("❌ Role not found.")
    await member.remove_roles(role)
    await ctx.send(f"✅ {role.name} role removed from {member}")

# --- MUTE ---
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, seconds: int = 0, *, reason=None):
    role = get(ctx.guild.roles, name="muted")
    if not role:
        # Create muted role if it doesn't exist
        role = await ctx.guild.create_role(name="muted", reason="Muted role needed")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, speak=False, send_messages=False, read_message_history=True, read_messages=False)
    await member.add_roles(role, reason=reason)
    if seconds > 0:
        await ctx.send(f"🔇 {member} muted for {seconds} seconds. Reason: {reason}")
        await asyncio.sleep(seconds)
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"🔈 {member} has been unmuted (mute time expired).")
    else:
        await ctx.send(f"🔇 {member} muted indefinitely. Reason: {reason}")

# --- UNMUTE ---
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = get(ctx.guild.roles, name="muted")
    if not role:
        return await ctx.send("❌ No muted role found.")
    await member.remove_roles(role)
    await ctx.send(f"🔈 {member} has been unmuted.")

# --- ANNOUNCE ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
    await channel.send(message)
    await ctx.send(f"📢 Announcement sent in {channel.mention}")

# --- VANITY (Nickname Change) ---
@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def vanity(ctx, member: discord.Member, *, nickname):
    await member.edit(nick=nickname)
    await ctx.send(f"✏️ Nickname of {member} changed to: {nickname}")

# --- WARN ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    warnings[member.id] = warnings.get(member.id, 0) + 1
    await ctx.send(f"⚠️ {member} has been warned. Reason: {reason} (Total warnings: {warnings[member.id]})")

# --- WARNINGS ---
@bot.command()
async def warnings(ctx, member: discord.Member = None):
    member = member or ctx.author
    count = warnings.get(member.id, 0)
    await ctx.send(f"ℹ️ {member} has {count} warning(s).")

# --- ROLES LIST ---
@bot.command()
async def roles(ctx):
    roles_list = [role.name for role in ctx.guild.roles if role.name != "@everyone"]
    roles_str = ", ".join(roles_list) if roles_list else "No roles found."
    await ctx.send(f"🎭 Roles in this server:\n{roles_str}")

# --- GIVEAWAY ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def giveaway(ctx, seconds: int, *, prize):
    embed = discord.Embed(title="🎉 Giveaway!", description=f"Prize: **{prize}**", color=discord.Color.green())
    embed.set_footer(text=f"Ends in {seconds} seconds!")
    giveaway_msg = await ctx.send(embed=embed)
    await giveaway_msg.add_reaction("🎉")

    await asyncio.sleep(seconds)

    giveaway_msg = await ctx.channel.fetch_message(giveaway_msg.id)
    users = await giveaway_msg.reactions[0].users().flatten()
    users = [user for user in users if not user.bot]

    if not users:
        await ctx.send("No valid participants, giveaway cancelled.")
        return

    winner = random.choice(users)
    await ctx.send(f"🎊 Congratulations {winner.mention}! You won **{prize}**!")

# Run the bot
import os
# ...
bot.run(os.getenv("DISCORD_BOT_TOKEN"))