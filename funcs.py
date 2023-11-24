import csv
import smtplib
import random
import email.message
from config.bot_password import bot_password, bot_email
from config import const


def teacher_datamanagement(datamail):
    with open(const.planilha_professores, mode='r') as arquivo_csv:
        leitor_csv = csv.reader(arquivo_csv)
        for linha in leitor_csv:
            if linha[1].lower() == datamail:
                name = linha[0]
                return (True, name)
    return (False, '')


def student_datamanagement(datamail):
    with open(const.planilha_alunos, mode='r') as arquivo_csv:
        leitor_csv = csv.reader(arquivo_csv)
        for linha in leitor_csv:
            if linha[7].lower() == datamail:
                name = linha[1]
                return (True, name)
    return (False, '')


def generate_verification_code():
    return str(random.randint(100000, 999999))


def send_verification_email(recipient_email):

    code = generate_verification_code()
    corpo_email = code

    bot_email_received = bot_email
    bot_password_received = bot_password

    msg = email.message.Message()
    msg['Subject'] = const.subject_codigo_de_verificacao
    msg['From'] = bot_email_received
    msg['To'] = recipient_email
    password = bot_password_received
    # Corpo da email
    msg.set_payload(f'Olá!\nSeu código de verificação para entrar no servidor é: {corpo_email}')

    s = smtplib.SMTP(const.smtp_porta)
    s.starttls()

    s.login(msg['From'], password)
    s.sendmail(msg['From'], [msg['To']], msg.as_string().encode(const.utf8))
    return code

