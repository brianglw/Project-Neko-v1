import discord
import datetime
import os
from discord.ext import commands
import logging
from ollama import Client
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('DISCORD_BOT_TOKEN')
OLLAMA_HOST = os.getenv('OLLAMA_HOST') or os.getenv('PORT')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
admin_role = 'secretary'

@bot.event
async def on_ready():
    print("discord bot ready to run", bot.user.name)

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome {member.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "cuck" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention}, please refrain from using foul language in this server!")
    

    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
    await ctx.send(f"hello {ctx.author.mention}!")

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=admin_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned {admin_role}")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def remove(ctx):
    role = discord.utils.get(ctx.guild.roles, name=admin_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} is now unassigned {admin_role}")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f'You said {msg}')

@bot.command()
async def reply(ctx):
    await ctx.reply('this is a reply to your message!')

@bot.command()
async def poll(ctx,*,question):
    embed = discord.Embed(title="Pokemon Quiz", description=question)
    poll = await ctx.send(embed=embed)
    await poll.add_reaction("🔥")

@bot.command()
@commands.has_role(admin_role)
async def secret(ctx):
    await ctx.send(f"Welcome to the admin team: {ctx.author.mention}")

@secret.error
async def secret_err(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You don't have the permission to do that")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)