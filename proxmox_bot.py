#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# https://geekytheory.com/telegram-programando-un-bot-en-python/
# https://bitbucket.org/master_groosha/telegram-proxy-bot/src/07a6b57372603acae7bdb78f771be132d063b899/proxy_bot.py?at=master&fileviewer=file-view-default
# https://github.com/eternnoir/pyTelegramBotAPI/blob/master/telebot/types.py

"""commands
wakeonlan - Start the server
reboot - Restart the server
poweroff - Turn off the server
halt - Turn off the server
exit - Exit
help - Show help
start - Start the bot
"""

import configparser
import re
import subprocess
from typing import NoReturn, Optional, Tuple

from telebot import TeleBot, types  # Importamos la librería Y los tipos especiales de esta

from Pentesting import client_ssh

FILE_CONFIG = 'settings.ini'
config = configparser.ConfigParser()
config.read(FILE_CONFIG)

config_basic = config["BASICS"]
config_ssh = config["SSH"]

administrador = 33063767
users_permitted = [33063767, 40522670]

bot = TeleBot(config_basic.get('BOT_TOKEN'))
bot.send_message(administrador, "El bot se ha iniciado")

dicc_botones = {
    'wakeonlan': '/wakeonlan',
    'reboot': '/reboot',
    'poweroff': '/poweroff',
    'halt': '/halt',
    'exit': '/exit',
}


def check_error(codigo, stderr) -> bool:
    if codigo.returncode and stderr:
        print(f"Error: {codigo}, {stderr}")
        return True
    return False


def format_text(param_text: bytes) -> Optional[str]:
    if param_text is not None:
        text = param_text.decode('utf-8')
        return str(text)
        # return text.replace('\n', '')
    return param_text


def execute_command(command: str) -> Tuple[str, str, subprocess.Popen]:
    execute = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = execute.communicate()
    return format_text(stdout), format_text(stderr), execute


# Handle always first "/start" message when new chat with your bot is created
@bot.message_handler(commands=["start"])
def command_start(message) -> NoReturn:
    bot.send_message(message.chat.id, f"Bienvenido al bot\nTu id es: {message.chat.id}")
    command_system(message)
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(commands=["help"])
def command_help(message) -> NoReturn:
    bot.send_message(message.chat.id, "Aqui pondre todas las opciones")
    markup = types.InlineKeyboardMarkup()
    itembtna = types.InlineKeyboardButton('Github', url="https://github.com/procamora/bot_proxmox")
    markup.row(itembtna)
    bot.send_message(message.chat.id, "Aqui pondre todas las opciones", reply_markup=markup)
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(func=lambda message: message.chat.id == administrador, content_types=["text"])
def my_text(message) -> NoReturn:
    if message.text in dicc_botones.values():
        if message.text == dicc_botones['wakeonlan']:
            send_wakeonlan(message)
        elif message.text == dicc_botones['reboot']:
            send_reboot(message)
        elif message.text == dicc_botones['poweroff']:
            send_poweroff(message)
        elif message.text == dicc_botones['halt']:
            send_halt(message)
        elif message.text == dicc_botones['exit']:
            send_exit(message)
    else:
        bot.send_message(message.chat.id, "Comando desconocido")
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(commands=["system"])
def command_system(message) -> NoReturn:
    bot.send_message(message.chat.id, "Lista de comandos disponibles")

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row(dicc_botones['wakeonlan'], dicc_botones['reboot'])
    markup.row(dicc_botones['poweroff'], dicc_botones['halt'])
    markup.row(dicc_botones['exit'])

    bot.send_message(message.chat.id, "Escoge una opcion: ", reply_markup=markup)
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['exit'])
def send_exit(message) -> NoReturn:
    pass


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['wakeonlan'])
def send_wakeonlan(message) -> NoReturn:
    command = f'wakeonlan {config_basic.get("MAC_PROXMOX")}'
    stdout, stderr, execute = execute_command(command)

    if check_error(execute, stderr):
        bot.reply_to(message, f'Error: {stderr}')
        return
    elif len(stdout) == 0:
        bot.reply_to(message, 'Ejecutado, no hace nada')
    else:
        bot.reply_to(message, stdout)


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['reboot'])
def send_reboot(message) -> NoReturn:
    cmd: str = 'reboot'
    ssh: client_ssh.ClientSSH = client_ssh.ClientSSH(config_ssh.get('IP'), config_ssh.get('USER'),
                                                     config_ssh.get('PASSWORD'), cmd, port=config_ssh.get('PORT'))
    if not ssh.is_online():
        bot.reply_to(message, f'Client: {config_ssh.get("IP")} is down!')
        return

    output, error = ssh.execute_command()
    if error != 0:
        bot.reply_to(message, f'Error: {output}')
    else:
        bot.reply_to(message, f'OK: {output}')
    return


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['poweroff'])
def send_poweroff(message) -> NoReturn:
    cmd: str = 'poweroff'
    ssh: client_ssh.ClientSSH = client_ssh.ClientSSH(config_ssh.get('IP'), config_ssh.get('USER'),
                                                     config_ssh.get('PASSWORD'), cmd, port=config_ssh.get('PORT'))
    if not ssh.is_online():
        bot.reply_to(message, f'Client: {config_ssh.get("IP")} is down!')
        return

    output, error = ssh.execute_command()
    if error != 0:
        bot.reply_to(message, f'Error: {output}')
    else:
        bot.reply_to(message, f'OK: {output}')
    return


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['halt'])
def send_halt(message) -> NoReturn:
    cmd: str = 'halt'
    ssh: client_ssh.ClientSSH = client_ssh.ClientSSH(config_ssh.get('IP'), config_ssh.get('USER'),
                                                     config_ssh.get('PASSWORD'), cmd, port=config_ssh.get('PORT'))
    if not ssh.is_online():
        bot.reply_to(message, f'Client: {config_ssh.get("IP")} is down!')
        return

    output, error = ssh.execute_command()
    if error != 0:
        bot.reply_to(message, f'Error: {output}')
    else:
        bot.reply_to(message, f'OK: {output}')
    return


@bot.message_handler(func=lambda message: message.chat.id == administrador, regexp="[Cc]md: .*")
def handle_cmd(message) -> NoReturn:
    command_dangerous = ['sudo reboot', ':(){ :|: & };:', 'sudo rm -rf /']

    command = re.sub('[Cc]md: ', '', message.text, re.IGNORECASE)
    if command not in command_dangerous:
        stdout, stderr, execute = execute_command(command)

        if check_error(execute, stderr):
            bot.reply_to(message, f'Error: {stderr}')
            return
        elif len(stdout) == 0:
            bot.reply_to(message, f'Ejecutado: {command}')
        else:
            bot.reply_to(message, stdout)
    else:
        bot.reply_to(message, 'Comando aun no implementado')


@bot.message_handler(func=lambda message: message.chat.id == administrador, content_types=["photo"])
def my_photo(message) -> NoReturn:
    if message.reply_to_message:
        bot.send_photo(message.chat.id, list(message.photo)[-1].file_id)
    else:
        bot.send_message(message.chat.id, "No one to reply photo!")
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(func=lambda message: message.chat.id == administrador, content_types=["voice"])
def my_voice(message) -> NoReturn:
    if message.reply_to_message:
        bot.send_voice(message.chat.id, message.voice.file_id, duration=message.voice.duration)
    else:
        bot.send_message(message.chat.id, "No one to reply voice!")
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(func=lambda message: message.chat.id in users_permitted, content_types=["document"])
def my_document(message) -> NoReturn:
    # if message.reply_to_message:
    #    bot.send_voice(message.chat.id, message.voice.file_id, duration=message.voice.duration)
    # else:
    bot.reply_to(message, f'Aun no he implementado este tipo de ficheros: "{message.document.mime_type}"')
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(regexp=".*")
def handle_resto(message) -> NoReturn:
    texto = 'No tienes permiso para ejecutar esta accion, eso se debe a que no eres yo.\n' \
            'Por lo que ya sabes, desaparece -.-'
    bot.reply_to(message, texto)
    return  # solo esta puesto para que no falle la inspeccion de codigo


# Con esto, le decimos al bot que siga funcionando incluso si encuentra
# algun fallo.
bot.polling(none_stop=False)
