import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging

# --- НАСТРОЙКИ ---
TOKEN = "MTU3MDQwNTAzMjAyODAxNjcwMQ.GKXOgF.xmNO8VOi0dP3aR884hyy7sSAdyZzS3gfv52dn0"

logging.basicConfig(level=logging.INFO)

# Настройки интентов
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Создаем класс бота
class PatriotBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Слэш-команды синхронизированы!")

bot = PatriotBot()

# --- СОБЫТИЕ ЗАПУСКА ---
@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен!')
    await bot.change_presence(activity=discord.Game(name="Гранд | Patriot"))

# --- КОМАНДА /help ---
@bot.tree.command(name="help", description="Показать список всех команд бота")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Patriot Bot | Список команд",
        description="Все доступные команды для управления сервером.",
        color=discord.Color.red()
    )
    embed.add_field(name="🛠️ Утилиты", value="`/echo` — написать сообщение от имени бота\n`/clean` — удалить сообщения (до 100)\n`/lockdown` — закрыть/открыть чат", inline=False)
    embed.add_field(name="📁 Разделы", value="`/createpost` — создать пост в форуме от имени бота\n`/deletepost` — удалить пост в форуме (пишется внутри поста)", inline=False)
    embed.set_footer(text="Patriot Bot | Сделано с душой для семьи")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- КОМАНДА /echo ---
@bot.tree.command(name="echo", description="Написать сообщение от имени бота")
@app_commands.describe(text="Текст сообщения", channel="Канал (по умолчанию текущий)")
async def echo(interaction: discord.Interaction, text: str, channel: discord.TextChannel = None):
    if channel is None:
        channel = interaction.channel
    
    await interaction.response.send_message("✅ Сообщение отправлено!", ephemeral=True)
    await channel.send(text)

# --- КОМАНДА /clean ---
@bot.tree.command(name="clean", description="Удалить последние сообщения в чате (до 100)")
@app_commands.describe(amount="Количество сообщений для удаления (1-100)")
async def clean(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Введи число от 1 до 100!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Удалено **{len(deleted)}** сообщений.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

# --- КОМАНДА /lockdown ---
@bot.tree.command(name="lockdown", description="Закрыть или открыть чат (только админы)")
@app_commands.describe(action="Закрыть или открыть")
@app_commands.choices(action=[
    app_commands.Choice(name="Закрыть", value="close"),
    app_commands.Choice(name="Открыть", value="open")
])
@app_commands.default_permissions(administrator=True)
async def lockdown(interaction: discord.Interaction, action: app_commands.Choice[str]):
    channel = interaction.channel
    everyone_role = interaction.guild.default_role
    overwrites = channel.overwrites_for(everyone_role)
    
    if action.value == "close":
        overwrites.send_messages = False
        await channel.set_permissions(everyone_role, overwrite=overwrites)
        await interaction.response.send_message("🔒 Канал закрыт. Писать могут только админы.")
    else:
        overwrites.send_messages = None
        await channel.set_permissions(everyone_role, overwrite=overwrites)
        await interaction.response.send_message("🔓 Канал открыт. Все могут писать.")

# --- КОМАНДА /createpost ---
@bot.tree.command(name="createpost", description="Создать пост в форуме от имени бота")
@app_commands.describe(
    forum="Выбери существующий форум",
    name="Название поста",
    description="Описание / текст поста"
)
@app_commands.default_permissions(administrator=True)
async def createpost(interaction: discord.Interaction, forum: discord.ForumChannel, name: str, description: str):
    await interaction.response.defer(ephemeral=True)
    
    try:
        await forum.create_thread(
            name=name,
            content=description,
            reason=f"Создано ботом для {interaction.user.name}"
        )
        await interaction.followup.send(f"✅ Пост **{name}** создан в форуме {forum.mention}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ У бота нет прав создавать посты в этом форуме!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

# --- КОМАНДА /deletepost ---
@bot.tree.command(name="deletepost", description="Удалить текущий пост в форуме (пишется внутри поста)")
@app_commands.default_permissions(administrator=True)
async def deletepost(interaction: discord.Interaction):
    # Проверяем, находится ли команда внутри треда (поста форума)
    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message("❌ Эту команду нужно писать внутри поста форума!", ephemeral=True)
        return

    # Проверяем, является ли этот тред постом именно в форуме (а не обычным тредом в чате)
    if interaction.channel.parent.type != discord.ChannelType.forum:
        await interaction.response.send_message("❌ Это не пост в форуме. Удаление отменено.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    try:
        # Удаляем тред (пост) целиком
        await interaction.channel.delete(reason=f"Пост удален ботом по команде {interaction.user.name}")
        # Отправлять followup после удаления канала нельзя, так что просто выходим
    except discord.Forbidden:
        await interaction.followup.send("❌ У бота нет прав удалять этот пост!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

# --- ЗАПУСК ---
async def main():
    print("Patriot Bot запускается...")
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())