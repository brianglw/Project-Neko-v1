import discord
import datetime
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()



class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}')

        try:
            guild = discord.Object(id=1516166946830417940)
            synced = await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if message.content.startswith('hello'):
            await message.channel.send(f'Hi there {message.author}')

    async def on_reaction_add(self, reaction, user):
        await reaction.message.channel.send("You reacted")

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="/", intents=intents)

GUILD_ID = discord.Object(id=1516166946830417940)

class View(discord.ui.View):
    @discord.ui.button(label="Which color is your favorite?", style=discord.ButtonStyle.red, emoji="🔥")
    async def button_callback(self, button, interaction):
        await button.response.send_message("Thanks for clicking the button!")

class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=180)
    
    @discord.ui.button(label="Mega Raichu Y",style=discord.Color.red)
    async def orange_button(self,button:discord.ui.Button, interaction:discord.Interaction):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Mega Metagross",style=discord.Color.blue)
    async def blue_button(self,button:discord.ui.Button, interaction:discord.Interaction):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Mega Staraptor",style=discord.Color.red)
    async def grey_button(self,button:discord.ui.Button, interaction:discord.Interaction):
        await interaction.response.edit_message(view=self)



# WRITE AN EMBED CLASS CONTAINING A QUIZ POLL. PRINT OUT EACH RESPONSE IN TERMINAL #
class Embed(discord.Embed):
    def __init__(self,title, desc, color, timestamp):
        super().__init__(title=title,description=desc,color=color,timestamp=timestamp)
    
    def set_thumbnail(self,url):
        super().set_thumbnail(url=url)

    def add_field(self,name,value,isInline):
        super().add_field(name=name,value=value,inline=isInline)


    

@client.tree.command(name="hello", description="say hello", guild=GUILD_ID)
async def greeting(interaction: discord.Interaction):
    await interaction.response.send_message("g'day!")

@client.tree.command(name="printer", description="outputs whatever you write into a channel", guild=GUILD_ID)
async def printer(interaction: discord.Interaction, printer: str):
    await interaction.response.send_message(printer)

@client.tree.command(name="embed", description="Embed demo", guild=GUILD_ID)
async def printer(interaction: discord.Interaction):
    embed = Embed(title="Who is the best Mega Pokemon of Regulation M-B?", desc="Choose one", color=discord.Color.random(),timestamp=datetime.datetime.now())
    embed.set_thumbnail(url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fwww.enduins.com%2Fwp-content%2Fuploads%2F2025%2F09%2Fmega-raichu-1024x576.jpg&f=1&nofb=1&ipt=bb39ac0573f7f53b7f9f69ef2c10823106a68e6e2d11573489a5a0027eaf2614")
    buttons = Buttons()

    await interaction.response.send_message(embed=embed, view=buttons)



@client.tree.command(name="button", description="displays a button with choices", guild=GUILD_ID)
async def printer(interaction: discord.Interaction):
    await interaction.response.send_message(view=View())

client.run(os.environ['DISCORD_BOT_TOKEN'])