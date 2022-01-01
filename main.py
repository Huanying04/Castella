import discord
from discord.channel import VoiceChannel
from discord.ext import commands
import song_finder
import asyncio

FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -timeout 1000', 'options': '-vn'}

client = commands.Bot(command_prefix="ca!", case_insensitive=True)
embed_color = 0xf7bf25
song_queue = {}
now_playing = {}

@client.event
async def on_ready():
    print("Bot is on ready")

@client.command()
@commands.is_owner()
async def shutdown(ctx: commands.Context):
    await ctx.send("正在退出…")
    await ctx.bot.close()

@client.command()
async def join(ctx: commands.Context):
    if (ctx.author.voice):
        vc: VoiceChannel = ctx.author.voice.channel
        if not ctx.me.voice:
            await vc.connect()
        else:
            await vc.move()
    else:
        embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
        await ctx.reply(embed=embedMsg)

@client.command()
async def leave(ctx: commands.Context):
    if (ctx.author.voice and ctx.me.voice):
        if (ctx.author.voice.channel == ctx.me.voice.channel):
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            voice.stop()
            now_playing[ctx.guild] = None
            song_queue[ctx.guild] = []
            await ctx.voice_client.disconnect()
        else:
            embedMsg = discord.Embed(description="你必須在該語音頻道內才能使用此指令", color=embed_color)
            await ctx.reply(embed=embedMsg)
    else:
        embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
        await ctx.reply(embed=embedMsg)

@client.command(aliases=['p'])
async def play(ctx: commands.Context, song):
    if (not ctx.author.voice):
        embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
        await ctx.reply(embed=embedMsg)
        return
    
    if (not ctx.me.voice):
        vc = ctx.author.voice.channel
        await vc.connect()
    
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    # 播完一首歌之後確認有無排隊，有則播放第一首
    def check_queue_and_play_next_if_have_next(ctx: commands.Context):
        if ctx.guild in song_queue and song_queue[ctx.guild]:
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            u_song = song_queue[ctx.guild].pop(0)
            now_playing[ctx.guild] = u_song
            voice.play(discord.FFmpegPCMAudio(u_song[0], **FFMPEG_OPTS), after=lambda e: check_queue_and_play_next_if_have_next(ctx))
            embedMsg = discord.Embed(title="正在播放", 
                description="**[{}]({})**".format(u_song[1], u_song[2]), 
                color=embed_color)
            asyncio.run_coroutine_threadsafe(ctx.send(embed=embedMsg), client.loop)
        else:
            now_playing[ctx.guild] = None
            return

    u_song = song_finder.find(song)
    if u_song[0] and u_song != 0 and u_song is not None:
        # 如果沒有佇列的話，直接播放
        if (ctx.guild not in song_queue or not song_queue[ctx.guild]) and (ctx.guild not in now_playing or not now_playing[ctx.guild]):
            now_playing[ctx.guild] = u_song
            voice.play(discord.FFmpegPCMAudio(u_song[0], **FFMPEG_OPTS), after=lambda e: check_queue_and_play_next_if_have_next(ctx))
            print(voice.is_playing())  # for debugging?
            embedMsg = discord.Embed(title="正在播放", 
                description="**[{}]({})**".format(u_song[1], song), 
                color=embed_color)
            await ctx.send(embed=embedMsg)
        else:  # 如果已經在播放了，則添加進佇列
            if ctx.guild not in song_queue:
                song_queue[ctx.guild] = [u_song]
            else:
                song_queue[ctx.guild].append(u_song)
            embedMsg = discord.Embed(title="已添加進佇列", 
                description="**[{}]({})**".format(u_song[1], song), 
                color=embed_color)
            await ctx.send(embed=embedMsg)
    elif u_song == 0:
        embedMsg = discord.Embed(description="這不是正確的音樂連結", color=embed_color)
        ctx.reply(embed=embedMsg)
    elif u_song is None:
        embedMsg = discord.Embed(description="不支援該平台", color=embed_color)
        ctx.reply(embed=embedMsg)

@client.command(aliases=['q'])
async def queue(ctx: commands.Context):
    #print(song_queue)  # this is for debugging
    if ctx.guild in song_queue:
        q = song_queue[ctx.guild]
        if not q:
            embedMsg = discord.Embed(description="沒有任何歌在排隊喔", color=embed_color)
            await ctx.send(embed=embedMsg)
            return
        msg = ""
        i = 1
        for x in q:
            msg += "{}. **{}**\n".format(i, x[1])
            i += 1
        embedMsg = discord.Embed(description=msg, color=embed_color)
        await ctx.send(embed=embedMsg)
    else:
        embedMsg = discord.Embed(description="沒有任何歌在排隊喔", color=embed_color)
        await ctx.send(embed=embedMsg)

@client.command(aliases=['np'])
async def nowplaying(ctx: commands.Context):
    print(song_queue)
    if ctx.guild not in now_playing or now_playing[ctx.guild] is None:
        # no song is playing
        embedMsg = discord.Embed(description="沒有任何歌在播放喔", color=embed_color)
        await ctx.send(embed=embedMsg)
    else:
        np_song = now_playing[ctx.guild]
        embedMsg = discord.Embed(title="正在播放", 
                description="**[{}]({})**".format(np_song[1], np_song[2]), 
                color=embed_color)
        await ctx.send(embed=embedMsg)


client.run("機器人TOKEN")
