import discord
from discord.channel import VoiceChannel
from discord.ext import commands
import song_finder
import asyncio
import math

FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 50 -timeout 5000', 'options': '-vn'}

client = commands.Bot(command_prefix="ca!", case_insensitive=True)
embed_color = 0xf7bf25
song_queue = {}
now_playing = {}
skip_vote = {}

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
        if ctx.voice_client is None:
            await vc.connect()
        else:
            await vc.move()
    else:
        embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
        await ctx.reply(embed=embedMsg)

@client.command()
async def leave(ctx: commands.Context):
    if (ctx.author.voice and ctx.voice_client.channel):
        if (ctx.author.voice.channel.id == ctx.voice_client.channel.id):
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            voice.stop()
            now_playing[ctx.guild.id] = None
            song_queue[ctx.guild.id] = []
            skip_vote[ctx.guild.id] = []
            await ctx.voice_client.disconnect()
        else:
            embedMsg = discord.Embed(description="你必須在該語音頻道內才能使用此指令", color=embed_color)
            await ctx.reply(embed=embedMsg)
    else:
        embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
        await ctx.reply(embed=embedMsg)

@client.command(aliases=['p'])
async def play(ctx: commands.Context, song):
    if (not ctx.author.voice):  # 使用者沒有在語音頻道內
        embedMsg = discord.Embed(description="你必須在語音頻道內才能使用此指令", color=embed_color)
        await ctx.reply(embed=embedMsg)
        return

    if (ctx.voice_client is not None):  # 機器人有在語音頻道內但使用者頻道不同
        if (ctx.author.voice.channel.id != ctx.voice_client.channel.id):
            embedMsg = discord.Embed(description="你必須相同的語音頻道才能使用此指令", color=embed_color)
            await ctx.reply(embed=embedMsg)
            return
    
    if (not ctx.voice_client):  # 機器人沒在語音頻道內
        vc = ctx.author.voice.channel
        await vc.connect()
    
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    # 播完一首歌之後確認有無排隊，有則播放第一首
    def check_queue_and_play_next_if_have_next(ctx: commands.Context):
        if ctx.guild.id in song_queue and song_queue[ctx.guild.id]:
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            u_song = song_queue[ctx.guild.id].pop(0)
            now_playing[ctx.guild.id] = u_song
            skip_vote[ctx.guild.id] = []
            voice.play(discord.FFmpegPCMAudio(u_song[0], **FFMPEG_OPTS), after=lambda e: check_queue_and_play_next_if_have_next(ctx))
            embedMsg = discord.Embed(title="正在播放", 
                description="**[{}]({})**".format(u_song[1], u_song[2]), 
                color=embed_color)
            asyncio.run_coroutine_threadsafe(ctx.send(embed=embedMsg), client.loop)
            return
        else:
            now_playing[ctx.guild.id] = None
            # song_queue[ctx.guild.id] = []
            skip_vote[ctx.guild.id] = []
            # 如果沒有下一首歌就直接退出
            asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), client.loop)
            return

    u_song = song_finder.find(song)
    if u_song is not None and u_song != 0 and u_song[0]:
        # 如果沒有佇列的話，直接播放
        if (ctx.guild.id not in song_queue or not song_queue[ctx.guild.id]) and (ctx.guild.id not in now_playing or not now_playing[ctx.guild.id]):
            now_playing[ctx.guild.id] = u_song
            voice.play(discord.FFmpegPCMAudio(u_song[0], **FFMPEG_OPTS), after=lambda e: check_queue_and_play_next_if_have_next(ctx))
            skip_vote[ctx.guild.id] = []
            print(voice.is_playing())  # for debugging?
            embedMsg = discord.Embed(title="正在播放", 
                description="**[{}]({})**".format(u_song[1], song), 
                color=embed_color)
            await ctx.send(embed=embedMsg)
        else:  # 如果已經在播放了，則添加進佇列
            u_song += (ctx.author.id, )
            if ctx.guild.id not in song_queue:
                song_queue[ctx.guild.id] = [u_song]
            else:
                song_queue[ctx.guild.id].append(u_song)
            embedMsg = discord.Embed(title="已添加進佇列", 
                description="**[{}]({})**".format(u_song[1], song), 
                color=embed_color)
            await ctx.send(embed=embedMsg)
    elif u_song is None:
        embedMsg = discord.Embed(description="不支援該平台", color=embed_color)
        await ctx.reply(embed=embedMsg)
    elif u_song == 0:
        embedMsg = discord.Embed(description="這不是正確的音樂連結", color=embed_color)
        await ctx.reply(embed=embedMsg)

@client.command(aliases=['q'])
async def queue(ctx: commands.Context):
    #print(song_queue)  # this is for debugging
    if ctx.guild.id in song_queue:
        q = song_queue[ctx.guild.id]
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
    #print(song_queue)  # this is for debugging
    if ctx.guild.id not in now_playing or now_playing[ctx.guild.id] is None:
        # no song is playing
        embedMsg = discord.Embed(description="沒有任何歌在播放喔", color=embed_color)
        await ctx.send(embed=embedMsg)
    else:
        np_song = now_playing[ctx.guild.id]
        embedMsg = discord.Embed(title="正在播放", 
                description="**[{}]({})**".format(np_song[1], np_song[2]), 
                color=embed_color)
        await ctx.send(embed=embedMsg)

# 還在測試階段
@client.command(aliases=['rmq'])
async def removequeue(ctx: commands.Context, index):
    try:
        index = int(index)
        assert index > 0
    except (ValueError, AssertionError):
        embedMsg = discord.Embed(description="必須輸入正數", color=embed_color)
        await ctx.send(embed=embedMsg)
        return
    
    if ctx.guild.id in song_queue and song_queue[ctx.guild.id]:
        if len(song_queue[ctx.guild.id]) >= index:
            if ctx.author.id == song_queue[ctx.guild.id][index - 1][3]:
                rm_song = song_queue[ctx.guild.id].pop(index - 1)
                embedMsg = discord.Embed(description="已移除佇列曲目 **{}**".format(rm_song[1]), color=embed_color)
                await ctx.send(embed=embedMsg)
            else:
                embedMsg = discord.Embed(description="必須是點該首歌的使用者才能使用此指令", color=embed_color)
                await ctx.send(embed=embedMsg)
        else:
            embedMsg = discord.Embed(description="佇列沒有那麼長", color=embed_color)
            await ctx.send(embed=embedMsg)
    else:
        embedMsg = discord.Embed(description="目前沒有歌曲佇列喔", color=embed_color)
        await ctx.send(embed=embedMsg)

# 尚未測試完的功能
@client.command()
async def skip(ctx: commands.Context):
    #print(skip_vote)
    if ctx.author.id in skip_vote[ctx.guild.id]:
        embedMsg = discord.Embed(description="你已經使用該指令過了，直到下一首歌播放之前都不能使用該指令", color=embed_color)
        await ctx.reply(embed=embedMsg)
        return
    skip_vote[ctx.guild.id].append(ctx.author.id)
    req = min(5, len(ctx.voice_client.channel.members) * .5)
    if len(skip_vote[ctx.guild.id]) >= req:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice.stop()
        embedMsg = discord.Embed(description="已跳過", color=embed_color)
        await ctx.send(embed=embedMsg)
    else:
        embedMsg = discord.Embed(description="跳過所需人數: {}/{}".format(len(skip_vote[ctx.guild.id]), math.ceil(req)), color=embed_color)
        await ctx.send(embed=embedMsg)

client.run("OTI2Mzk3NjE0NTM3MTc5MTM2.Yc7FAg.ccY6kfpc6moiyh-GQog500ppfUw")
