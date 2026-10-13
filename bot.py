import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio

from config import DISCORD_TOKEN, BRIXHUB_API_KEY, BRIXHUB_API_URL, FREE_SEARCHES_PER_DAY
import db

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    db.init_db()
    await tree.sync()
    print(f"[+] Bot online — {bot.user}")


async def query_brixhub(query: str) -> dict:
    headers = {
        "Authorization": f"Bearer {BRIXHUB_API_KEY}",
        "Content-Type": "application/json",
    }
    params = {"q": query}
    async with aiohttp.ClientSession() as session:
        async with session.get(BRIXHUB_API_URL, headers=headers, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            return {"error": f"API returned {resp.status}"}


def build_result_embed(data: dict, query: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"🔍 BrixHub — `{query}`",
        color=0x2B2D31,
    )

    fields_map = {
        "first_name": "👤 Prénom",
        "last_name": "👤 Nom",
        "full_name": "👤 Nom complet",
        "address": "🏠 Adresse",
        "email": "📧 Email",
        "phone": "📞 Téléphone",
        "dob": "🎂 Date de naissance",
        "ip": "🌐 IP",
        "username": "🆔 Username",
        "password": "🔑 Password",
    }

    results = data.get("results", [data])
    if not isinstance(results, list):
        results = [results]

    for i, result in enumerate(results[:5], 1):
        lines = []
        for key, label in fields_map.items():
            val = result.get(key)
            if val:
                lines.append(f"**{label}:** `{val}`")
        if lines:
            embed.add_field(
                name=f"Result #{i}",
                value="\n".join(lines),
                inline=False,
            )

    if not embed.fields:
        embed.description = "Aucun résultat trouvé."

    embed.set_footer(text="BrixHub Searcher • powered by AR-AI")
    return embed


@tree.command(name="search", description="Cherche une personne sur BrixHub")
@app_commands.describe(query="Nom, email, numéro, adresse...")
async def search(interaction: discord.Interaction, query: str):
    user_id = str(interaction.user.id)

    if not db.can_search(user_id, FREE_SEARCHES_PER_DAY):
        user = db.get_user(user_id)
        remaining = FREE_SEARCHES_PER_DAY - user["searches_today"]
        embed = discord.Embed(
            title="❌ Limite atteinte",
            description=(
                f"Tu as utilisé tes **{FREE_SEARCHES_PER_DAY} recherches gratuites** pour aujourd'hui.\n\n"
                "Pour un accès **illimité**, utilise `/ticket` et règle le paiement.\n"
                "Un admin te donnera l'accès premium."
            ),
            color=0xFF4444,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)

    data = await query_brixhub(query)

    if "error" in data:
        embed = discord.Embed(
            title="⚠️ Erreur API",
            description=f"`{data['error']}`",
            color=0xFF8800,
        )
        await interaction.followup.send(embed=embed)
        return

    db.increment_search(user_id)
    user = db.get_user(user_id)
    is_premium = user["is_premium"] == 1
    searches_left = "∞" if is_premium else str(FREE_SEARCHES_PER_DAY - user["searches_today"])

    embed = build_result_embed(data, query)
    embed.set_footer(text=f"BrixHub Searcher • Searches restantes aujourd'hui : {searches_left}")

    await interaction.followup.send(embed=embed)


@tree.command(name="ticket", description="Ouvre un ticket pour obtenir l'accès premium illimité")
async def ticket(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    username = str(interaction.user)

    ticket_id = db.open_ticket(user_id, username)

    embed = discord.Embed(
        title="🎫 Ticket ouvert",
        description=(
            f"Ton ticket **#{ticket_id}** a été créé.\n\n"
            "Un admin va te contacter pour le paiement.\n"
            "Une fois payé, ton compte sera passé en **Premium illimité**."
        ),
        color=0x5865F2,
    )
    embed.set_footer(text=f"Ticket ID: {ticket_id} • {username}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="status", description="Vérifie ton statut et tes recherches restantes")
async def status(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    db.reset_if_new_day(user_id)
    user = db.get_user(user_id)

    if user is None:
        searches_done = 0
        is_premium = False
    else:
        searches_done = user["searches_today"]
        is_premium = user["is_premium"] == 1

    searches_left = "∞" if is_premium else str(max(0, FREE_SEARCHES_PER_DAY - searches_done))
    tier = "💎 Premium" if is_premium else "🆓 Gratuit"

    embed = discord.Embed(title="📊 Ton statut", color=0x57F287 if is_premium else 0x99AAB5)
    embed.add_field(name="Tier", value=tier, inline=True)
    embed.add_field(name="Searches aujourd'hui", value=str(searches_done), inline=True)
    embed.add_field(name="Restantes", value=searches_left, inline=True)
    embed.set_footer(text=f"User: {interaction.user}")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="setpremium", description="[ADMIN] Passe un user en premium")
@app_commands.describe(user="L'utilisateur à passer premium")
@app_commands.checks.has_permissions(administrator=True)
async def setpremium(interaction: discord.Interaction, user: discord.Member):
    db.set_premium(str(user.id))
    embed = discord.Embed(
        title="✅ Premium activé",
        description=f"{user.mention} est maintenant **Premium illimité**.",
        color=0x57F287,
    )
    await interaction.response.send_message(embed=embed)


@tree.command(name="closeticket", description="[ADMIN] Ferme un ticket par son ID")
@app_commands.describe(ticket_id="ID du ticket à fermer")
@app_commands.checks.has_permissions(administrator=True)
async def closeticket(interaction: discord.Interaction, ticket_id: int):
    db.close_ticket(ticket_id)
    embed = discord.Embed(
        title="🔒 Ticket fermé",
        description=f"Ticket **#{ticket_id}** marqué comme fermé.",
        color=0xFEE75C,
    )
    await interaction.response.send_message(embed=embed)


@setpremium.error
@closeticket.error
async def admin_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ Permissions insuffisantes.", ephemeral=True)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
