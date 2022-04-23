#Automatic Checkin-Bot using Tabbycat API
#Code is probably many times longer than it needs to be 

import os
import discord 
from discord import Game
from discord.ext import commands
from discord.ext.commands import CommandNotFound
import asyncio
import json
import random
import requests 
from dotenv import load_dotenv

token_env_path = "tkns.env"
load_dotenv(token_env_path) 

intents = discord.Intents.default()
intents.members = True

TOKEN = os.environ.get("BOT_TOKEN")

prefix = '+'
bot = commands.Bot(command_prefix=prefix, help_command=None, intents = intents) 

API_TOKEN = os.environ.get("API_TOKEN")
HEADERS = {'Authorization': 'Token {}'.format(API_TOKEN)}

domain = os.environ.get("DOMAIN")
slug = os.environ.get("SLUG")

api_prefix = f"{domain}/api/v1/tournaments/{slug}"
verification_url = f"{domain}/{slug}/checkins/status/people/"

session = requests.Session()
session.headers.update(HEADERS)

@bot.command(pass_context = True, aliases=['h'])
async def help(ctx):
    await ctx.send(f"{ctx.author.mention} Use the command `{prefix}checkin <First Last>` to get started. Enter your full name as it appears on the tab and ensure the spelling is an exact match. If you have any questions or issues, you can direct message any member of the org-comm.")
 
@bot.command(pass_context = True)
async def checkin(ctx,*,inp_name):
    spk = session.get(f'{api_prefix}/speakers').json()
    author_id = None
    is_debater = False
    for i in spk:
        if(i['name'].lower() == inp_name.lower()):
            author_id = i['id']
            is_debater = True
            break
    if(author_id == None):
        adj = session.get(f'{api_prefix}/adjudicators').json()
        for i in adj:
            if(i['name'].lower() == inp_name.lower()):
                author_id = i['id']
                break

    if(author_id == None):
        await ctx.send(f"{ctx.author.mention} Sorry, that name wasn't recognized. Please try again.")
    else:
        if(is_debater):
            r2 = session.get(f'{api_prefix}/speakers/{author_id}/checkin')
            if r2.json()['checked']:
                await ctx.send(f"{ctx.author.mention} You are already checked in! Please direct message Tabs if there is an issue with your check-in!")
            else:
                r3 = session.put(f'{api_prefix}/speakers/{author_id}/checkin')
                await ctx.send(f"{ctx.author.mention} You are checked in as [Debater] {inp_name}! You can verify your check-in has succeeded at {verification_url}. The link might take 1-2 minutes to update to reflect your check-in status, so please be patient.")
        else:
            r2 = session.get(f'{api_prefix}/adjudicators/{author_id}/checkin')
            if r2.json()['checked']:
                await ctx.send(f"{ctx.author.mention} You are already checked in! Please direct message Tabs if there is an issue with your check-in!")
            else:
                r3 = session.put(f'{api_prefix}/adjudicators/{author_id}/checkin')
                await ctx.send(f"{ctx.author.mention} You are checked in as [Adjudicator] {inp_name}! You can verify your check-in has succeeded at {verification_url}. The link might take 1-2 minutes to update to reflect your check-in status, so please be patient.")
@checkin.error
async def checkin_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send(f" {ctx.author.mention} Please check-in using the command `{prefix}checkin <First Last>`. Enter your full name as it appears on the tab and ensure the spelling is an exact match. If you have any questions or issues, you can direct message any member of the org-comm.") 
    else:
        await ctx.send(f"{ctx.author.mention} An error has occurred. Please message a member of org-comm for help!\n{error}")

@commands.has_permissions(administrator=True)
@bot.command(pass_context=True)
async def unchecked(ctx):
    out_str = "The following people have not checked in (This might take some time, so please be patient):\n"
    msg = await ctx.send(out_str)
    spk = session.get(f'{api_prefix}/speakers').json()
    for i in spk:
        id = i['id']
        r2 = session.get(f'{api_prefix}/speakers/{id}/checkin')
        if not r2.json()['checked']:
            r3 = session.get(i['team'])
            out_str += f"{i['name']} [{r3.json()['reference']}]\n"
            await msg.edit(content=out_str+". . .")
    await msg.edit(content=out_str)
@unchecked.error
async def unchecked_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{ctx.author.mention} Sorry you're not allowed to use this command. This command is only for administrators.")
    else:
        await ctx.send(f"{ctx.author.mention} An error has occurred.\n{error}")

@bot.event
async def on_ready():
    print('Logged in as: ' + bot.user.name)
    await bot.change_presence(status=discord.Status.idle, activity=Game(name=f"{prefix}checkin"))
bot.run(TOKEN) 
