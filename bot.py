import discord
from discord.ext import commands
from config.key import token
from config import const
from time import sleep
from funcs import teacher_datamanagement, student_datamanagement, send_verification_email
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(intents=intents, command_prefix='!')
TOKEN = token.get('TOKEN')


# O bot é ligado
@client.event
async def on_ready():
    print(f'{client.user} está online!')


# Funcao timer para deletar o chat depois de 15 minutos
async def timer(channel, member):
    await asyncio.sleep(870)
    await channel.send(const.tempo_chat_expirado)
    await asyncio.sleep(30)
    await channel.delete()
    await member.kick()


# Quando um novo membro entrar no server
@client.event
async def on_member_join(member):
    # Função de dar cargo
    async def add_role(role_name):
        role = discord.utils.get(member.guild.roles, name=role_name)
        await member.add_roles(role)

    # Função remover cargo pretendente
    async def remove_role(role_name):
        role = discord.utils.get(member.guild.roles, name=role_name)
        await member.remove_roles(role)

    await add_role(const.pretendente)

    overwrites = {
        member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        client.user: discord.PermissionOverwrite(read_messages=True)

    }

    # Aqui será criado canal de autenticação privado
    canal_autenticacao = await member.guild.create_text_channel(const.canal_autenticacao, overwrites=overwrites)
    # inicia o timer
    timer_task = asyncio.create_task(timer(canal_autenticacao, member))

    sleep(0.5)
    await canal_autenticacao.send(const.msg_bem_vindo)
    sleep(0.5)
    await canal_autenticacao.send('\n\u200B')
    await canal_autenticacao.send(const.msg_pede_email)

    async def invalid_attempt(attempt):
        if attempt < 3:
            await canal_autenticacao.send(const.msg_email_nao_encontrado)

        else:
            await canal_autenticacao.send(const.msg_nao_possui_email)
            sleep(0.5)
            await member.kick()
            await canal_autenticacao.delete()

    async def attempts(email, type):
        for attempt_email in range(1, 4):
            if type == const.tipo_estudante:
                email_type, name = student_datamanagement(email)
            else:
                email_type, name = teacher_datamanagement(email)

            if email_type:
                await canal_autenticacao.send(const.msg_email_enviado)
                code = send_verification_email(email)

                # Tentativas de enviar o código
                for attempt_code in range(1, 4):
                    response_code = await client.wait_for(
                        const.message,
                        check=lambda m: m.author == member and m.channel == canal_autenticacao,
                        timeout=900
                    )

                    if response_code.content == code:
                        await canal_autenticacao.send(const.msg_entrou)
                        await member.edit(nick=name)
                        break
                    elif attempt_code < 3:
                        await canal_autenticacao.send(const.msg_codigo_invalido)
                    else:
                        await canal_autenticacao.send(const.msg_fim_das_tent)
                        sleep(0.5)
                        await member.kick()
                        await canal_autenticacao.delete()
                break
            else:
                await invalid_attempt(attempt_email)

            response_email = await client.wait_for(
                const.message,
                check=lambda m: m.author == member and m.channel == canal_autenticacao,
                timeout=900
            )
            email = response_email.content.lower()
            email_type = student_datamanagement(email)

    # Será solicitado seu e-mail
    for attempt in range(1, 4):
        response_email = await client.wait_for(const.message,
                                               check=lambda m: m.author == member and m.channel == canal_autenticacao,
                                               timeout=900)
        email = response_email.content.lower()

        # Verificar se é e-mail de aluno
        if const.formato_email_estudante in email:
            await attempts(email=email, type=const.tipo_estudante)
            if member.guild.get_member(member.id) is not None:
                await add_role(const.aluno)
                await remove_role(const.pretendente)
                await canal_autenticacao.delete()
                timer_task.cancel()
                break
            else:
                break

        # Verificar se é e-mail de professor
        elif const.formato_email_professor in email:
            await attempts(email=email, type=const.tipo_professor)
            if member.guild.get_member(member.id) is not None:
                await add_role(const.professor)
                await remove_role(const.pretendente)
                await canal_autenticacao.delete()
                timer_task.cancel()
                break
            else:
                break

        else:
            await invalid_attempt(attempt)


@client.command(description=const.criar_canal)
async def criar(ctx):
    if ctx.author == client.user:
        return

    member_role = ctx.author.roles[1].name

    await ctx.author.send(const.msg_comeco_criacao_canal)
    try:
        channel_name = f'Canal do {ctx.author.nick.split()[0]}'

        if member_role != const.aluno:
            embed = discord.Embed(
                title=const.criar_canal,
                description=const.informar_nome_canal,
                color=discord.Color.brand_green()
            )
            await ctx.author.send(embed=embed)

            while True:
                # Aguarda a mensagem do usuário por 60 segundos
                response_channel_name = await client.wait_for(
                    const.message,
                    check=lambda m: m.author == ctx.author and isinstance(
                        m.channel, discord.DMChannel),
                    timeout=120
                )

                channel_name = response_channel_name.content

                embed.description = const.confirmar_canal

                confirmation_message = await ctx.author.send(embed=embed)
                await confirmation_message.add_reaction('✅')  # Reação para "sim"
                await confirmation_message.add_reaction('❌')  # Reação para "não"

                def check_reaction(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

                response_reaction, _ = await client.wait_for(const.reaction_add, timeout=120, check=check_reaction)

                if str(response_reaction.emoji) == '✅':
                    break
                embed.description = const.msg_informe_novamente_o_nome_do_canal
                await ctx.author.send(embed=embed)

        embed = discord.Embed(

            title=const.criar_canal,
            description=const.msg_informe_qnt_vagas,
            color=discord.Color.brand_green()
        )
        await ctx.author.send(embed=embed)

        while True:
            while True:
                response_number_vacancies = await client.wait_for(const.message,
                                                                  check=lambda m: m.author == ctx.author and isinstance(
                                                                      m.channel, discord.DMChannel), timeout=120)
                if response_number_vacancies.content.isnumeric() and int(response_number_vacancies.content) <= 99:
                    break
                await ctx.author.send(const.msg_vagas_ate_99)

            embed.description = const.msg_confirma_quantidade_vagas
            confirmation_message = await ctx.author.send(embed=embed)
            await confirmation_message.add_reaction('✅')  # Reação para "sim"
            await confirmation_message.add_reaction('❌')  # Reação para "não"

            def check_reaction(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

            response_reaction, _ = await client.wait_for(const.reaction_add, timeout=120, check=check_reaction)

            if str(response_reaction.emoji) == '✅':
                break
            embed.description = const.msg_qnt_vagas_novamente
            await ctx.author.send(embed=embed)

        number_vacancies = int(response_number_vacancies.content)
        pretendente_role = discord.utils.get(ctx.guild.roles, name=const.pretendente)

        overwrites = {

            ctx.author: discord.PermissionOverwrite(connect=True, mute_members=True, deafen_members=True,
                                                    view_channel=True),
            pretendente_role: discord.PermissionOverwrite(connect=False, view_channel=False),

        }

        id_category_privados = 1122732787393384478
        category = discord.utils.get(ctx.guild.categories, id=id_category_privados)
        channel = await ctx.guild.create_voice_channel(channel_name, category=category, overwrites=overwrites)

        await channel.set_permissions(ctx.author, connect=True, mute_members=True, deafen_members=True)
        await channel.edit(user_limit=number_vacancies)

        embed = discord.Embed(

            title=const.canal_criado_com_sucesso,
            description=const.volte_ao_servidor,
            color=discord.Color.brand_green()
        )

        await ctx.author.send(embed=embed)

        await asyncio.sleep(12 * 60 * 60)
        await channel.delete()

    except asyncio.TimeoutError:

        embed = discord.Embed(
            title=const.tempo_excedido,
            description=const.tempo_esgotado,
            color=discord.Color.brand_green()
        )


@client.command(description=const.mostrar_comandos)
async def ajuda(ctx):
    bot_commands = client.commands
    embed = discord.Embed(

        title=const.lista_comandos,
        description=const.comandos_disponiveis,
        color=discord.Color.brand_green()
    )

    for command in bot_commands:
        if command.name != const.help:
            embed.add_field(name=f"!{command.name}", value=command.description, inline=False)
    await ctx.send(embed=embed)


client.run(TOKEN)
