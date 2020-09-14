import discord, re, psutil, os, subprocess, time, asyncio, shutil, json, pathlib
from discord.ext import commands

with open(
    str(pathlib.Path(__file__).parent.absolute()) + "/kartbot_config.json", "r"
) as f:
    config = json.loads(f.read())

if not os.path.exists(config["server_folder_path"] + "tmp"):
    os.makedirs(config["server_folder_path"] + "tmp")

map_re = re.compile('Map is now "(.+)"')
node_re = re.compile(r"^\d+:\s+(.+) - \d+ - \d+")
action_re = re.compile(
    r"^((\*.+ entered the game\.)|(\*.+ left the game)|(\*.+ has joined the game \(node \d+\))|(\*.+ renamed to [^\n]+)|(\*.+ became a spectator\.)|(.+ has finished the race\.)|(.+ ran out of time\.)|(The round has ended\.)|(Speeding off to level\.\.\.)|(Map is now \"(.+)\"))"
)

bot = commands.Bot(command_prefix=config["prefix"], description=config["description"])

last_log_line = 0


async def chat_bridge():
    global last_log_line

    while True:
        with open(f"{config['server_folder_path']}log.txt", "r") as f:
            log = [l.strip() for l in f.readlines()]
            if last_log_line != 0:
                for line in log[last_log_line:]:
                    if line.startswith("<") and not line.startswith("<~SERVER> [D]"):
                        await bot.get_channel(config["chat_bridge_channel_id"]).send(
                            discord.utils.escape_mentions(line)
                        )
                    elif action_re.match(line) is not None:
                        await bot.get_channel(config["chat_bridge_channel_id"]).send(
                            discord.utils.escape_mentions(
                                "*"
                                + re.search(action_re, line).group(1).replace("*", "")
                                + "*"
                            )
                        )
            last_log_line = len(log)

        await asyncio.sleep(2)


async def delete_tmp():
    while True:
        files = [
            config["server_folder_path"] + "tmp/" + f
            for f in os.listdir(config["server_folder_path"] + "tmp")
        ]
        files.sort(key=os.path.getctime)
        for f in files[:-3]:
            os.system("rm " + f)
        await asyncio.sleep(10)


@bot.event
async def on_message(message):
    if message.channel.id == config["chat_bridge_channel_id"]:
        if message.author.id != bot.user.id:
            text = (
                message.clean_content.replace('"', "")
                .replace("^", "")
                .replace("\n", "")
                .replace(";", "")
            )
            path = config["server_folder_path"] + f"tmp/tmp{message.id}.cfg"
            with open(path, "w") as f:
                f.write(f"say [D] {message.author.name}: {text}")
            os.system(
                f"screen -S {config['screen_name']} -p 0 -X stuff \"exec tmp/tmp{message.id}.cfg^M\""
            )
    else:
        await bot.process_commands(message)


def is_admin(ctx):
    for role in ctx.author.roles:
        if role.name in config["admin_roles"]:
            return True
    return False


def is_helper(ctx):
    for role in ctx.author.roles:
        if role.name in config["helper_roles"] + config["admin_roles"]:
            return True
    return False


@bot.event
async def on_ready():
    print(f"Conectado como {bot.user.name} (id {bot.user.id})")
    if config["chat_bridge"]:
        bot.loop.create_task(chat_bridge())
        bot.loop.create_task(delete_tmp())


@bot.command(help="Manda o IP do servidor")
async def ip(ctx):
    await ctx.send(config["ip_message"])


@bot.command(help="Muda o gamemode do servidor para Race", checks=[is_helper])
async def race(ctx):
    os.system(
        f"screen -S {config['screen_name']} -p 0 -X stuff \"map map01 -gametype Race^Msay Gamemode mudado para Race^M\""
    )
    await ctx.send("Gamemode mudado para Race")


@bot.command(help="Reinicia o servidor", checks=[is_admin])
async def restart(ctx):
    os.system(f"pkill {config['server_executable_name']}")
    if config["enable_dkartconfig_corruption_workaround"]:
        try:
            shutil.copyfile(
                config["backup_dkartconfig_path"], config["dkartconfig_path"]
            )  # copies config backup over original config file, incase the original file gets corrupted
        except FileNotFoundError:
            print("Não foi possível copiar o backup do dkartconfig")
    os.system(
        f"screen -dmS {config['screen_name']} {config['server_folder_path']}{config['server_executable_name']} {config['server_executable_args']}"
    )
    await ctx.send("Servidor reiniciado")


@bot.command(
    help="Executa um comando no servidor", checks=[is_admin], aliases=["comando"]
)
async def command(ctx, *, cmd):
    text = cmd.replace('"', "").replace("^", "").replace("\n", "").replace(";", "")
    path = config["server_folder_path"] + f"tmp/tmp{ctx.message.id}.cfg"
    with open(path, "w") as f:
        f.write(text)
    os.system(
        f"screen -S {config['screen_name']} -p 0 -X stuff \"exec tmp/tmp{ctx.message.id}.cfg^M\""
    )
    await ctx.send("Comando executado")


@bot.command(help="Muda o gamemode do servidor para Battle", checks=[is_helper])
async def battle(ctx):
    os.system(
        f"screen -S {config['screen_name']} -p 0 -X stuff \"map mapb0 -gametype 1^Msay Gamemode mudado para Battle^M\""
    )
    await ctx.send("Gamemode mudado para Battle")


@race.error
@battle.error
async def admin_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send(config["permission_error_message"])


@bot.command(
    help="Manda informações sobre o servidor e os jogadores conectados",
    aliases=["info", "players"],
)
async def status(ctx):
    status = "ON"
    uptime = 0

    try:
        pid = int(
            subprocess.check_output(["pidof", config["server_executable_name"]]).split(
                b" "
            )[0]
        )
        process = psutil.Process(pid)
        uptime = time.time() - process.create_time()
    except subprocess.CalledProcessError:
        status = "OFF"

    state = 0
    players = []
    specs = []
    map_ = "???"

    if status == "ON":
        os.system(
            f"screen -S {config['screen_name']} -p 0 -X stuff \"nodes^Mversion^M\""
        )

        await asyncio.sleep(0.5)

        for _ in range(5):
            with open(f"{config['server_folder_path']}log.txt", "r") as f:
                log = f.read().split("\n")[::-1]
                state = 0
                for line in log:
                    if state == 0:
                        if line.startswith("SRB2Kart"):
                            state = 1
                    elif state == 1:
                        match = node_re.match(line)
                        if match is not None:
                            if line[-1] == ")":
                                specs.append(match.group(1))
                            else:
                                players.append(match.group(1))
                        elif line.startswith("$nodes"):
                            state = 2
                    elif state == 2:
                        for line in log:
                            match = map_re.match(line)
                            if match is not None:
                                map_ = match.group(1)
                                break
                        break
                if state == 2:
                    break
                else:
                    continue
    else:
        state = 2

    if state == 2:
        if len(players) + len(specs) == 0:
            formatted_players = "\u200B"
        else:
            formatted_players = "· " + "\n· ".join(
                players + list(map(lambda x: f"*{x}*", specs))
            )
        formatted_uptime = (
            f"{int(uptime/60/60):02}:{int(uptime/60%60):02}:{int(uptime%60):02}"
        )

        embed = discord.Embed(color=0x00FF00 if status == "ON" else 0xFF0000)
        embed.add_field(
            name="Status", value="✅ ON" if status == "ON" else "❌ OFF", inline=True
        )
        embed.add_field(name="Uptime", value=formatted_uptime, inline=True)
        embed.add_field(name="\u200B", value="\u200B", inline=True)
        embed.add_field(name="CPU", value=f"{psutil.cpu_percent()}%", inline=True)
        embed.add_field(
            name="RAM", value=f"{psutil.virtual_memory().percent}%", inline=True
        )
        embed.add_field(name="\u200B", value="\u200B", inline=True)
        if status == "ON":
            embed.add_field(name="Mapa", value=map_, inline=True)
            embed.add_field(
                name=f"{len(players)+len(specs)}/{config['server_max_players']} players:",
                value=discord.utils.escape_mentions(formatted_players),
                inline=False,
            )

        await ctx.send(embed=embed)
    else:
        await ctx.send("Não foi possível ler o log do servidor")


bot.run(config["token"])
