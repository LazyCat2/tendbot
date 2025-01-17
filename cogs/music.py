import discord
from discord.ext import commands
import json
import pafy
from youtubesearchpython.__future__ import VideosSearch
import logging
import requests
from discord import app_commands
from flask import request, Flask

app = Flask("Music")

logger = logging.getLogger("Music")
info = logger.info
error = logger.error
debug = logger.debug
warn = logger.warning

pausestate = False
userstate = "none"
botdebug=False
currentradio = "main"

blockedusers =[
	
]

apistatusjson = {
	"playing": "false",
	"type": "idle",
	"url": "none",
	"name": "none",
	"author": "none"
}

errorjson = json.dumps(
	{
	"result": "false"
	})

compjson = json.dumps(
	{
	"result": "true"
	})

radioldb = {
	"main": "http://radiorecord.hostingradio.ru/rr_main96.aacp",
	"phonk": "https://radiorecord.hostingradio.ru/phonk96.aacp"
}

radiodb = {
	"main": 15016,
	"phonk": 43174
}

servers = {}

def antihack(message):
	out = True
	test = list(message)
	if "$" == test[0] or "{" == test[0] or "(" == test[0]:
		info("WARN")
		out = False
	if out == False:
		return out
	else:
		info(2)
		for i in test:
			if "$" == i or "{" == i or "(" == i:
				info("WARN")
				out = False
				break
		if out == False:
			return out
		if "$(" in message or "${" in message or "(" in message or "{" in message:
			return False
		else:
			return True		   

def parsejson(radioid=15016):
	info("Downloading...")
	recordlist = requests.get("https://www.radiorecord.ru/api/stations/now/").json()
	for i in recordlist["result"]:
		if i["id"] == radioid:
			info("Founded record dance radio")
			info("Getting info...")
			recordtrack = i["track"]
			break
		else:
			pass
	recordtrackinfo = {
		"song": recordtrack["song"],
		"artist": recordtrack["artist"]
	}
	info("Parser work done!")
	return recordtrackinfo

def checkyoutubeurl(url):
	info(f"URL: {url}")
	info("Checking url...")
	if url == None:
		info("This is a file!")
		return "file"
	elif url.startswith("https://youtube.com/watch?") or url.startswith("https://soundcloud.com/") or url.startswith("https://youtu.be") or url.startswith("http://youtube.com/watch?") or url.startswith("http://www.youtube.com/watch?") or url.startswith("https://www.youtube.com/watch?") or url.startswith("youtube.com/watch?") or url.startswith("www.youtube.com/watch?"):
		info("This is youtube url!")
		return "ytdl"
	elif url.startswith("https://") or url.startswith("http://"):
		info("This is not youtube url!")
		return "url"
	elif url.startswith("https://youtube.com/playlist?") or url.startswith("http://youtube.com/playlist?") or url.startswith("https://www.youtube.com/playlist?") or url.startswith("http://www.youtube.com/playlist?") or url.startswith("www.youtube.com/playlist?") or url.startswith("youtube.com/playlist?"):
		info("This is a playlist!")
		return "playlist"
	else:
		info("This is not url!")
		return "ytdl"

def on_complete_playing(e, server_id):
	info(e)
	global apistatusjson
	queuelist = servers[server_id]["queuelist"]
	loopstate = servers[server_id]["loopstate"]
	if queuelist == []:
		info("Clearing api status...")
		apistatusjson["playing"] = "false"
		apistatusjson["type"] = "idle"
		apistatusjson["url"] = "none"
		apistatusjson["name"] = "none"
		apistatusjson["author"] = "none"
	else:
		info("Is queue has a file to play?")
		if loopstate == "single":
			info("Loop is on!")
		else:
			del queuelist[0]
		if queuelist == []:
			info("No!")
			info("Clearing api status...")
			apistatusjson["playing"] = "false"
			apistatusjson["type"] = "idle"
			apistatusjson["url"] = "none"
			apistatusjson["name"] = "none"
			apistatusjson["author"] = "none"
		else:
			info("Yes!")
			info("Playing file...")
			apistatusjson = queuelist[0]
			servers[server_id]["vc"].play(discord.FFmpegPCMAudio(queuelist[0]["playurl"]), after=lambda e: on_complete_playing(e, server_id))

class Music(commands.Cog):
	def __init__(self, bot):
		info("Intializating Music cog...")
		self.bot = bot

	class API_methods:
		def gendochtmlamogus(): return "<p>indev</p>"

	@commands.command(aliases=["p"])
	async def play(self, ctx, *, url=None):
		server_id = ctx.guild.id
		if server_id in servers:
			pass
		else:
			servers[server_id] = {"queuelist": [], "loopstate": "off"}
		try:
			connected = ctx.author.voice
			if connected != None:
				servers[server_id]["vc"] = await connected.channel.connect()
			else:
				raise RuntimeException('Сначала зайди в войс.')
		except Exception as e:
			info(e)
		queuelist = servers[server_id]["queuelist"]
		result = checkyoutubeurl(url)
		# await senddebug(ctx, "Проверка на попытку взлома севрера...")
		if result != "file": test = antihack(url)
		else: test = True
		if test == False:
			await ctx.send("!!! WARNING !!!")
			await ctx.send("!!! ОБНАРУЖЕНА ПОПЫТКА ВЗЛОМА БОТА !!!")
		else:
			if result == "ytdl":
				# await senddebug(self, ctx, "Получение url...")
				#os.system('yt-dlp --output /tmp/song.mp3 --force-overwrites -f 140 "{}"'.format(url))
				try:
					info("Trying to get audio url...")
					video = pafy.new(url)
					if len(queuelist) == 0:
						info("Queue is empty.")
						apistatusjson["playing"] = "true"
						apistatusjson["type"] = "ytdl"
						apistatusjson["name"] = str(video.title)
						apistatusjson["author"] = str(video.author)
						apistatusjson["url"] = str(url)
						audio = video.getbestaudio()
						info("Playing...")
						queuefile = {
							"playing": "true",
							"type": "ytdl",
							"name": video.title,
							"author": video.author,
							"url": url,
							"playurl": audio.url
						}
						servers[server_id]["queuelist"].append(queuefile)
						#await ctx.send("Воспроизведение...")
						servers[server_id]["vc"].play(discord.FFmpegPCMAudio(audio.url), after=lambda e: on_complete_playing(e, server_id))
						_embed = discord.Embed(color=0x0080ff)
						_embed.add_field(value=f"[{video.title} by {video.author}]({url})", name="Сейчас играет")
						_embed.set_image(url=video.thumb)
						await ctx.send(embed=_embed)
						return
					else:
						audio = video.getbestaudio()
						queuefile = {
							"playing": "true",
							"type": "ytdl",
							"name": video.title,
							"author": video.author,
							"url": url,
							"playurl": audio.url
						}
						servers[server_id]["queuelist"].append(queuefile)
						_embed = discord.Embed(color=0x0080ff)
						_embed.add_field(value=f"[{video.title} by {video.author}]({vidurl})", name="Добавлен в очередь!")
						_embed.set_image(url=video.thumb)
						await ctx.send(embed=_embed)
						return
				except Exception as e:
					error(f"Error: {e}")
					info("This is not a url")
					info("Trying to search...")
					videosSearch = VideosSearch(url, limit = 1)
					videosResult = await videosSearch.next()
					vidurl = videosResult["result"][0]['link']
					video = pafy.new(vidurl)
					info("Getting audio url...")
					if len(queuelist) == 0:
						info("Queue is empty.")
						apistatusjson["playing"] = "true"
						apistatusjson["type"] = "ytdl"
						apistatusjson["name"] = str(video.title)
						apistatusjson["author"] = str(video.author)
						apistatusjson["url"] = str(vidurl)
						audio = video.getbestaudio()
						info("Playing...")
						#await ctx.send("Воспроизведение...")
						queuefile = {
							"playing": "true",
							"type": "ytdl",
							"name": video.title,
							"author": video.author,
							"url": vidurl,
							"playurl": audio.url
						}
						servers[server_id]["vc"].play(discord.FFmpegPCMAudio(audio.url), after=lambda e: on_complete_playing(e, server_id))
						servers[server_id]["queuelist"].append(queuefile)
						_embed = discord.Embed(color=0x0080ff)
						_embed.add_field(value=f"[{video.title} by {video.author}]({vidurl})", name="Сейчас играет")
						_embed.set_image(url=video.thumb)
						await ctx.send(embed=_embed)
						return
					else:
						audio = video.getbestaudio()
						queuefile = {
							"playing": "true",
							"type": "ytdl",
							"name": video.title,
							"author": video.author,
							"url": vidurl,
							"playurl": audio.url
						}
						servers[server_id]["queuelist"].append(queuefile)
						_embed = discord.Embed(color=0x0080ff)
						_embed.add_field(value=f"[{video.title} by {video.author}]({vidurl})", name="Добавлен в очередь!")
						_embed.set_image(url=video.thumb)
						await ctx.send(embed=_embed)
						return
			elif result == "playlist":
				info("Getting videos from playlist...")
			elif result == "file":
				info("Getting files...")
				files = ctx.message.attachments
				#print(files)
				info(f"Files count: {len(files)}")
				connected = ctx.author.voice
				# grab the user who sent the command
				user=ctx.message.author
				voice_channel=user.voice.channel
				channel=None
				# only play music if user is in a voice channel
				if voice_channel != None:
					for i in files:
						if len(queuelist) == 0:
							queuefile = {
								"playing": "true",
								"type": "file",
								"name": i.filename,
								"author": "none",
								"url": i.url,
								"playurl": i.url
							}
							#apistatusjson = queuefile
							servers[server_id]["queuelist"].append(queuefile)
							servers[server_id]["vc"].play(discord.FFmpegPCMAudio(i.url), after=lambda e: on_complete_playing(e, server_id))
							info(f"File {i.filename} playing now...")
						else:
							queuefile = {
								"playing": "true",
								"type": "file",
								"name": i.filename,
								"author": "none",
								"url": i.url,
								"playurl": i.url
							}
							servers[server_id]["queuelist"].append(queuefile)
							info(f"File {i.filename} added to queue.")
					return
			else:
				connected = ctx.author.voice
				# grab the user who sent the command
				user=ctx.message.author
				voice_channel=user.voice.channel
				channel=None
				apistatusjson["playing"] = "true"
				apistatusjson["type"] = "url"
				apistatusjson["url"] = str(url)
				# only play music if user is in a voice channel
				if voice_channel!= None:
					if len(queuelist) == 0:
						queuefile = {
							"playing": "true",
							"type": "url",
							"name": "none",
							"author": "none",
							"url": url,
							"playurl": url
						}
						servers[server_id]["queuelist"].append(queuefile)
						servers[server_id]["vc"].play(discord.FFmpegPCMAudio(url), after=lambda e: on_complete_playing(e, server_id))
						return
					else:
						queuefile = {
							"playing": "true",
							"type": "url",
							"name": "none",
							"author": "none",
							"url": url,
							"playurl": url
						}
						servers[server_id]["queuelist"].append(queuefile)
						return
				else:
					await ctx.send('Сначала войди в войс.')
					return
	@commands.command(aliases=["np"])
	async def nowplaying(self, ctx):
		if apistatusjson["type"] == "ytdl":
			_embed = discord.Embed(title=apistatusjson["name"], description=apistatusjson["author"], color=0x0080ff)
			await ctx.send(embed=_embed)
		elif apistatusjson["type"] == "url":
			await ctx.send("Something playing")
		elif apistatusjson["type"] == "pause":
			await ctx.send("Music on pause")
		elif apistatusjson["type"] == "idle":
			await ctx.send("Nothing is playing")
		elif apistatusjson["type"] == "radio":
			await ctx.send("Radio is playing now.")
	
	@commands.command()
	async def join(self, ctx):
		connected = ctx.author.voice
		server_id = ctx.guild.id
		if server_id in servers:
			pass
		else:
			servers[server_id] = {"queuelist": [], "loopstate": "off"}
		if connected != None:
			servers[server_id]['vc'] = await connected.channel.connect()
		else:
			await ctx.send('Сначала зайди в войс.')
	@commands.command()
	async def leave(self, ctx):
		await ctx.send("Ок, выхожу...")
		server_id = ctx.guild.id
		await servers[server_id]["vc"].disconnect()

	@commands.command()
	async def loop(self, ctx, state="single"):
		if state == "single":
			servers[ctx.guild.id]["loopstate"] = state
		elif state == "off":
			servers[ctx.guild.id]["loopstate"] = state
		else:
			await ctx.send("single - один файл\noff - выключить")

	@commands.command()
	async def pause(self, ctx):
		global pausestate
		global oldtypestatusjson
		try:
			if pausestate == False:
				vc.pause()
				pausestate = True
				apistatusjson["playing"] = "false"
				oldtypestatusjson = apistatusjson["type"]
				apistatusjson["type"] = "pause"
			elif pausestate == True:
				vc.resume()
				pausestate = False
				apistatusjson["playing"] = "true"
				apistatusjson["type"] = oldtypestatusjson
		except Exception as e:
			info(e)
			await ctx.send("Error!")

	@commands.command(aliases=["skip"])
	async def stop(self, ctx):
		server_id = ctx.guild.id
		apistatusjson["playing"] = "false"
		apistatusjson["type"] = "idle"
		apistatusjson["url"] = "none"
		apistatusjson["name"] = "none"
		apistatusjson["author"] = "none"
		servers[server_id]["vc"].stop()
	@commands.command(aliases=["q"])
	async def queue(self, ctx):
		server_id = ctx.guild.id
		embed = discord.Embed(title="Очередь", color=0x0080ff)
		queuelist = servers[server_id]["queuelist"]
		if queuelist == []: embed.add_field(name="Ничего сейчас не играет.", value="***это костыль***")
		else:
			#await ctx.send("Queue:")
			for i in queuelist:
				if i["type"] == "url": embed.add_field(name="URL", value=i["url"])
				elif i["type"] == "ytdl": embed.add_field(name=f'[{i["name"]}]({i["url"]})', value=i["author"])
				elif i["type"] == "file": embed.add_field(name="Файл", value=f"[{i['name']}]({i['url']})")
		await ctx.send(embed=embed)

async def setup(bot):
	info("Setup of Music cog called!")
	await bot.add_cog(Music(bot))