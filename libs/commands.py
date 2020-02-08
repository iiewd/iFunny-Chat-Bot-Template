from libs import google
import random
import requests
import json
import traceback
import time
import os
import math
from colorama import Fore, Back, Style
import threading

header = {'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}

class commands_container(type):
	
	commands = {}
	
	@classmethod
	def add(self, aliases, function):
		if isinstance(aliases, str): aliases = [aliases]
		assert isinstance(aliases, list), f"Function {function.__name__} aliases must be str or list of strings"
		for alias in aliases:
			assert not self.commands.get(alias), f"Function {function.__name__} already exists for {alias}"
			self.commands[alias] = function
			
	def __getitem__(self, index):
		return self.commands.get(index)
	
class pool(metaclass=commands_container): pass

def command(*args, **kwargs): 
	def decorator(function):
		aliases = []
		if name := kwargs.get("name"):
			aliases.append(name)
		else:
			aliases.append(function.__name__)
		if kwargs.get("aliases"):
			aliases.extend(kwargs["aliases"])
		pool.add(aliases, function) 
		return function
	return decorator


def execute(function, ctx):
	try: function(ctx)
	except: traceback.print_exc()
		
		
def user_or_other(ctx, specific_other=None):
	
	channel = ctx.channel
	message = ctx.message
	author = message.author
	other = message.command.arguments
	
	if not specific_other:
		specific_other = other
	
	if other:
	
		other = ctx.bot.user_by_nick(specific_other)

		if not other:
			channel.send("I couldn't find that user! 😕")
			False
			
		return other
	
	else:
		author.get_data()
		return author
	
	
	
def nick_by_id(bot, id_list):
	
	nick_list = []
	tasks = []
	
	def request_data(user_id, container):
		other_user = bot.user(user_id)
		if other_user: user_nick = other_user.name
		else: user_nick = "<unknown user>"
		container.append(user_nick)
	
	for user_id in id_list:
		task = threading.Thread(target=request_data, args=(user_id,nick_list))
		task.start()
		tasks.append(task)
		
	[task.join() for task in tasks]
		
	return nick_list


def paginate(data, page=1, limit=30):
	max_page = math.ceil(len(data)/limit)
	page = min(max(int(page), 1), max_page)
	chunk = data[(page-1)*limit:page*limit]
	return chunk, page, max_page


help_msg = """
This is where you write your help message

:)
"""

@command(aliases = ["commands"], name = "help")
def _help(ctx):
	
	channel = ctx.channel
	message = ctx.message
	author = message.author
	category = message.command.arguments.lower()

	if category == "admin":
		msg = admin_help
	else:
		msg = help_msg

	channel.send(msg)
		

@command()
def clap(ctx):
	
	channel = ctx.channel
	text = ctx.message.command.arguments
	
	text = text.replace(" ", "👏")
	text += "👏"
	channel.send(text)
	
	
@command()
def say(ctx):
	return
	ctx.channel.send(ctx.message.command.arguments)
	

@command()
def ping(ctx):

	channel = ctx.channel
	message = ctx.message
	author = message.author
	latency = int(time.time()*1000)-message.ts
	
	channel.send(f"Pong! {latency}ms")
	
@command()
def rr(ctx):

	channel = ctx.channel
	members = channel.get_members()
	other = random.choice(members.items)
	channel.send(f"{other.name} died in Russian Roulette 💀")
	

@command(aliases = ["image", "pic"])
def img(ctx):
	
	channel = ctx.channel
	message = ctx.message
	author = message.author
	search = message.command.arguments
	
	if not search:
		channel.send("Specify a query")
		return
	
	images = google.Images.search(search)

	if images:
		package = random.choice(images)
		channel.upload(*package)
		return
			
	channel.send(f"No results for {search}")
	

@command(aliases = ["add"])
def invite(ctx):
	
	channel = ctx.channel
	message = ctx.message
	other = message.command.arguments
	
	if " " in other:
		channel.send("Specify only one user")
		return
	
	if channel.type == "chat":
		channel.send("I cannot invite people to a dm")
		return
	
	other_user = user_or_other(ctx)
	
	if not other_user:
		return

	response = channel.invite(other_user)
	
	if not response:
		channel.send(f"{other_user.name} was invited")
	else:
		channel.send(response)


@command()
def setcolor(ctx):
	
	"""This will only work if the loopcolor thread
	is not running on the bot obviously
	"""
	
	channel = ctx.channel
	message = ctx.message
	author = message.author
	color = message.command.arguments.strip("#").upper()
	
	if author != ctx.bot.me:
		return
	
	if len(color) != 6:
		channel.send("That is not a valid color")
		return
	
	url = f"https://api-us-1.sendbird.com/v3/users/{ctx.bot.me.id}/metadata"
	headers = {"Session-Key": ctx.bot.sessionkey}
	payload = json.dumps({"metadata": {"nick_color": color}})
	
	r = requests.put(url, data=payload, headers=headers).json()
	
	if "error" in r:
		r = requests.post(url, data=payload, headers=headers).json()

	channel.send("Color successfully updated")
	

@command()
def setnick(ctx):
	
	channel = ctx.channel
	message = ctx.message
	author = message.author
	nick = message.command.arguments
	
	if author != ctx.bot.me:
		return
	
	#nickname thread must be running for this to work
	ctx.bot.nick = nick
	channel.send("Nickname successfully updated")
	


	