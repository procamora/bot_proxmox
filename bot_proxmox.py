#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# https://geekytheory.com/telegram-programando-un-bot-en-python/
# https://bitbucket.org/master_groosha/telegram-proxy-bot/src/07a6b57372603acae7bdb78f771be132d063b899/proxy_bot.py?at=master&fileviewer=file-view-default
# https://github.com/eternnoir/pyTelegramBotAPI/blob/master/telebot/types.py

"""commands
wakeonlan - Start the server
reboot - Restart the server
poweroff - Turn off the server
shutdown - Turn off the server
exit - Exit
help - Show help
start - Start the bot
"""

import configparser
import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn, Optional, Tuple, Dict, List

from telebot import TeleBot, types  # Importamos la librería Y los tipos especiales de esta
from procamora_utils.logger import get_logging, logging
from procamora_utils.client_ssh import ClientSSH

logger: logging = get_logging(False, 'bot_proxmox')

FILE_CONFIG: Path = Path('settings.cfg')
if not FILE_CONFIG.exists():
    logger.critical(f'File {FILE_CONFIG} not exists and is necesary')
    sys.exit(1)

config: configparser.ConfigParser = configparser.ConfigParser()
config.read(FILE_CONFIG)

config_basic: configparser.SectionProxy = config["BASICS"]
config_ssh: configparser.SectionProxy = config["SSH"]
administrador: int = 33063767
users_permitted: List = [33063767, 40522670]

cert_str: str = config_ssh.get('CERT')
if cert_str is not None:
    cert = Path(cert_str)
else:
    cert = None

if not cert.exists():
    logger.critical(f'certificate {cert_str} not exists')
    sys.exit(1)

bot: TeleBot = TeleBot(config_basic.get('BOT_TOKEN'))
bot.send_message(administrador, "El bot se ha iniciado")
logger.info('Starting bot')

dicc_botones: Dict = {
    'wakeonlan': '/wakeonlan',
    'reboot': '/reboot',
    'poweroff': '/poweroff',
    'shutdown': '/shutdown',
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


def get_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row(dicc_botones['wakeonlan'], dicc_botones['reboot'])
    markup.row(dicc_botones['poweroff'], dicc_botones['shutdown'])
    markup.row(dicc_botones['exit'])
    return markup


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


@bot.message_handler(commands=["system"])
def command_system(message) -> NoReturn:
    bot.send_message(message.chat.id, "Lista de comandos disponibles")

    bot.send_message(message.chat.id, "Escoge una opcion: ", reply_markup=get_keyboard())
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['exit'])
def send_exit(message) -> NoReturn:
    pass


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['/wakeonlan'])
def send_wakeonlan(message) -> NoReturn:
    command = f'wakeonlan {config_basic.get("MAC_PROXMOX")}'
    stdout, stderr, execute = execute_command(command)

    if check_error(execute, stderr):
        bot.reply_to(message, f'Error: {stderr}')
        return
    elif len(stdout) == 0:
        bot.reply_to(message, 'Ejecutado, no hace nada', reply_markup=get_keyboard())
    else:
        bot.reply_to(message, stdout, reply_markup=get_keyboard())


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['reboot'])
def send_reboot(message) -> NoReturn:
    cmd: str = 'reboot'
    ssh: ClientSSH = ClientSSH(ip=config_ssh.get('IP'), port=int(config_ssh.get('PORT')), debug=False)
    if not ssh.is_online():
        bot.reply_to(message, f'Client: {config_ssh.get("IP")} is down!')
        return

    output, error = ssh.execute_command(user=config_ssh.get('USER'), password=config_ssh.get('PASSWORD'), cert=cert,
                                        command=cmd)
    if error != 0:
        bot.reply_to(message, f'Error: {output}', reply_markup=get_keyboard())
    else:
        bot.reply_to(message, f'rebooting in process', reply_markup=get_keyboard())
    return


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['poweroff'])
def send_poweroff(message) -> NoReturn:
    cmd: str = 'poweroff'
    ssh: ClientSSH = ClientSSH(ip=config_ssh.get('IP'), port=int(config_ssh.get('PORT')), debug=False)

    if not ssh.is_online():
        bot.reply_to(message, f'Client: {config_ssh.get("IP")} is down!')
        return

    output, error = ssh.execute_command(user=config_ssh.get('USER'), password=config_ssh.get('PASSWORD'), cert=cert,
                                        command=cmd)
    if error != 0:
        bot.reply_to(message, f'Error: {output}', reply_markup=get_keyboard())
    else:
        bot.reply_to(message, f'OK: {output}', reply_markup=get_keyboard())
    return


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['shutdown'])
def send_shutdown(message) -> NoReturn:
    cmd: str = 'shutdown -h now'
    ssh: ClientSSH = ClientSSH(ip=config_ssh.get('IP'), port=int(config_ssh.get('PORT')), debug=False)

    if not ssh.is_online():
        bot.reply_to(message, f'Client: {config_ssh.get("IP")} is down!')
        return

    output, error = ssh.execute_command(user=config_ssh.get('USER'), password=config_ssh.get('PASSWORD'), cert=cert,
                                        command=cmd)
    if error != 0:
        bot.reply_to(message, f'Error: {output}', reply_markup=get_keyboard())
    else:
        bot.reply_to(message, f'OK: {output}', reply_markup=get_keyboard())
    return


@bot.message_handler(func=lambda message: message.chat.id == administrador, regexp="[Cc]md: .*")
def handle_cmd(message) -> NoReturn:
    command_dangerous = ['sudo reboot', ':(){ :|: & };:', 'sudo rm -rf /']

    command = re.sub('[Cc]md: ', '', message.text, re.IGNORECASE)
    if command not in command_dangerous:
        stdout, stderr, execute = execute_command(command)

        if check_error(execute, stderr):
            bot.reply_to(message, f'Error: {stderr}', reply_markup=get_keyboard())
            return
        elif len(stdout) == 0:
            bot.reply_to(message, f'Ejecutado: {command}', reply_markup=get_keyboard())
        else:
            bot.reply_to(message, stdout, reply_markup=get_keyboard())
    else:
        bot.reply_to(message, 'Comando aun no implementado', reply_markup=get_keyboard())


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


@bot.message_handler(func=lambda message: message.chat.id == administrador, content_types=["text"])
def my_text(message) -> NoReturn:
    if message.text in dicc_botones.values():
        pass
    else:
        bot.send_message(message.chat.id, "Comando desconocido", reply_markup=get_keyboard())
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
