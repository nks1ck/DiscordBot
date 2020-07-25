import discord
from discord.ext import commands
import sqlite3
import random
import datetime

TOKEN = 'NzM2MzIxMDY4ODg0Njg4OTcx.XxtGbw.T1Jtljz8liMFcROQIDc7aZFtMVE'

client = commands.Bot(command_prefix='.')
client.remove_command('help')

# connection for db
connection = sqlite3.connect('server.db')
cursor = connection.cursor()


@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=100):
    await ctx.channel.purge(limit=amount)


@client.event
async def on_ready():
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    name TEXT,
    id INT,
    cash BIGINT,
    rep INT,
    lvl INT,
    server_id INT
  )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS shop (
        role_id INT,
        id INT,
        cost BIGINT
    )""")

    for guild in client.guilds:
        for member in guild.members:
            if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0, 1, {guild.id})")
            else:
                pass
    connection.commit()
    print('Bot connected')


@client.event
async def on_member_join(member):
    if cursor.execute(f'SELECT id FROM users WHERE id = {member.id}').fetchone() in None:
        cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0, 1, {member.guild.id})")
        connection.commit()
    else:
        pass


@client.command(aliases=['balance', 'cash'])
async def __balance(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(embed=discord.Embed(
            description=f"""Баланc пользователя **{ctx.author}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :leaves:**"""
        ))
    else:
        await ctx.send(embed=discord.Embed(
            description=f"""Баланc пользователя **{member}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]} :leaves:**"""
        ))


@client.command(aliases=['award'])
@commands.has_permissions(administrator=True)
async def __award(ctx, member: discord.Member = None, amount: int = None):
    if member is None:
        await ctx.send(f"**{ctx.author}**, укажите пользователя, которому желаете выдать деньги ")
    else:
        if amount is None:
            await ctx.send(f"**{ctx.author}**, укажите сумму, которую хотите начислить")
        elif amount < 1:
            await ctx.send(f"**{ctx.author}**, укажите сумму больше")
        else:
            cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
            connection.commit()

            await ctx.message.add_reaction("✅")


@client.command(aliases=['take'])
@commands.has_permissions(administrator=True)
async def __take(ctx, member: discord.Member = None, amount=None):
    if member is None:
        await ctx.send(f"**{ctx.author}**, укажите пользователя, у которого желаете снять деньги")
    else:
        if amount is None:
            await ctx.send(f"**{ctx.author}**, укажите сумму, которую хотите снять у пользователя")
        elif amount == 'all':
            cursor.execute("UPDATE users SET cash = {} WHERE id = {}".format(0, member.id))
            connection.commit()
        elif int(amount) < 1:
            await ctx.send(f"**{ctx.author}**, укажите сумму больше")
        else:
            cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(int(amount), member.id))
            connection.commit()

            await ctx.message.add_reaction("✅")


@client.command(aliases=['add-shop'])
@commands.has_permissions(administrator=True)
async def __add_shop(ctx, role: discord.Role = None, cost: int = None):
    if role is None:
        await ctx.send(f"**{ctx.author}**, укажите роль, которую вы желаете внести в магазин")
    else:
        if cost is None:
            await ctx.send(f"**{ctx.author}**, укажите роль, которую вы желаете внести в магазин")
        elif cost < 0:
            await ctx.send(f"**{ctx.author}**, стоимость роли не может быть такой маленькой")
        else:
            cursor.execute("INSERT INTO shop VALUES ({}, {}, {})".format(role.id, ctx.guild.id, cost))
            connection.commit()

            await ctx.message.add_reaction("✅")


@client.command(aliases=['remove-shop'])
@commands.has_permissions(administrator=True)
async def __remove_shop(ctx, role: discord.Role = None, ):
    if role is None:
        await ctx.send(f"**{ctx.author}**, укажите роль, которую вы желаете убрать из магазина")
    else:
        cursor.execute("DELETE FROM shop WHERE role_id = {}".format(role.id))
        connection.commit()

        await ctx.message.add_reaction("✅")


@client.command(aliases=['shop'])
async def __shop(ctx):
    embed = discord.Embed(title='Магазин ролей')

    for row in cursor.execute("SELECT role_id, cost FROM shop WHERE id = {}".format(ctx.guild.id)):
        if ctx.guild.get_role(row[0]) is not None:
            embed.add_field(
                name=f"Стоимость: {row[1]}",
                value=f"Вы приобретаете роль {ctx.guild.get_role(row[0]).mention}",
                inline=False
            )
        else:
            pass

    await ctx.send(embed=embed)


@client.command(aliases=['buy', 'buy-role'])
async def __buy(ctx, role: discord.Role = None):
    if role is None:
        await ctx.send(f"**{ctx.author}**, укажите роль, которую хотите приобрести")
    else:
        if role in ctx.author.roles:
            await ctx.send(f'**{ctx.author}**, у вас уже имеется данная роль')
        elif cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0] > \
                cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]:
            await ctx.send(f'**{ctx.author}**, у вас не хватает средств на покупку данной роли')
        else:
            await ctx.author.add_roles(role)
            cursor.execute("UPDATE users SET cash = cash - {0} WHERE id = {1}".format(
                cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0],
                ctx.author.id))

            await ctx.message.add_reaction("✅")
            await ctx.channel.purge(limit=1)


@client.command(aliases=['rep', '+rep'])
async def __rep(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(f"**{ctx.author}**, укажите участника сервера")
    else:
        if member.id == ctx.author.id:
            await ctx.send(f"**{ctx.author}**, вы не можете указать самого себя =)")
        else:
            cursor.execute("UPDATE users SET rep = rep + {} WHERE id = {}".format(1, member.id))
            connection.commit()

            await ctx.message.add_reaction("✅")
            await ctx.channel.purge(limit=1)


@client.command(aliases=['leaderboard', 'lb'])
async def __leaderboard(ctx):
    embed = discord.Embed(title='Топ 10 сервера')
    counter = 0

    for row in cursor.execute("SELECT name, cash FROM users WHERE server_id = {} ORDER BY cash DESC LIMIT 10".format(ctx.guild.id)):
        counter += 1
        embed.add_field(
            name=f'# {counter} | {row[0]}',
            value=f'Баланс: {row[1]}',
            inline=False,
        )

    await ctx.channel.purge(limit=1)
    await ctx.send(embed=embed)


@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await ctx.channel.purge(limit=1)

    await member.kick(reason=reason)

    await ctx.send(f'User {member.mention} kicked')


@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    emb = discord.Embed(title='Ban', color=discord.Color.red())
    await ctx.channel.purge(limit=1)

    await member.ban(reason=reason)

    emb.set_author(name=member.name, icon_url=member.avatar_url)
    emb.add_field(name='User ban', value='Banned user : {}'.format(member.mention))
    emb.set_footer(text='Был забанен администратором {}'.format(ctx.author.name), icon_url=ctx.author.avatar_url)

    await ctx.send(embed=emb)


# unban user
@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def unban(ctx, *, member):
    await ctx.channel.purge(limit=1)

    banned_users = await ctx.guild.bans()

    for ban_entry in banned_users:
        user = ban_entry.user

        await ctx.guild.unban(user)
        await ctx.send(f'User {user.mention} unbanned')

        return


@client.command()
@commands.has_permissions(administrator=True)
async def user_mute(ctx, member: discord.Member):
    await ctx.channel.purge(limit=1)

    mute_role = discord.utils.get(ctx.message.guild.roles, name='MUTE')

    await member.add_roles(mute_role)
    await ctx.send(f'{member.mention} улетел(а) в мут')


@client.command(pass_context=True)
async def commands(ctx):
    embed = discord.Embed(title='Навигация по командам бота')

    embed.add_field(name='{}balance or cash'.format('.'), value='Проверка вашего или чужого баланса')
    embed.add_field(name='{}rep'.format('.'), value='Поднять репутацию на сервере')
    embed.add_field(name='{}leaderboard'.format('.'), value='Таблица лидеров по репутации и сумме на балансе')
    embed.add_field(name='{}shop'.format('.'), value='Посмотреть доступные для покупки роли')
    await ctx.channel.purge(limit=1)

    await ctx.send(embed=embed)


@client.command(pass_context=True)
async def helpadmin(ctx):
    embed = discord.Embed(title='Навигация по командам для администраторов')

    embed.add_field(name='{}clear'.format('.'), value='Очистка чата')
    embed.add_field(name='{}kick'.format('.'), value='Удаление участника с сервера')
    embed.add_field(name='{}ban'.format('.'), value='Ограничение доступа к серверу')
    embed.add_field(name='{}unban'.format('.'), value='Удаление ограничений доступа к серверу')
    embed.add_field(name='{}award'.format('.'), value='Выдача денег юзеру')
    embed.add_field(name='{}add-shop'.format('.'), value='Добавить роль в магазин')
    embed.add_field(name='{}remove-shop'.format('.'), value='Убрать роль из магазина')
    embed.add_field(name='{}take'.format('.'), value='Забрать деньги у юзера')
    await ctx.channel.purge(limit=1)

    await ctx.send(embed=embed)


@client.command(pass_context=True)
async def time(ctx):
    emb = discord.Embed(title='Current Time', color=discord.Color.blue(),
                        url='https://www.timeserver.ru/cities/ru/moscow')
    await ctx.channel.purge(limit=1)

    emb.set_author(name=client.user.name, icon_url=client.user.avatar_url)
    emb.set_footer(text='Лучший бот за работой')
    # emb.set_image(url='https://s1.iconbird.com/ico/2013/12/505/w450h4001385925290Alarm.png')
    emb.set_thumbnail(url='https://s1.iconbird.com/ico/2013/12/505/w450h4001385925290Alarm.png')

    now_date = datetime.datetime.now()
    emb.add_field(name='Time', value='Time : {}'.format(now_date))

    await ctx.send(embed=emb)

client.run(TOKEN)
