import asyncio
import youtube_dl
import pafy
import discord
from webserver import keep_alive
from discord.ext import commands
from judulvideo import judulvideo


intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="*", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} Sudah Siap.")

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        self.song_queue = {}
        self.setup()

    def setup(self):
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []

    async def check_queue(self, ctx):
        queue_len = len(self.song_queue[ctx.guild.id])
        if queue_len == 0 :
            ctx.voice_client.stop()
            
        if len(self.song_queue[ctx.guild.id]) > 0:
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)
        if (queue_len == 0) and ctx.voice_client.source is None:
          await asyncio.sleep(240) 
          if (queue_len == 0) and ctx.voice_client.source is None:
            await ctx.send("Ah lama banget request lagunya . gua chau dah ")
            await ctx.voice_client.disconnect()

    async def search_song(self, amount, song, get_url=False):
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format" : "bestaudio", "quiet" : True}).extract_info(f"ytsearch{amount}:{song}", download=False, ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

    async def play_song(self, ctx, song):
        queue_len= len(self.song_queue[ctx.guild.id])
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        if queue_len == 0 :
            ctx.voice_client.stop()
        url = pafy.new(song).getbestaudio().url
        
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url,**FFMPEG_OPTIONS)),after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 1
        await ctx.send(f"Langsung ae kali yak , diplay: {song}")
        
        
        
    @commands.command()
    async def petunjuk(self,ctx):
      await ctx.send("*join\n #ini digunain buat ngundang si bot buat masuk ke voice channel\n\n*play / p\n#ini digunain buat lu ngeplay lagunye\n\n*antrian\n#ini digunain buat ngeliat antrian lagu yang mau diplay \n\n*skip / s\n#ini digunain buat ngeskip lagu yang lagi diplay ye\n\n*stop\n#ini digunain buat ngestop lagunya\n\n*start \n#ini digunain buat ngeplay  lagunya lagi bro\n\n*leave \n#ini digunain buat mengeluarkan bot\n")

    @commands.command(aliases=['j','J'])
    async def join(self, ctx):

        if ctx.author.voice is None:
            return await ctx.send("Lu Belum Masuk Ke Voice Channel pe'ak")

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
        await ctx.send("Hallo Gaes .. ")
        await ctx.author.voice.channel.connect()
        queue_len = len(self.song_queue[ctx.guild.id])
        if queue_len == 0 :
            await asyncio.sleep(240) 
            await ctx.send("Ah lama banget request lagunya . gua chau dah ")
            await ctx.voice_client.disconnect()

    @commands.command(aliases=['l','L'])
    async def leave(self, ctx):
        if ctx.voice_client is not None:
            self.song_queue[ctx.guild.id].clear()
            await ctx.send("Makasih ye udah gunain gua , Im Chau")
            return await ctx.voice_client.disconnect()
        if ctx.voice_client is None:
            await ctx.send("Gua Belom Masuk Voice Channel cuy , Udah Disuruh Keluar Bae")

    @commands.command(aliases=['P','Play','p','PLAY'])
    async def play(self, ctx, *, song=None):
        queue_len = len(self.song_queue[ctx.guild.id])
        if ctx.author.voice is None:
            return await ctx.send("Lu belom masuk ke voice channel")
        if ctx.author.voice is not None:
          if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        if (ctx.voice_client.source is None) and (queue_len >0):
            self.song_queue[ctx.guild.id].clear()

        if song is None:
            return await ctx.send("Masukin Judul lagunya cok !")

        # handle song where song isn't url
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
 
            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Lagu lu engga ketemu , masukin yang jelas !")

            song = result[0]

        ''' Memasukkan Lagu Kedalam Antrian  '''
        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                self.song_queue[ctx.guild.id].append(song)
                await ctx.send(f"Lagunya lagi jalan , jangan di ganggu nunggu antrian dong , Antrian : {queue_len+1}.")
                embed = discord.Embed(title="Antrian Lagu", description="", colour=discord.Colour.dark_gold())
                i = 1
                for url in self.song_queue[ctx.guild.id]:

                    embed.description += f"{i}) {judulvideo(url)}\n"

                    i += 1

                ''' embed.set_footer(text="Makasih Ye udah gunain gua") '''
                await ctx.send(embed=embed)

            else:
                return await ctx.send("Banyak amat nyetel lagunya, udah 10 lagu nih lu play . tunggu yang lain selesai")

        ''' Program dilanjutkan ke fungsi play_song '''
        if ctx.voice_client.source is None:

          await self.play_song(ctx, song)

    @commands.command()
    async def search(self, ctx, *, song=None):
        if song is None: return await ctx.send("Masukin Judul Lagunya dong")

        await ctx.send("Bentar yak , lagunya lagi dicariin nih . maap otaknya agak lola")

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f"Hasil untuk lagu '{song}':", description="*Lu Bisa gunain link ini buat nyetel lagunya di internet*\n", colour=discord.Colour.red())
        
        amount = 0
        for entry in info["Antrian"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f"Menampilkan Tampilan paling atas {amount} hasil")
        await ctx.send(embed=embed)

    @commands.command()
    async def antrian(self, ctx): # display the current guilds queue
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("Kgk Ada antrian lagu , tambahin Gih biar ada")

        embed = discord.Embed(title="Antrian Lagu", description="", colour=discord.Colour.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            embed.description += f"{i}) {judulvideo(url)}\n"

            i += 1

        await ctx.send(embed=embed)

    @commands.command(aliases=["s","S"])
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("Gua lagi engga jalanin lagu apapun")

        if ctx.author.voice is None:
            return await ctx.send("Lu belom konek ke voice channel")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("Gua engga lagi nyetel lagu apaapun buat lu ")

        ''' poll = discord.Embed(title=f"Musyawarah dulu dong biar bisa skip - {ctx.author.name}#{ctx.author.discriminator}", description="**Harus 80% Suara dulu biar bisa diskip lagunya !**", colour=discord.Colour.blue())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Voting selesai dalam 15 detik")

        poll_msg = await ctx.send(embed=poll)
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") # 
        await poll_msg.add_reaction(u"\U0001F6AB") #
        
        await asyncio.sleep(10) 

        poll_msg = await ctx.channel.fetch_message(poll_id)
        
        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79: # 80% or higher
                skip = True
                embed = discord.Embed(title="Skip Successful", description="***Musyawarah buat skip lagunya biar mendapatkan hasil yang mufakat***", colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Skip Failed", description="*Voting minimal harus 80% dari jumlah anggota dong , biar bisa skip**", colour=discord.Colour.red())

        embed.set_footer(text="Yoi, Voting Selesai")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed) '''

        
        ctx.voice_client.stop()
        self.check_queue(ctx)

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client.is_paused():
            return await ctx.send("Gua Udah Pause Lagunya")

        ctx.voice_client.pause()
        await ctx.send("Lagunya Di Pause yak")

    @commands.command()
    async def start(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("Gua belum masuk ke voice channel, masukin dulu")

        if not ctx.voice_client.is_paused():
            return await ctx.send("Gua lagi nyetel lagu")
        
        ctx.voice_client.resume()
        await ctx.send("Lagunya udah disetel lagi")

async def setup():
    await bot.wait_until_ready()
    bot.add_cog(Player(bot))

bot.loop.create_task(setup())
keep_alive()
