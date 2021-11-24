import discord


def create_embed(
    title: str, desc: str, user: discord.Member, color: hex = 0x000001
):
    embed = discord.Embed(title=title, description=desc, color=color)
    embed.set_author(name=user, icon_url=user.avatar.url)

    embed.set_thumbnail(
        url="https://cdn.discordapp.com/app-icons/801483463642841150/4316132ab7deebe9b1bc93fc2fea576b.png"
    )
    return embed
