#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
import json
import base64
import os
from datetime import datetime

#######################################################################################################################
# Импорт параметров из файла settings.json ############################################################################
#######################################################################################################################
json_file = open("C:/connector2/settings.json", 'r', encoding='utf-8-sig')
data = json.load(json_file)
log_level = data['general_settings']['log_level']
log_path = data['general_settings']['log_path']
sync_timeout = data['general_settings']['sync_timeout']
error_timeout = data['general_settings']['error_timeout']
max_tries = data['general_settings']['max_tries']
delta_timezone = data['general_settings']['timezone']
suib_conn_type = data['suib_settings']['ssl']
suib_server_name = data['suib_settings']['server_name']
suib_server_port = data['suib_settings']['server_port']
suib_conn_timeout = data['suib_settings']['connection_timeout']
gossopka_conn_type = data['gossopka_settings']['ssl']
gossopka_server_name = data['gossopka_settings']['server_name']
gossopka_server_port = data['gossopka_settings']['server_port']
gossopka_organization = data['gossopka_settings']['organization']
account_name = data['suib_settings']['account_name']
account_password = data['suib_settings']['account_password']
encrypt = data['suib_settings']['encrypt']
prefix = data['suib_settings']['incident_id_prefix']
token = data['gossopka_settings']['server_token']
json_file.close()
# Статичные переменные #################################################################################################
# Протокол http/https
if suib_conn_type:
    suib_ssl = "https"
else:
    suib_ssl = "http"
if gossopka_conn_type:
    gossopka_ssl = "https"
else:
    gossopka_ssl = "http"
#
# Шифрование логина и пароля, если параметр в encrypt=True (файл settings.json) #######################################
if encrypt:
    account_name_log = account_name
    account_name_encode = account_name.encode('ascii')
    account_name_base64 = base64.b64encode(account_name_encode)
    account_name_decode = account_name_base64.decode('ascii')
    account_password_add = ":" + account_password
    account_password_encode = account_password_add.encode('ascii')
    account_password_base64 = base64.b64encode(account_password_encode)
    account_password_decode = account_password_base64.decode('ascii')
    data['suib_settings']['account_name'] = account_name_decode
    data['suib_settings']['account_password'] = account_password_decode
    data['suib_settings']['encrypt'] = False
    json_file = open("settings.json", 'w', encoding='utf-8-sig')
    json.dump(data, json_file, indent=2, ensure_ascii=False)
    json_file.close()
    base64_auth_header = account_name_decode + account_password_decode
else:
    base64_auth_header = account_name + account_password
    account_name_log = base64.b64decode(account_name)
    account_name_log = account_name_log.decode('ascii')


# Проверка наличия папки с журналами ##################################################################################
def check_folder(log_path):
    folder_name = datetime.today().strftime('%Y%m')
    folder_path = log_path + '/' + folder_name
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_name = str(datetime.today().strftime('%Y%m%d')) + '.log'
    file_path = os.path.join(folder_path, file_name)
    file = open(file_path, "a")
    file.close()
    return file_path
