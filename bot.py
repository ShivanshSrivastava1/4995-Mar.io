import random
import datetime
import typing as t
import hikari
from hikari.impl import MessageActionRowBuilder
import lightbulb
from lightbulb import commands

token = '' # Paste bot token here
test_guilds = () # Paste server IDs here (as a tuple)

bot = lightbulb.BotApp(
        token=token,
        intents=hikari.Intents.ALL,
        default_enabled_guilds=test_guilds,
)

PERMISSIONS = (
    hikari.Permissions.VIEW_CHANNEL,
    hikari.Permissions.CONNECT,
    hikari.Permissions.SPEAK,
)

POKEMON: t.Mapping[str, t.Tuple[int, str]] = {
    "Charizard (Red)": (
        0xFF0000,
        "Breathing intense, hot flames, it can melt almost anything. Its breath inflicts terrible pain on enemies.",
    ),
    "Venusaur (Green)": (
        0x00FF00,
        "The plant blooms when it is absorbing solar energy. It stays on the move to seek sunlight.",
    ),
    "Blastoise (Blue)": (
        0x0000FF,
        "The jets of water it spouts from the rocket cannons on its shell can punch through thick steel.",
    ),
    "Koraidon (Scarlet)": (0xFFA500, "This seems to be the Winged King mentioned in an old expedition journal. It was said to have split the land with its bare fists."),
    "Miraidon (Violet)": (
        0xA020F0,
        "This seems to be the Iron Serpent mentioned in an old book. The Iron Serpent is said to have turned the land to ash with its lightning.",
    ),
    "Pikachu (Yellow)": (
        0xFFFF00,
        "This forest-dwelling Pokémon stores electricity in its cheeks, so you'll feel a tingly shock if you touch it.",
    ),
    "Reshiram (Black)": (0x000000, "This legendary Pokémon can scorch the world with fire. It helps those who want to build a world of truth."),
    "Zekrom (White)": (0xFFFFFF, "This legendary Pokémon can scorch the world with lightning. It assists those who want to build an ideal world."),
}


async def generate_rows(bot: lightbulb.BotApp) -> t.Iterable[MessageActionRowBuilder]:

    rows: t.List[MessageActionRowBuilder] = []

    row = bot.rest.build_message_action_row()

    for i in range(len(POKEMON)):
        if i % 4 == 0 and i != 0:
            rows.append(row)
            row = bot.rest.build_message_action_row()

        label = list(POKEMON)[i]

        (
            row.add_button(
                hikari.ButtonStyle.SECONDARY,
                label,
            )

            .set_label(label)
            .add_to_container()
        )

    rows.append(row)

    return rows


async def handle_responses(
    bot: lightbulb.BotApp,
    author: hikari.User,
    message: hikari.Message,
) -> None:

    with bot.stream(hikari.InteractionCreateEvent, 120).filter(

        lambda e: (
            isinstance(e.interaction, hikari.ComponentInteraction)
            and e.interaction.user == author
            and e.interaction.message == message
        )
    ) as stream:
        async for event in stream:
            pid = event.interaction.custom_id

            embed = hikari.Embed(
                title=pid,
                color=POKEMON[pid][0],
                description=POKEMON[pid][1],
            )

            try:
                await event.interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_UPDATE,
                    embed=embed,
                )
            except hikari.NotFoundError:
                await event.interaction.edit_initial_response(
                    embed=embed,
                )

    await message.edit(
        components=[]
    )

@bot.listen(hikari.GuildMessageCreateEvent)
async def echo(event):
    print(event.content)

@bot.listen(hikari.StartedEvent)
async def bot_started(event):
    print('Bot has started!')

@bot.command
@lightbulb.command('ping', 'Says pong!')
@lightbulb.implements(lightbulb.SlashCommand)
async def ping(ctx):
    await ctx.respond('Pong!')

@bot.command
@lightbulb.command('group', 'This is a group')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def my_group(ctx):
    pass

@my_group.child
@lightbulb.command('subcommand', 'This is a subcommand')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def subcommand(ctx):
    await ctx.respond('I am a subcommand!')

@bot.command
@lightbulb.option('num2', 'The second number', type=int)
@lightbulb.option('num1', 'The first number', type=int)
@lightbulb.command('add', 'Add two numbers together')
@lightbulb.implements(lightbulb.SlashCommand)
async def add(ctx):
    await ctx.respond(ctx.options.num1 + ctx.options.num2)

@bot.command
@lightbulb.option("bonus", "A fixed number to add to the total roll.", int, default=0)
@lightbulb.option("sides", "The number of sides each die will have.", int, default=6)
@lightbulb.option("number", "The number of dice to roll.", int)
@lightbulb.command("dice", "Roll one or more dice.")
@lightbulb.implements(commands.SlashCommand)
async def dice(ctx: lightbulb.context.Context) -> None:
    number = ctx.options.number
    sides = ctx.options.sides
    bonus = ctx.options.bonus

    if number > 25:
        await ctx.respond("No more than 25 dice can be rolled at once.")
        return

    if sides > 100:
        await ctx.respond("The dice cannot have more than 100 sides.")
        return

    rolls = [random.randint(1, sides) for _ in range(number)]

    await ctx.respond(
        " + ".join(f"{r}" for r in rolls)
        + (f" + {bonus} (bonus)" if bonus else "")
        + f" = **{sum(rolls) + bonus:,}**"
    )

@bot.command
@lightbulb.option("target", "The member to get information about.", hikari.Member)
@lightbulb.command("userinfo", "Get info on a server member.")
@lightbulb.implements(commands.SlashCommand)
async def user_info(ctx: lightbulb.context.Context) -> None:
    target_ = ctx.options.target
    target = (
        target_
        if isinstance(target_, hikari.Member)
        else ctx.get_guild().get_member(target_)
    )
    if not target:
        await ctx.respond("That user is not in the server.")
        return

    created_at = int(target.created_at.timestamp())
    joined_at = int(target.joined_at.timestamp())
    roles = (await target.fetch_roles())[1:]

    embed = (
        hikari.Embed(
            title="User Information",
            description=f"ID: {target.id}",
            colour=hikari.Colour(0x563275),
            timestamp=datetime.datetime.now().astimezone(),
        )
        .set_footer(
            text=f"Requested by {ctx.member.display_name}",
            icon=ctx.member.avatar_url,
        )
        .set_thumbnail(target.avatar_url)

        .add_field(name="Discriminator", value=target.discriminator, inline=True)
        .add_field(name="Bot?", value=target.is_bot, inline=True)
        .add_field(name="No. of roles", value=len(roles), inline=True)
        .add_field(
            name="Created on",
            value=f"<t:{created_at}:d> (<t:{created_at}:R>)",
            inline=False,
        )
        .add_field(
            name="Joined on",
            value=f"<t:{joined_at}:d> (<t:{joined_at}:R>)",
            inline=False,
        )
        .add_field(name="Roles", value=" | ".join(r.mention for r in roles))
    )

    await ctx.respond(embed)

@bot.command()
@lightbulb.option("reason", "Reason for the ban", required=False)
@lightbulb.option("user", "The user to ban.", type=hikari.User)
@lightbulb.command("ban", "Ban a user from the server.")
@lightbulb.implements(lightbulb.SlashCommand)
async def ban(ctx: lightbulb.SlashContext) -> None:
    if not ctx.guild_id:
        await ctx.respond("This command can only be used in a guild.")
        return

    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
    await ctx.app.rest.ban_user(ctx.guild_id, ctx.options.user.id, reason=ctx.options.reason or hikari.UNDEFINED)
    await ctx.respond(f"Banned {ctx.options.user.mention}.\n**Reason:** {ctx.options.reason or 'No reason provided.'}")


@bot.command()
@lightbulb.option("count", "The amount of messages to purge.", type=int, max_value=100, min_value=1)
@lightbulb.command("purge", "Purge a certain amount of messages from a channel.", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def purge(ctx: lightbulb.SlashContext, count: int) -> None:
    """Purge a certain amount of messages from a channel."""
    if not ctx.guild_id:
        await ctx.respond("This command can only be used in a server.")
        return
        
    messages = (
        await ctx.app.rest.fetch_messages(ctx.channel_id)
        .take_until(lambda m: datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14) > m.created_at)
        .limit(count)
    )
    if messages:
        await ctx.app.rest.delete_messages(ctx.channel_id, messages)
        await ctx.respond(f"Purged {len(messages)} messages.")
    else:
        await ctx.respond("Could not find any messages younger than 14 days!")

@bot.command()
@lightbulb.command("dex", "Get facts on different mascot Pokémon!", guilds=test_guilds)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def rgb_command(ctx: lightbulb.Context) -> None:
    """Get facts on different mascot Pokémon!"""

    rows = await generate_rows(ctx.bot)

    response = await ctx.respond(
        hikari.Embed(title="Pick a Pokémon"),
        components=rows,
    )
    message = await response.message()

    await handle_responses(ctx.bot, ctx.author, message)

# bot.load_extensions_from('./extensions')

bot.run()