#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
import requests
import json
import time
import xmltodict
from datetime import datetime
from notifications import level_debug, level_info, level_warn, level_error, level_fatal, \
    log_suib_test_connect_critical, log_suib_session_limit_user, log_suib_session_limit_server, \
    log_suib_notifications_success
from notifications import log_module_start, log_module_end, log_sync_start, log_sync_end, log_gossopka_test_connect, \
    log_suib_test_connect, log_notifications_add, \
    log_suib_test_connect_error, \
    log_gossopka_test_connect_error, log_gossopka_test_connect_unavailable, log_suib_test_connect_unavailable, \
    log_gossopka_test_connect_success, log_gossopka_test_connect_credentials_error, log_suib_test_connect_success, \
    log_suib_get_notifications, log_suib_null_notifications, log_suib_get_notifications_error
from notifications import connector_logger
from main import delta_timezone
from main import log_path, log_level, max_tries, error_timeout, sync_timeout
from main import gossopka_ssl, gossopka_server_name, gossopka_server_port, gossopka_organization, token, prefix
from main import suib_ssl, suib_server_name, suib_server_port, suib_conn_timeout
from main import check_folder, base64_auth_header, account_name_log


def run_connector():
    file_path = check_folder(log_path=log_path)  # Проверка созданния папки для хранения журналов
    if log_level == 'DEBUG' or log_level == 'INFO':
        connector_logger(file_path=file_path, level=level_info, message_text=log_module_start)
    attempts = 0
    while attempts < max_tries:
        if log_level == 'DEBUG' or log_level == 'INFO':
            connector_logger(file_path=file_path, level=level_info, message_text=log_sync_start)
        else:
            pass
        test_conn_to_gossopka_result = test_conn_to_gossopka()
        if test_conn_to_gossopka_result == "Проверка соединения с ГосСОПКА завершилась успешно":
            print("Проверка соединения с ГосСОПКА завершилась успешно")
            test_conn_to_suib_result = test_conn_to_suib()
            if test_conn_to_suib_result == "Проверка соединения с СУИБ прошла успешно":
                print("Проверка соединения с СУИБ прошла успешно")
                get_notifications_from_suib_result = get_notifications_from_suib()
                if get_notifications_from_suib_result == "В СУИБ не найдено уведомлений для передачи в ГосСОПКА":
                    time.sleep(sync_timeout)
                elif get_notifications_from_suib_result == "Проверка соединения с СУИБ завершилась ошибкой":
                    time.sleep(error_timeout)
                else:
                    print(get_notifications_from_suib_result)
                    time.sleep(sync_timeout)
            elif test_conn_to_suib_result == "Проверка соединения с СУИБ завершилась ошибкой":
                print("Проверка соединения с СУИБ завершилась ошибкой")
                if log_level == 'DEBUG' or log_level == 'INFO':
                    connector_logger(file_path=file_path, level=level_info, message_text=log_module_end)
                return test_conn_to_suib_result
        elif test_conn_to_gossopka_result == "Проверка соединения с ГосСОПКА завершилась ошибкой":
            print("Проверка соединения с ГосСОПКА завершилась ошибкой")
            if log_level == 'DEBUG' or log_level == 'INFO':
                connector_logger(file_path=file_path, level=level_info, message_text=log_module_end)
            return test_conn_to_gossopka_result


# 5.1 Проверка возможности подключения к ГосСОПКА (+ 4.1 Обработка ошибок ГосСОПКА)
def test_conn_to_gossopka():  # Проверка возможности подключения к ГосСОПКА
    file_path = check_folder(log_path=log_path)  # Проверка созданния папки для хранения журналов
    if "DEBUG" in log_level:
        connector_logger(file_path=file_path, level=level_debug, message_text=log_gossopka_test_connect)
    test_conn_gossopka_date = str(datetime.today().strftime('%Y-%m-%d'))
    test_conn_gossopka_url = gossopka_ssl + "://" + gossopka_server_name + ":" + str(
        gossopka_server_port) + "/api/v2/incidents?filter=%5B%7B%22property%22%3A%22category%22%2C%22operator%22%3A%22in%22%2C%22value%22%3A%5B%22%D0%A3%D0%B2%D0%B5%D0%B4%D0%BE%D0%BC%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%BE%20%D0%BA%D0%BE%D0%BC%D0%BF%D1%8C%D1%8E%D1%82%D0%B5%D1%80%D0%BD%D0%BE%D0%BC%20%D0%B8%D0%BD%D1%86%D0%B8%D0%B4%D0%B5%D0%BD%D1%82%D0%B5%22%2C%20%22%D0%A3%D0%B2%D0%B5%D0%B4%D0%BE%D0%BC%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%BE%20%D0%BA%D0%BE%D0%BC%D0%BF%D1%8C%D1%8E%D1%82%D0%B5%D1%80%D0%BD%D0%BE%D0%B9%20%D0%B0%D1%82%D0%B0%D0%BA%D0%B5%22%2C%20%22%D0%A3%D0%B2%D0%B5%D0%B4%D0%BE%D0%BC%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%BE%20%D0%BD%D0%B0%D0%BB%D0%B8%D1%87%D0%B8%D0%B8%20%D1%83%D1%8F%D0%B7%D0%B2%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D0%B8%22%5D%7D%2C%7B%22property%22%3A%22createtime%22%2C%22operator%22%3A%22%3E%3D%22%2C%22value%22%3A%222" + test_conn_gossopka_date + "T22%3A37%3A54%22%7D%5D&fields=regnumber&fields=createtime&offset=15&limit=50"
    test_conn_gossopka_payload = ""
    test_conn_gossopka_headers = {
        'accept': 'application/json',
        'x-token': token,
    }
    success_connection = 0
    while success_connection < 1:  # - пока не будет выполнено подключение к ГосСОПКА
        try:
            test_conn_gossopka_response = requests.request("GET", test_conn_gossopka_url,
                                                           headers=test_conn_gossopka_headers,
                                                           data=test_conn_gossopka_payload, verify=False)
            test_conn_gossopka_response_error = str(test_conn_gossopka_response.text).split(",")[1].split(":")[
                1].replace('"', "")
            if "DEBUG" in log_level:
                connector_logger(file_path=file_path, level=level_debug, message_text=(
                        "Запрос в ГосСОПКА:" + " " + "GET" + " " + str(test_conn_gossopka_url) + " " + str(
                    test_conn_gossopka_headers).replace(token, "***************************") + "\r\n"))
                connector_logger(file_path=file_path, level=level_debug,
                                 message_text=("Ответ от ГосСОПКА: " + str(test_conn_gossopka_response.text) + "\r\n"))
            else:
                pass
            if "200" in str(test_conn_gossopka_response.status_code):
                if log_level == 'DEBUG' or log_level == 'INFO':
                    connector_logger(file_path=file_path, level=level_info,
                                     message_text=log_gossopka_test_connect_success)
                    success_connection += 1
                    test_conn_gossopka_success = "Проверка соединения с ГосСОПКА завершилась успешно"
            else:  # ОШИБКА п 4.1
                if log_level == 'DEBUG' or log_level == 'INFO' or log_level == 'WARN':
                    connector_logger(file_path=file_path, level=level_warn,
                                     message_text=log_gossopka_test_connect_error)
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            "Запрос в ГосСОПКА:" + " " + "GET" + " " + str(test_conn_gossopka_url) + " " + str(
                        test_conn_gossopka_headers).replace(token, "***************************") + "\r\n"))
                    connector_logger(file_path=file_path, level=level_warn,
                                     message_text=("Ответ от ГосСОПКА: " + str(
                                         test_conn_gossopka_response.text) + "\r\n"))
                else:
                    pass
                if str(test_conn_gossopka_response.status_code) == '400' or str(
                        test_conn_gossopka_response.status_code) == '401':
                    print("Указаны неверные учетные данные для авторизации в ГосСОПКА")
                    connector_logger(file_path=file_path, level=level_fatal,
                                     message_text=log_gossopka_test_connect_credentials_error)
                    raise ValueError('FATAL')
                elif str(test_conn_gossopka_response.status_code) == '403' or str(
                        test_conn_gossopka_response.status_code) == '404' or str(
                    test_conn_gossopka_response.status_code) == '500':
                    if log_level == 'DEBUG' or log_level == 'INFO' or log_level == 'WARN':
                        connector_logger(file_path=file_path, level=level_warn, message_text=(
                                "Получен статус " + str(
                            test_conn_gossopka_response.status_code) + " при выполнении запроса в ГосСОПКА. Текст ошибки: " + str(
                            test_conn_gossopka_response_error) + "\r\n"))
                    time.sleep(error_timeout)
                else:
                    connector_logger(file_path=file_path, level=level_fatal, message_text=(
                            "Возникла критическая ошибка при выполнении запроса в ГосСОПКА. Текст ошибки: " + str(
                        test_conn_gossopka_response_error) + "\r\n"))
                    raise ValueError('FATAL')
        except requests.exceptions.RequestException as net_error:
            print("ГосСОПКА недоступна: ", net_error)
            if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
                connector_logger(file_path=file_path, level=level_warn,
                                 message_text=log_gossopka_test_connect_unavailable)
            time.sleep(error_timeout)
        except ValueError:
            success_connection += 1
            test_conn_gossopka_success = "Проверка соединения с ГосСОПКА завершилась ошибкой"

            time.sleep(error_timeout)
    return str(test_conn_gossopka_success)


# 5.2 Проверка возможности подключения к СУИБ (+ 4.2 Обработка ошибок СУИБ)
def test_conn_to_suib():
    file_path = check_folder(log_path=log_path)  # Проверка созданния папки для хранения журналов
    if "DEBUG" in log_level:
        connector_logger(file_path=file_path, level=level_debug, message_text=log_suib_test_connect)
    suib_url = suib_ssl + "://" + suib_server_name + ":" + str(suib_server_port) + "/SM/7/ws"
    test_conn_suib_payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://schemas.hp.com/SM/7\">\r\n   <soapenv:Header/>\r\n   <soapenv:Body>\r\n      <ns:RetrieveIncidentNotifyListRequest>\r\n         <ns:keys query=\"false\">\r\n            <ns:Id type=\"String\"/>\r\n         </ns:keys>\r\n      </ns:RetrieveIncidentNotifyListRequest>\r\n   </soapenv:Body>\r\n</soapenv:Envelope>"
    suib_headers = {
        'SOAPAction': '"RetrieveList"',
        'Connection': 'Close',
        'Content-Type': 'text/xml;charset=UTF-8',
        'Authorization': 'Basic ' + base64_auth_header
    }
    success_connection = 0  # Счетчик ошибок
    while success_connection < 1:  # - пока не будет выполнено подключение к СУИБ
        try:
            # Выполняем подключение к СУИБ
            test_conn_suib_response = requests.request("POST", suib_url, headers=suib_headers,
                                                       data=test_conn_suib_payload, timeout=suib_conn_timeout)
            if "DEBUG" in log_level:
                connector_logger(file_path=file_path, level=level_debug,
                                 message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                     suib_headers).replace(base64_auth_header, "********************") + " " + str(
                                     test_conn_suib_payload.replace("\r\n", "")) + "\r\n"))
                connector_logger(file_path=file_path, level=level_debug,
                                 message_text=("Ответ от СУИБ: " + str(test_conn_suib_response.text) + "\r\n"))
            else:
                pass
            if str(test_conn_suib_response.status_code) == '200':
                parsed_text = xmltodict.parse(test_conn_suib_response.text, encoding='utf-8', namespace_separator=":")
                test_conn_suib_response_code = \
                    parsed_text['SOAP-ENV:Envelope']['SOAP-ENV:Body']['RetrieveIncidentNotifyListResponse'][
                        '@returnCode']
                test_conn_suib_response_status = \
                    parsed_text['SOAP-ENV:Envelope']['SOAP-ENV:Body']['RetrieveIncidentNotifyListResponse']['@status']
                if test_conn_suib_response_code == '0':
                    if "FAILURE" in test_conn_suib_response_status:
                        connector_logger(file_path=file_path, level=level_fatal,
                                         message_text=log_suib_test_connect_error)
                        connector_logger(file_path=file_path, level=level_fatal,
                                         message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                             suib_headers).replace(base64_auth_header,
                                                                   "********************") + " " + str(
                                             test_conn_suib_payload.replace("\r\n", "")) + "\r\n"))
                        connector_logger(file_path=file_path, level=level_fatal,
                                         message_text=("Ответ от СУИБ: " + str(test_conn_suib_response.text) + "\r\n"))
                        raise ValueError('FATAL')
                    else:
                        if log_level == 'DEBUG' or log_level == 'INFO':
                            connector_logger(file_path=file_path, level=level_info,
                                             message_text=log_suib_test_connect_success)
                        success_connection += 1
                        test_conn_suib_success = "Проверка соединения с СУИБ прошла успешно"
                elif test_conn_suib_response_code == '9':
                    if log_level == 'DEBUG' or log_level == 'INFO':
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text=log_suib_test_connect_success)
                    success_connection += 1
                    test_conn_suib_success = "Проверка соединения с СУИБ прошла успешно"
                else:
                    if log_level == 'DEBUG' or log_level == 'INFO' or log_level == 'WARN':
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=log_suib_test_connect_error)
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                             suib_headers).replace(base64_auth_header,
                                                                   "********************") + " " + str(
                                             test_conn_suib_payload.replace("\r\n", "")) + "\r\n"))
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=("Ответ от СУИБ: " + str(test_conn_suib_response.text) + "\r\n"))
            elif str(test_conn_suib_response.status_code) == '401':
                if str(test_conn_suib_response.text) == '<HTML><BODY>Not Authorized</BODY></HTML>':
                    if log_level == 'INFO' or log_level == 'WARN' or log_level == 'DEBUG':
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=log_suib_test_connect_error)
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                             suib_headers).replace(base64_auth_header,
                                                                   "********************") + " " + str(
                                             test_conn_suib_payload.replace("\r\n", "")) + "\r\n"))
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=("Ответ от СУИБ: " + str(test_conn_suib_response.text) + "\r\n"))
                    connector_logger(file_path=file_path, level=level_fatal, message_text=(
                            "Ответ от СУИБ: " + "Указаны неверные учетные данные для авторизации в СУИБ, либо пользователь" + " " + str(
                        account_name_log) + " " + "не имеет прав для совершения выполняемого действия\r\n"))
                    raise ValueError('FATAL')
                else:
                    success_user_limit = 0
                    while success_user_limit < 1:
                        test_conn_suib_response = requests.request("POST", suib_url, headers=suib_headers,
                                                                   data=test_conn_suib_payload, timeout=suib_conn_timeout)
                        if str(test_conn_suib_response.text) == '<HTML><BODY>6:Login failed. Maximum active logins for this user exceeded</BODY></HTML>':
                            if log_level == 'INFO' or log_level == 'WARN' or log_level == 'DEBUG':
                                connector_logger(file_path=file_path, level=level_warn,
                                                 message_text=log_suib_test_connect_error)
                                connector_logger(file_path=file_path, level=level_warn, message_text=(
                                            "Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                        suib_headers).replace(base64_auth_header, "********************") + " " + str(
                                        test_conn_suib_payload.replace("\r\n", "")) + "\r\n"))
                                connector_logger(file_path=file_path, level=level_warn, message_text=(
                                            "Ответ от СУИБ: " + str(test_conn_suib_response.text) + "\r\n"))
                                connector_logger(file_path=file_path, level=level_warn,
                                                 message_text=log_suib_session_limit_user)
                                time.sleep(error_timeout)
                        else:
                            success_user_limit += 1
            elif str(test_conn_suib_response.status_code) == '500':
                success_server_limit = 0
                while success_server_limit < 1:
                    test_conn_suib_response = requests.request("POST", suib_url, headers=suib_headers,
                                                               data=test_conn_suib_payload, timeout=suib_conn_timeout)
                    if str(test_conn_suib_response.status_code) == '500':
                        if log_level == 'INFO' or log_level == 'WARN' or log_level == 'DEBUG':
                            connector_logger(file_path=file_path, level=level_warn,
                                             message_text=log_suib_test_connect_error)
                            connector_logger(file_path=file_path, level=level_warn,
                                             message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                                 suib_headers).replace(base64_auth_header,
                                                                       "********************") + " " + str(
                                                 test_conn_suib_payload.replace("\r\n", "")) + "\r\n"))
                            connector_logger(file_path=file_path, level=level_warn,
                                             message_text=("Ответ от СУИБ: " + str(test_conn_suib_response.text) + "\r\n"))
                            connector_logger(file_path=file_path, level=level_warn,
                                             message_text=log_suib_session_limit_server)
                            time.sleep(error_timeout)
                    else:
                        success_server_limit += 1
            else:
                connector_logger(file_path=file_path, level=level_fatal, message_text=log_suib_test_connect_critical)
                raise ValueError('FATAL')
        except requests.exceptions.RequestException as net_error:
            print("СУИБ недоступен: ", net_error)
            if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
                connector_logger(file_path=file_path, level=level_warn,
                                 message_text=log_suib_test_connect_unavailable)
            time.sleep(error_timeout)
        except ValueError:
            success_connection += 1
            time.sleep(error_timeout)
            test_conn_suib_success = "Проверка соединения с СУИБ завершилась ошибкой"
    return test_conn_suib_success


# 6.1 Получение новых уведомлений из СУИБ для добавления в ГосСОПКА
def get_notifications_from_suib():
    file_path = check_folder(log_path=log_path)
    if log_level == "DEBUG" or log_level == "INFO":
        connector_logger(file_path=file_path, level=level_info,
                         message_text=log_notifications_add)
    success_connection = 0  # Счетчик ошибок
    while success_connection < 1:  # - пока не будет выполнено подключение к СУИБ
        print("Получение новых уведомлений из СУИБ для добавления в ГосСОПКА")
        file_path = check_folder(log_path=log_path)  # Проверка созданния папки для хранения журналов
        if "DEBUG" in log_level:
            connector_logger(file_path=file_path, level=level_debug, message_text=log_suib_get_notifications)
        suib_url = suib_ssl + "://" + suib_server_name + ":" + str(suib_server_port) + "/SM/7/ws"
        conn_suib_payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
                            "xmlns:ns=\"http://schemas.hp.com/SM/7\">\r\n   <soapenv:Header/>\r\n   " \
                            "<soapenv:Body>\r\n      <ns:RetrieveIncidentNotifyListRequest>\r\n         <ns:keys " \
                            "query=\"gossopka.send=true and gossopka.ready=true and gossopka.sync=false and null(" \
                            "gossopka.id)\">\r\n            <ns:Id type=\"String\"/>\r\n         </ns:keys>\r\n      " \
                            "</ns:RetrieveIncidentNotifyListRequest>\r\n   </soapenv:Body>\r\n</soapenv:Envelope> "
        suib_headers = {
            'SOAPAction': '"RetrieveList"',
            'Connection': 'Close',
            'Content-Type': 'text/xml;charset=UTF-8',
            'Authorization': 'Basic ' + base64_auth_header
        }
        try:
            # Выполняем подключение к СУИБ
            conn_suib_response = requests.request("POST", suib_url, headers=suib_headers,
                                                  data=conn_suib_payload, timeout=suib_conn_timeout)
            if "DEBUG" in log_level:
                connector_logger(file_path=file_path, level=level_debug,
                                 message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                     suib_headers).replace(base64_auth_header, "********************") + " " + str(
                                     conn_suib_payload.replace("\r\n", "")) + "\r\n"))
                connector_logger(file_path=file_path, level=level_debug,
                                 message_text=("Ответ от СУИБ: " + str(conn_suib_response.text) + "\r\n"))
            else:
                pass
            parsed_text = xmltodict.parse(conn_suib_response.text, encoding='utf-8', namespace_separator=":")
            conn_suib_response_code = \
                parsed_text['SOAP-ENV:Envelope']['SOAP-ENV:Body']['RetrieveIncidentNotifyListResponse']['@returnCode']
            conn_suib_response_status = \
                parsed_text['SOAP-ENV:Envelope']['SOAP-ENV:Body']['RetrieveIncidentNotifyListResponse']['@status']
            if conn_suib_response_code == '0':  # имеются уведомления
                parsed_list = parsed_text['SOAP-ENV:Envelope']['SOAP-ENV:Body']['RetrieveIncidentNotifyListResponse'][
                    'instance']
                if isinstance(parsed_list, list):  # количество уведомлений > 1
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                "В СУИБ найдены уведомления для добавления в ГосСОПКА. Количество уведомлений -" + " " + str(
                            len(parsed_list)) + "\r\n"))
                    elif "INFO" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                "В СУИБ найдены уведомления для добавления в ГосСОПКА. Количество уведомлений -" + " " + str(
                            len(parsed_list)) + "\r\n"))
                    gossopka_success_updates, gossopka_failed_updates, suib_success_updates, suib_failed_updates = save_notifications_to_gossopka(
                        parsed_list=parsed_list)
                    print("Количество успешных добавленных уведомлений в ГосСОПКА - " + str(gossopka_success_updates))
                    print("Количество не добавленных уведомлений в ГосСОПКА - " + str(gossopka_failed_updates))
                    print("Количество успешных добавленных уведомлений в СУИБ - " + str(suib_success_updates))
                    print("Количество не добавленных уведомлений в СУИБ - " + str(suib_failed_updates))
                    if log_level == "DEBUG" or log_level == "INFO":
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text=log_suib_notifications_success)
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text="Количество успешно добавленных уведомлений в ГосСОПКА - " + str(
                                             gossopka_success_updates) + "\r\n")
                        if gossopka_failed_updates > 0:
                            connector_logger(file_path=file_path, level=level_error,
                                             message_text="Количество не добавленных уведомлений в ГосСОПКА - " + str(
                                                 gossopka_failed_updates) + "\r\n")
                        else:
                            pass
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text="Количество записей в СУИБ обновленных успешно - " + str(
                                             suib_success_updates) + "\r\n")
                        if suib_failed_updates > 0:
                            connector_logger(file_path=file_path, level=level_error,
                                             message_text="Количество записей, не обновленных в СУИБ - " + str(
                                                 suib_failed_updates) + "\r\n")
                        else:
                            pass
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text=log_sync_end)
                    elif log_level == "WARN" or log_level == "ERROR":
                        if gossopka_failed_updates > 0:
                            connector_logger(file_path=file_path, level=level_error,
                                             message_text="Количество не добавленных уведомлений в ГосСОПКА - " + str(
                                                 gossopka_failed_updates) + "\r\n")
                        elif suib_failed_updates > 0:
                            connector_logger(file_path=file_path, level=level_error,
                                             message_text="Количество записей, не обновленных в СУИБ - " + str(
                                                 suib_failed_updates) + "\r\n")
                    conn_suib_notifications_status = "Передача уведомлений в ГосСОПКУ и СУИБ прошла успешно"
                    success_connection += 1


                else:  # 1 - уведомление
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                "В СУИБ найдены уведомления для добавления в ГосСОПКА. Количество уведомлений -" + " " + "1" + "\r\n"))
                    elif "INFO" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                "В СУИБ найдены уведомления для добавления в ГосСОПКА. Количество уведомлений -" + " " + "1" + "\r\n"))
                    gossopka_success_updates, gossopka_failed_updates, suib_success_updates, suib_failed_updates = save_notification_to_gossopka(
                        parsed_list=parsed_list)
                    print("Количество успешных добавленных уведомлений в ГосСОПКА - " + str(gossopka_success_updates))
                    print("Количество не добавленных уведомлений в ГосСОПКА - " + str(gossopka_failed_updates))
                    print("Количество успешных добавленных уведомлений в СУИБ - " + str(suib_success_updates))
                    print("Количество не добавленных уведомлений в СУИБ - " + str(suib_failed_updates))
                    if log_level == "DEBUG" or log_level == "INFO":
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text=log_suib_notifications_success)
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text="Количество успешно добавленных уведомлений в ГосСОПКА - " + str(
                                             gossopka_success_updates) + "\r\n")
                        if gossopka_failed_updates > 0:
                            connector_logger(file_path=file_path, level=level_error,
                                             message_text="Количество не добавленных уведомлений в ГосСОПКА - " + str(
                                                 gossopka_failed_updates) + "\r\n")
                        else:
                            pass
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text="Количество записей в СУИБ обновленных успешно - " + str(
                                             suib_success_updates) + "\r\n")
                        if suib_failed_updates > 0:
                            connector_logger(file_path=file_path, level=level_error,
                                             message_text="Количество записей, не обновленных в СУИБ - " + str(
                                                 suib_failed_updates) + "\r\n")
                        else:
                            pass
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text=log_sync_end)
                    elif log_level == "WARN" or log_level == "ERROR":
                        if gossopka_failed_updates > 0:
                            connector_logger(file_path=file_path, level=level_error,
                                             message_text="Количество не добавленных уведомлений в ГосСОПКА - " + str(
                                                 gossopka_failed_updates) + "\r\n")
                        elif suib_failed_updates > 0:
                            connector_logger(file_path=file_path, level=level_error,
                                             message_text="Количество записей, не обновленных в СУИБ - " + str(
                                                 suib_failed_updates) + "\r\n")
                    conn_suib_notifications_status = "Передача уведомлений в ГосСОПКУ и СУИБ прошла успешно"
                    success_connection += 1

            elif conn_suib_response_code == '9':
                if log_level == "DEBUG" or log_level == "INFO":
                    connector_logger(file_path=file_path, level=level_info,
                                     message_text=log_suib_null_notifications)
                    connector_logger(file_path=file_path, level=level_info,
                                     message_text=log_sync_end)
                conn_suib_notifications_status = "В СУИБ не найдено уведомлений для передачи в ГосСОПКА"
                print(conn_suib_notifications_status)
                success_connection += 1
            else:
                if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
                    connector_logger(file_path=file_path, level=level_warn,
                                     message_text=log_suib_get_notifications_error)
                    connector_logger(file_path=file_path, level=level_warn,
                                     message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                         suib_headers).replace(base64_auth_header, "********************") + " " + str(
                                         conn_suib_payload.replace("\r\n", "")) + "\r\n"))
                    connector_logger(file_path=file_path, level=level_warn,
                                     message_text=("Ответ от СУИБ: " + str(conn_suib_response.text) + "\r\n"))

                    raise ValueError('FATAL')
        except requests.exceptions.RequestException as net_error:
            print("CУИБ недоступен: ", net_error)
            if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
                connector_logger(file_path=file_path, level=level_warn,
                                 message_text=log_suib_test_connect_unavailable)
            time.sleep(error_timeout)
            if log_level == "DEBUG" or log_level == "INFO":
                connector_logger(file_path=file_path, level=level_info,
                                 message_text=log_sync_end)
            conn_suib_notifications_status = "СУИБ недоступен"
            return conn_suib_notifications_status
        except ValueError:
            if log_level == "DEBUG" or log_level == "INFO":
                connector_logger(file_path=file_path, level=level_info,
                                 message_text=log_sync_end)
            conn_suib_notifications_status = "Проверка соединения с СУИБ завершилась ошибкой"
            return conn_suib_notifications_status
    return conn_suib_notifications_status


# 6.2, 6.3, 6.4 Добавление уведомлений в ГосСОПКА
def save_notification_to_gossopka(parsed_list):
    file_path = check_folder(log_path=log_path)
    gossopka_url = gossopka_ssl + "://" + gossopka_server_name + ":" + str(gossopka_server_port) + "/api/v2/incidents?"
    gossopka_headers = {
        'accept': 'application/json',
        'x-token': token,
    }
    event_id = parsed_list['Id']['#text']
    if "DEBUG" in log_level:
        connector_logger(file_path=file_path, level=level_info, message_text=(
                event_id + " " + "Обработка уведомления для добавления в ГосСОПКА\r\n"))
    elif "INFO" in log_level:
        connector_logger(file_path=file_path, level=level_info, message_text=(
                event_id + " " + "Обработка уведомления для добавления в ГосСОПКА\r\n"))
    technical_ready = parsed_list['GosSOPKATechnicalReady']['#text']
    gossopka_category = parsed_list['GosSOPKACategory']['#text']
    gossopka_type = parsed_list['GosSOPKAType']['#text']
    if "GosSOPKACompany" in parsed_list:
        gossopka_company = parsed_list['GosSOPKACompany']['#text']
    else:
        gossopka_company = str(gossopka_organization)
    if "GosSOPKAAssistance" in parsed_list:
        gossopka_assistance = parsed_list['GosSOPKAAssistance']['#text']
    else:
        gossopka_assistance = ''
    gossopka_tlp = parsed_list['GosSOPKATLP']['#text']
    gossopka_detecttime = parsed_list['GosSOPKADetectionTime']['#text']
    if "GosSOPKACompletionTime" in parsed_list:
        gossopka_endtime = parsed_list['GosSOPKACompletionTime']['#text']
    else:
        gossopka_endtime = ''
    gossopka_activitystatus = parsed_list['GosSOPKAState']['#text']
    if "GosSOPKADetectedSystem" in parsed_list:
        gossopka_detectiontool = parsed_list['GosSOPKADetectedSystem']['#text']
    else:
        gossopka_detectiontool = ''
    gossopka_affectedsystemname = parsed_list['GosSOPKASystemName']['#text']
    gossopka_affectedsystemcategory = parsed_list['GosSOPKASystemOCIIRatingName']['#text']
    gossopka_affectedsystemfunction = parsed_list['GosSOPKAScope']['#text']
    if "GosSOPKAInternet" in parsed_list:
        gossopka_affectedsystemconnection = parsed_list['GosSOPKAInternet']['#text']
    else:
        gossopka_affectedsystemconnection = ''
    gossopka_eventsdescription = parsed_list['GosSOPKADescription']
    if isinstance(gossopka_eventsdescription['GosSOPKADescription'], list):
        gossopka_eventdescription = ''
        for events in gossopka_eventsdescription['GosSOPKADescription']:
            gossopka_eventdescription_tolist = events['#text']
            gossopka_eventdescription += gossopka_eventdescription_tolist
            gossopka_eventdescription += '\n'
        gossopka_eventdescription = gossopka_eventdescription[:-1]
    else:
        gossopka_eventdescription = gossopka_eventsdescription['GosSOPKADescription']['#text']
    if "GosSOPKAIntegrityImpact" in parsed_list:
        gossopka_integrityimpact = parsed_list['GosSOPKAIntegrityImpact']['#text']
    else:
        gossopka_integrityimpact = ''
    if "GosSOPKAAvailabilityImpact" in parsed_list:
        gossopka_availabilityimpact = parsed_list['GosSOPKAAvailabilityImpact']['#text']
    else:
        gossopka_availabilityimpact = ''
    if "GosSOPKAAvailabilityImpact" in parsed_list:
        gossopka_confidentialityimpact = parsed_list['GosSOPKAPrivacyImpact']['#text']
    else:
        gossopka_confidentialityimpact = ''
    if "GosSOPKAOtherImpact" in parsed_list:
        gossopka_customimpacts = parsed_list['GosSOPKAOtherImpact']['GosSOPKAOtherImpact']
        if isinstance(gossopka_customimpacts, list):
            customimpact = ''
            for impacts in gossopka_customimpacts:
                customimpact_tolist = impacts['#text']
                customimpact += customimpact_tolist
                customimpact += '\n'
            gossopka_customimpact = customimpact[:-1]
        else:
            gossopka_customimpact = gossopka_customimpacts['#text']
    else:
        gossopka_customimpact = ''
    gossopka_location = parsed_list['GosSOPKARegion']['#text']
    if "GosSOPKACity" in parsed_list:
        gossopka_city = parsed_list['GosSOPKACity']['#text']
    else:
        gossopka_city = ''
    if "gossopka.products" in parsed_list:
        gossopka_products_info = parsed_list['gossopka.products']
        gossopka_product_info = gossopka_products_info['gossopka.products']
        if isinstance(gossopka_product_info, list):
            product_info_dict = {}
            product_info_list_of_dicts = []
            for products in gossopka_product_info:
                if "GosSOPKAProductName" in products:
                    product_name = products['GosSOPKAProductName']['#text']
                else:
                    product_name = ''
                if "GosSOPKAProductVersion" in products:
                    product_version = products['GosSOPKAProductVersion']['#text']
                else:
                    product_version = ''
                product_info_dict['name'] = product_name
                product_info_dict['version'] = product_version
                product_info_list_of_dicts.append(product_info_dict)
                product_info_dict = {}
        else:
            product_info_dict = {}
            product_info_list_of_dicts = []
            if "GosSOPKAProductName" in gossopka_product_info:
                product_name = gossopka_product_info['GosSOPKAProductName']['#text']
            else:
                product_name = ''
            if "GosSOPKAProductVersion" in gossopka_product_info:
                product_version = gossopka_product_info['GosSOPKAProductVersion']['#text']
            else:
                product_version = ''
            product_info_dict['name'] = product_name
            product_info_dict['version'] = product_version
            product_info_list_of_dicts.append(product_info_dict)
    else:
        product_info_list_of_dicts = ''
    if "GosSOPKAVulnerId" in parsed_list:
        gossopka_vulnerid = parsed_list['GosSOPKAVulnerId']['#text']
    else:
        gossopka_vulnerid = ''
    if "GosSOPKAProductCategory" in parsed_list:
        gossopka_product_category = parsed_list['GosSOPKAProductCategory']['#text']
    else:
        gossopka_product_category = ''
    if "gossopka.injureds.ipv4" in parsed_list:
        gossopka_injureds_ipv4 = parsed_list['gossopka.injureds.ipv4']
        gossopka_injured_ipv4 = gossopka_injureds_ipv4['gossopka.injureds.ipv4']
        if isinstance(gossopka_injured_ipv4, list):
            injured_ipv4_dict = {}
            injured_ipv4_list_of_dicts = []
            for injureds in gossopka_injured_ipv4:
                if "GosSOPKAInjuredIPv4" in injureds:
                    injured_ipv4 = injureds['GosSOPKAInjuredIPv4']['#text']
                    injured_ipv4_dict['value'] = injured_ipv4
                    injured_ipv4_list_of_dicts.append(injured_ipv4_dict)
                    injured_ipv4_dict = {}
                else:
                    injured_ipv4 = ''
                    injured_ipv4_dict = {}
        else:
            injured_ipv4_dict = {}
            injured_ipv4_list_of_dicts = []
            if "GosSOPKAInjuredIPv4" in gossopka_injured_ipv4:
                injured_ipv4 = gossopka_injured_ipv4['GosSOPKAInjuredIPv4']['#text']
                injured_ipv4_dict['value'] = injured_ipv4
                injured_ipv4_list_of_dicts.append(injured_ipv4_dict)
            else:
                injured_ipv4 = ''
    else:
        injured_ipv4_list_of_dicts = ''
    if "gossopka.injureds.ipv6" in parsed_list:
        gossopka_injureds_ipv6 = parsed_list['gossopka.injureds.ipv6']
        gossopka_injured_ipv6 = gossopka_injureds_ipv6['gossopka.injureds.ipv6']
        if isinstance(gossopka_injured_ipv6, list):
            injured_ipv6_dict = {}
            injured_ipv6_list_of_dicts = []
            for injureds in gossopka_injured_ipv6:
                if "GosSOPKAInjuredIPv6" in injureds:
                    injured_ipv6 = injureds['GosSOPKAInjuredIPv6']['#text']
                    injured_ipv6_dict['value'] = injured_ipv6
                    injured_ipv6_list_of_dicts.append(injured_ipv6_dict)
                    injured_ipv6_dict = {}
                else:
                    injured_ipv6 = ''
                    injured_ipv6_dict = {}
        else:
            injured_ipv6_dict = {}
            injured_ipv6_list_of_dicts = []
            if "GosSOPKAInjuredIPv6" in gossopka_injured_ipv6:
                injured_ipv6 = gossopka_injured_ipv6['GosSOPKAInjuredIPv6']['#text']
                injured_ipv6_dict['value'] = injured_ipv6
                injured_ipv6_list_of_dicts.append(injured_ipv6_dict)
            else:
                injured_ipv6 = ''
    else:
        injured_ipv6_list_of_dicts = ''
    if "gossopka.injureds.domain" in parsed_list:
        gossopka_injureds_domain = parsed_list['gossopka.injureds.domain']
        gossopka_injured_domain = gossopka_injureds_domain['gossopka.injureds.domain']
        if isinstance(gossopka_injured_domain, list):
            injured_domain_dict = {}
            injured_domain_list_of_dicts = []
            for injureds in gossopka_injured_domain:
                if "GosSOPKAInjuredDomain" in injureds:
                    injured_domains = injureds['GosSOPKAInjuredDomain']['#text']
                    injured_domain_dict['value'] = injured_domains
                    injured_domain_list_of_dicts.append(injured_domain_dict)
                    injured_domain_dict = {}
                else:
                    injured_domains = ''
                    injured_domain_dict = {}
        else:
            injured_domain_dict = {}
            injured_domain_list_of_dicts = []
            if "GosSOPKAInjuredDomain" in gossopka_injured_domain:
                injured_domains = gossopka_injured_domain['GosSOPKAInjuredDomain']['#text']
                injured_domain_dict['value'] = injured_domains
                injured_domain_list_of_dicts.append(injured_domain_dict)
            else:
                injured_domains = ''
    else:
        injured_domain_list_of_dicts = ''
    if "gossopka.injureds.uri" in parsed_list:
        gossopka_injureds_uri = parsed_list['gossopka.injureds.uri']
        gossopka_injured_uri = gossopka_injureds_uri['gossopka.injureds.uri']
        if isinstance(gossopka_injured_uri, list):
            injured_uri_dict = {}
            injured_uri_list_of_dicts = []
            for injureds in gossopka_injured_uri:
                if "GosSOPKAInjuredURI" in injureds:
                    injured_uri = injureds['GosSOPKAInjuredURI']['#text']
                    injured_uri_dict['value'] = injured_uri
                    injured_uri_list_of_dicts.append(injured_uri_dict)
                    injured_uri_dict = {}
                else:
                    injured_uri = ''
                    injured_uri_dict = {}
        else:
            injured_uri_dict = {}
            injured_uri_list_of_dicts = []
            if "GosSOPKAInjuredURI" in gossopka_injured_uri:
                injured_uri = gossopka_injured_uri['GosSOPKAInjuredURI']['#text']
                injured_uri_dict['value'] = injured_uri
                injured_uri_list_of_dicts.append(injured_uri_dict)
            else:
                injured_uri = ''
    else:
        injured_uri_list_of_dicts = ''
    if "gossopka.injureds.email" in parsed_list:
        gossopka_injureds_email = parsed_list['gossopka.injureds.email']
        gossopka_injured_email = gossopka_injureds_email['gossopka.injureds.email']
        if isinstance(gossopka_injured_email, list):
            injured_email_dict = {}
            injured_email_list_of_dicts = []
            for injureds in gossopka_injured_email:
                if "GosSOPKAInjuredEmail" in injureds:
                    injured_email = injureds['GosSOPKAInjuredEmail']['#text']
                    injured_email_dict['value'] = injured_email
                    injured_email_list_of_dicts.append(injured_email_dict)
                    injured_email_dict = {}
                else:
                    injured_email = ''
                    injured_email_dict = {}
        else:
            injured_email_dict = {}
            injured_email_list_of_dicts = []
            if "GosSOPKAInjuredEmail" in gossopka_injured_email:
                injured_email = gossopka_injured_email['GosSOPKAInjuredEmail']['#text']
                injured_email_dict['value'] = injured_email
                injured_email_list_of_dicts.append(injured_email_dict)
            else:
                injured_email = ''
    else:
        injured_email_list_of_dicts = ''
    if "gossopka.injureds.service" in parsed_list:
        gossopka_injureds_service = parsed_list['gossopka.injureds.service']
        gossopka_injured_service = gossopka_injureds_service['gossopka.injureds.service']
        if isinstance(gossopka_injured_service, list):
            injured_service_port_dict = {}
            injured_service_port_list_of_dicts = []
            for injureds in gossopka_injured_service:
                if "GosSOPKAInjuredServiceName" in injureds:
                    injured_service = injureds['GosSOPKAInjuredServiceName']['#text']
                else:
                    injured_service = ''
                if "GosSOPKAInjuredServicePort" in injureds:
                    injured_port = injureds['GosSOPKAInjuredServicePort']['#text']
                else:
                    injured_port = ''
                injured_service_port_dict['name'] = injured_service
                injured_service_port_dict['value'] = injured_port
                injured_service_port_list_of_dicts.append(injured_service_port_dict)
                injured_service_port_dict = {}
        else:
            injured_service_port_dict = {}
            injured_service_port_list_of_dicts = []
            injured_service = gossopka_injured_service['GosSOPKAInjuredServiceName']['#text']
            injured_port = gossopka_injured_service['GosSOPKAInjuredServicePort']['#text']
            injured_service_port_dict['name'] = injured_service
            injured_service_port_dict['value'] = injured_port
            injured_service_port_list_of_dicts.append(injured_service_port_dict)
    else:
        injured_service_port_list_of_dicts = ''
    if "GosSOPKAInjuredsAsPath" in parsed_list:
        injured_aspath = parsed_list['GosSOPKAInjuredsAsPath']['#text']
    else:
        injured_aspath = ''
    if "gossopka.attackers.ipv4" in parsed_list:
        gossopka_attackers_ipv4 = parsed_list['gossopka.attackers.ipv4']
        gossopka_attacker_ipv4 = gossopka_attackers_ipv4['gossopka.attackers.ipv4']
        if isinstance(gossopka_attacker_ipv4, list):
            attacker_ipv4_dict = {}
            attacker_ipv4_list_of_dicts = []
            for attackers in gossopka_attacker_ipv4:
                if "GosSOPKAAttackerIPv4" in attackers:
                    attackers_ipv4 = attackers['GosSOPKAAttackerIPv4']['#text']
                else:
                    attackers_ipv4 = ''
                if "GosSOPKAAttackerIPv4Function" in attackers:
                    attackers_ipv4_function = attackers['GosSOPKAAttackerIPv4Function']['#text']
                else:
                    attackers_ipv4_function = ''
                if attackers_ipv4 == '':
                    attacker_ipv4_dict = {}
                else:
                    attacker_ipv4_dict['function'] = attackers_ipv4_function
                    attacker_ipv4_dict['value'] = attackers_ipv4
                    attacker_ipv4_list_of_dicts.append(attacker_ipv4_dict)
                    attacker_ipv4_dict = {}
        else:
            attacker_ipv4_dict = {}
            attacker_ipv4_list_of_dicts = []
            if "GosSOPKAAttackerIPv4" in gossopka_attacker_ipv4:
                attackers_ipv4 = gossopka_attacker_ipv4['GosSOPKAAttackerIPv4']['#text']
            else:
                attackers_ipv4 = ''
            if "GosSOPKAAttackerIPv4Function" in gossopka_attacker_ipv4:
                attackers_ipv4_function = gossopka_attacker_ipv4['GosSOPKAAttackerIPv4Function']['#text']
            else:
                attackers_ipv4_function = ''
            if attackers_ipv4 == '':
                pass
            else:
                attacker_ipv4_dict['function'] = attackers_ipv4_function
                attacker_ipv4_dict['value'] = attackers_ipv4
                attacker_ipv4_list_of_dicts.append(attacker_ipv4_dict)
    else:
        attacker_ipv4_list_of_dicts = ''
    if "gossopka.attackers.ipv6" in parsed_list:
        gossopka_attackers_ipv6 = parsed_list['gossopka.attackers.ipv6']
        gossopka_attacker_ipv6 = gossopka_attackers_ipv6['gossopka.attackers.ipv6']
        if isinstance(gossopka_attacker_ipv6, list):
            attacker_ipv6_dict = {}
            attacker_ipv6_list_of_dicts = []
            for attackers in gossopka_attacker_ipv6:
                if "GosSOPKAAttackerIPv6" in attackers:
                    attackers_ipv6 = attackers['GosSOPKAAttackerIPv6']['#text']
                else:
                    attackers_ipv6 = ''
                if "GosSOPKAAttackerIPv6Function" in attackers:
                    attackers_ipv6_function = attackers['GosSOPKAAttackerIPv6Function']['#text']
                else:
                    attackers_ipv6_function = ''
                if attackers_ipv6 == '':
                    attacker_ipv6_dict = {}
                else:
                    attacker_ipv6_dict['function'] = attackers_ipv6_function
                    attacker_ipv6_dict['value'] = attackers_ipv6
                    attacker_ipv6_list_of_dicts.append(attacker_ipv6_dict)
                    attacker_ipv6_dict = {}
        else:
            attacker_ipv6_dict = {}
            attacker_ipv6_list_of_dicts = []
            if "GosSOPKAAttackerIPv6" in gossopka_attacker_ipv6:
                attackers_ipv6 = gossopka_attacker_ipv6['GosSOPKAAttackerIPv6']['#text']
            else:
                attackers_ipv6 = ''
            if "GosSOPKAAttackerIPv6Function" in gossopka_attacker_ipv6:
                attackers_ipv6_function = gossopka_attacker_ipv6['GosSOPKAAttackerIPv6Function']['#text']
            else:
                attackers_ipv6_function = ''
            if attackers_ipv6 == '':
                pass
            else:
                attacker_ipv6_dict['function'] = attackers_ipv6_function
                attacker_ipv6_dict['value'] = attackers_ipv6
                attacker_ipv6_list_of_dicts.append(attacker_ipv6_dict)
    else:
        attacker_ipv6_list_of_dicts = ''
    if "gossopka.attackers.domain" in parsed_list:
        gossopka_attackers_domain = parsed_list['gossopka.attackers.domain']
        gossopka_attacker_domain = gossopka_attackers_domain['gossopka.attackers.domain']
        if isinstance(gossopka_attacker_domain, list):
            attacker_domain_dict = {}
            attacker_domain_list_of_dicts = []
            for attackers in gossopka_attacker_domain:
                if "GosSOPKAAttackerDomain" in attackers:
                    attackers_domain = attackers['GosSOPKAAttackerDomain']['#text']
                else:
                    attackers_domain = ''
                if "GosSOPKAAttackerDomainFunction" in attackers:
                    attackers_domain_function = attackers['GosSOPKAAttackerDomainFunction'][
                        '#text']
                else:
                    attackers_domain_function = ''
                if attackers_domain == '':
                    attacker_domain_dict = {}
                else:
                    attacker_domain_dict['function'] = attackers_domain_function
                    attacker_domain_dict['value'] = attackers_domain
                    attacker_domain_list_of_dicts.append(attacker_domain_dict)
                    attacker_domain_dict = {}
        else:
            attacker_domain_dict = {}
            attacker_domain_list_of_dicts = []
            if "GosSOPKAAttackerDomain" in gossopka_attacker_domain:
                attackers_domain = gossopka_attacker_domain['GosSOPKAAttackerDomain']['#text']
            else:
                attackers_domain = ''
            if "GosSOPKAAttackerDomainFunction" in gossopka_attacker_domain:
                attackers_domain_function = gossopka_attacker_domain['GosSOPKAAttackerDomainFunction']['#text']
            else:
                attackers_domain_function = ''
            if attackers_domain == '':
                pass
            else:
                attacker_domain_dict['function'] = attackers_domain_function
                attacker_domain_dict['value'] = attackers_domain
                attacker_domain_list_of_dicts.append(attacker_domain_dict)
    else:
        attacker_domain_list_of_dicts = ''
    if "gossopka.attackers.uri" in parsed_list:
        gossopka_attackers_uri = parsed_list['gossopka.attackers.uri']
        gossopka_attacker_uri = gossopka_attackers_uri['gossopka.attackers.uri']
        if isinstance(gossopka_attacker_uri, list):
            attacker_uri_dict = {}
            attacker_uri_list_of_dicts = []
            for attackers in gossopka_attacker_uri:
                if "GosSOPKAAttackerURI" in attackers:
                    attackers_uri = attackers['GosSOPKAAttackerURI']['#text']
                else:
                    attackers_uri = ''
                if "GosSOPKAAttackerURIFunction" in attackers:
                    attackers_uri_function = attackers['GosSOPKAAttackerURIFunction']['#text']
                else:
                    attackers_uri_function = ''
                if attackers_uri == '':
                    attacker_uri_dict = {}
                else:
                    attacker_uri_dict['function'] = attackers_uri_function
                    attacker_uri_dict['value'] = attackers_uri
                    attacker_uri_list_of_dicts.append(attacker_uri_dict)
                    attacker_uri_dict = {}
        else:
            attacker_uri_dict = {}
            attacker_uri_list_of_dicts = []
            if "GosSOPKAAttackerURI" in gossopka_attacker_uri:
                attackers_uri = gossopka_attacker_uri['GosSOPKAAttackerURI']['#text']
            else:
                attackers_uri = ''
            if "GosSOPKAAttackerURIFunction" in gossopka_attacker_uri:
                attackers_uri_function = gossopka_attacker_uri['GosSOPKAAttackerURIFunction']['#text']
            else:
                attackers_uri_function = ''
            if attackers_uri == '':
                pass
            else:
                attacker_uri_dict['function'] = attackers_uri_function
                attacker_uri_dict['value'] = attackers_uri
                attacker_uri_list_of_dicts.append(attacker_uri_dict)
    else:
        attacker_uri_list_of_dicts = ''
    if "gossopka.attackers.email" in parsed_list:
        gossopka_attackers_email = parsed_list['gossopka.attackers.email']
        gossopka_attacker_email = gossopka_attackers_email['gossopka.attackers.email']
        if isinstance(gossopka_attacker_email, list):
            attacker_email_dict = {}
            attacker_email_list_of_dicts = []
            for attackers in gossopka_attacker_email:
                attackers_email = attackers['GosSOPKAAttackerEmail']['#text']
                attacker_email_dict['value'] = attackers_email
                attacker_email_list_of_dicts.append(attacker_email_dict)
                attacker_email_dict = {}
        else:
            attacker_email_dict = {}
            attacker_email_list_of_dicts = []
            attackers_email = gossopka_attacker_email['GosSOPKAAttackerEmail']['#text']
            attacker_email_dict['value'] = attackers_email
            attacker_email_list_of_dicts.append(attacker_email_dict)
    else:
        attacker_email_list_of_dicts = ''
    if "gossopka.attackers.hash" in parsed_list:
        gossopka_attackers_hash = parsed_list['gossopka.attackers.hash']
        gossopka_attacker_hash = gossopka_attackers_hash['gossopka.attackers.hash']
        if isinstance(gossopka_attacker_hash, list):
            attacker_hash_dict = {}
            attacker_hash_list_of_dicts = []
            for attackers in gossopka_attacker_hash:
                attackers_hash = attackers['GosSOPKAAttackerHash']['#text']
                attacker_hash_dict['value'] = attackers_hash
                attacker_hash_list_of_dicts.append(attacker_hash_dict)
                attacker_hash_dict = {}
        else:
            attacker_hash_dict = {}
            attacker_hash_list_of_dicts = []
            attackers_hash = gossopka_attacker_hash['GosSOPKAAttackerHash']['#text']
            attacker_hash_dict['value'] = attackers_hash
            attacker_hash_list_of_dicts.append(attacker_hash_dict)
    else:
        attacker_hash_list_of_dicts = ''
    if "gossopka.attackers.vulner" in parsed_list:
        gossopka_attackers_vulner = parsed_list['gossopka.attackers.vulner']
        gossopka_attacker_vulner = gossopka_attackers_vulner['gossopka.attackers.vulner']
        if isinstance(gossopka_attacker_vulner, list):
            attacker_vulner_dict = {}
            attacker_vulner_list_of_dicts = []
            for attackers in gossopka_attacker_vulner:
                attackers_vulner = attackers['GosSOPKAAttackerVulner']['#text']
                attacker_vulner_dict['value'] = attackers_vulner
                attacker_vulner_list_of_dicts.append(attacker_vulner_dict)
                attacker_vulner_dict = {}
        else:
            attacker_vulner_dict = {}
            attacker_vulner_list_of_dicts = []
            attackers_vulner = gossopka_attacker_vulner['GosSOPKAAttackerVulner']['#text']
            attacker_vulner_dict['value'] = attackers_vulner
            attacker_vulner_list_of_dicts.append(attacker_vulner_dict)
    else:
        attacker_vulner_list_of_dicts = ''
    if "GosSOPKAAttackerASN" in parsed_list:
        gossopka_attackerasn = parsed_list['GosSOPKAAttackerASN']['#text']
    else:
        gossopka_attackerasn = ''
    if "GosSOPKAAttackerAS" in parsed_list:
        gossopka_attackeras = parsed_list['GosSOPKAAttackerAS']['#text']
    else:
        gossopka_attackeras = ''
    if "GosSOPKAAttackerLIR" in parsed_list:
        gossopka_attackerlir = parsed_list['GosSOPKAAttackerLIR']['#text']
    else:
        gossopka_attackerlir = ''
    try:
        gossopka_success_updates = 0
        gossopka_failed_updates = 0
        suib_success_updates = 0
        suib_failed_updates = 0
        if "Уведомление о компьютерном инциденте" in gossopka_category:  # уведомление о компьютерном инциденте
            if technical_ready == 'true':
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            event_id + " " + "Добавление уведомления о компьютерном инциденте в ГосСОПКА с техническими сведениями\r\n"))
                else:
                    pass
                incident_notification = json.dumps({
                    "company": gossopka_company,
                    "category": gossopka_category,
                    "type": gossopka_type,
                    "activitystatus": gossopka_activitystatus,
                    "assistance": gossopka_assistance,
                    "eventdescription": gossopka_eventdescription,
                    "detectiontool": gossopka_detectiontool,
                    "detecttime": gossopka_detecttime,
                    "endtime": gossopka_endtime,
                    "tlp": gossopka_tlp,
                    "availabilityimpact": gossopka_availabilityimpact,
                    "integrityimpact": gossopka_integrityimpact,
                    "confidentialityimpact": gossopka_confidentialityimpact,
                    "customimpact": gossopka_customimpact,
                    "affectedsystemname": gossopka_affectedsystemname,
                    "affectedsystemcategory": gossopka_affectedsystemcategory,
                    "affectedsystemfunction": gossopka_affectedsystemfunction,
                    "affectedsystemconnection": gossopka_affectedsystemconnection,
                    "location": gossopka_location,
                    "city": gossopka_city,
                    "relatedobservablesipv4": injured_ipv4_list_of_dicts,
                    "relatedobservablesipv6": injured_ipv6_list_of_dicts,
                    "relatedobservablesdomain": injured_domain_list_of_dicts,
                    "relatedobservablesuri": injured_uri_list_of_dicts,
                    "relatedobservablesemail": injured_email_list_of_dicts,
                    "relatedobservablesservice": injured_service_port_list_of_dicts,
                    "relatedobservablesaspath": injured_aspath,
                    "relatedindicatorsipv4": attacker_ipv4_list_of_dicts,
                    "relatedindicatorsipv6": attacker_ipv6_list_of_dicts,
                    "relatedindicatorsdomain": attacker_domain_list_of_dicts,
                    "relatedindicatorsuri": attacker_uri_list_of_dicts,
                    "relatedindicatorsemail": attacker_email_list_of_dicts,
                    "malwarehash": attacker_hash_list_of_dicts,
                    "relatedindicatorsvuln": attacker_vulner_list_of_dicts,
                    "relatedindicatorsasn": gossopka_attackerasn,
                    "relatedindicatorsas": gossopka_attackeras,
                    "relatedindicatorsaslir": gossopka_attackerlir
                })
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(gossopka_headers).replace(
                        token, "***************************") + " " + str(json.loads(incident_notification)) + "\r\n"))
                else:
                    pass
                gossopka_response = requests.request("POST", gossopka_url,
                                                     headers=gossopka_headers,
                                                     data=incident_notification, verify=False)
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                else:
                    pass
                gossopka_response_text = json.loads(gossopka_response.text)
                gossopka_response_status_code = str(gossopka_response.status_code)
            else:
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            event_id + " " + "Добавление уведомления о компьютерном инциденте в ГосСОПКА без технических сведений\r\n"))
                else:
                    pass
                incident_notification = json.dumps({
                    "company": gossopka_company,
                    "category": gossopka_category,
                    "type": gossopka_type,
                    "activitystatus": gossopka_activitystatus,
                    "assistance": gossopka_assistance,
                    "eventdescription": gossopka_eventdescription,
                    "detectiontool": gossopka_detectiontool,
                    "detecttime": gossopka_detecttime,
                    "endtime": gossopka_endtime,
                    "tlp": gossopka_tlp,
                    "availabilityimpact": gossopka_availabilityimpact,
                    "integrityimpact": gossopka_integrityimpact,
                    "confidentialityimpact": gossopka_confidentialityimpact,
                    "customImpact": gossopka_customimpact,
                    "affectedsystemname": gossopka_affectedsystemname,
                    "affectedsystemcategory": gossopka_affectedsystemcategory,
                    "affectedsystemfunction": gossopka_affectedsystemfunction,
                    "affectedsystemconnection": gossopka_affectedsystemconnection,
                    "location": gossopka_location,
                    "city": gossopka_city
                })
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(gossopka_headers).replace(
                        token, "***************************") + " " + str(json.loads(incident_notification)) + "\r\n"))
                else:
                    pass
                gossopka_response = requests.request("POST", gossopka_url,
                                                     headers=gossopka_headers,
                                                     data=incident_notification, verify=False)
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                else:
                    pass
                gossopka_response_text = json.loads(gossopka_response.text)
                gossopka_response_status_code = str(gossopka_response.status_code)
            if gossopka_response_status_code == '200' or gossopka_response_status_code == '201':
                gossopka_success_updates += 1
                log_uuid = str(gossopka_response_text['data'][0]['uuid'])
                log_identifier = str(gossopka_response_text['data'][0]['identifier']).replace("INC", prefix)
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_info, message_text=(
                            event_id + " " + "Уведомление о компьютерном инциденте успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                elif "INFO" in log_level:
                    connector_logger(file_path=file_path, level=level_info, message_text=(
                            event_id + " " + "Уведомление о компьютерном инциденте успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                save_success_notification_to_suib_result = str(
                    save_success_notification_to_suib(event_id=event_id, log_uuid=log_uuid,
                                                      log_identifier=log_identifier,
                                                      incident_notification=incident_notification,
                                                      gossopka_response_text=gossopka_response_text))
                print(save_success_notification_to_suib_result)
                if "прошла успешно" in save_success_notification_to_suib_result:
                    suib_success_updates += 1
                else:
                    suib_failed_updates += 1
            else:
                gossopka_failed_updates += 1
                if log_level == 'DEBUG' or log_level == 'INFO' or log_level == 'WARN':
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            event_id + " " + "Возникла ошибка при передаче уведомления о компьютерном инциденте в ГосСОПКА\r\n"))
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                        gossopka_headers).replace(token, "***************************") + " " + str(
                        json.loads(incident_notification)) + "\r\n"))
                    connector_logger(file_path=file_path, level=level_warn,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                save_error_notification_to_suib_result = str(
                    save_error_notification_to_suib(event_id=event_id, incident_notification=incident_notification,
                                                    gossopka_response_text=gossopka_response_text))
                print(save_error_notification_to_suib_result)
                if "прошла успешно" in save_error_notification_to_suib_result:
                    suib_success_updates += 1
                else:
                    suib_failed_updates += 1
        elif "Уведомление о компьютерной атаке" in gossopka_category:  # уведомление о компьютерной атаке
            if technical_ready == 'true':
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            event_id + " " + "Добавление уведомления о компьютерной атаке в ГосСОПКА с техническими сведениями\r\n"))
                else:
                    pass
                incident_notification = json.dumps({
                    "company": gossopka_company,
                    "category": gossopka_category,
                    "type": gossopka_type,
                    "activitystatus": gossopka_activitystatus,
                    "assistance": gossopka_assistance,
                    "eventdescription": gossopka_eventdescription,
                    "detectiontool": gossopka_detectiontool,
                    "detecttime": gossopka_detecttime,
                    "endtime": gossopka_endtime,
                    "tlp": gossopka_tlp,
                    "availabilityimpact": gossopka_availabilityimpact,
                    "integrityimpact": gossopka_integrityimpact,
                    "confidentialityimpact": gossopka_confidentialityimpact,
                    "customimpact": gossopka_customimpact,
                    "affectedsystemname": gossopka_affectedsystemname,
                    "affectedsystemcategory": gossopka_affectedsystemcategory,
                    "affectedsystemfunction": gossopka_affectedsystemfunction,
                    "affectedsystemconnection": gossopka_affectedsystemconnection,
                    "location": gossopka_location,
                    "city": gossopka_city,
                    "relatedobservablesipv4": injured_ipv4_list_of_dicts,
                    "relatedobservablesipv6": injured_ipv6_list_of_dicts,
                    "relatedobservablesdomain": injured_domain_list_of_dicts,
                    "relatedobservablesuri": injured_uri_list_of_dicts,
                    "relatedobservablesemail": injured_email_list_of_dicts,
                    "relatedobservablesservice": injured_service_port_list_of_dicts,
                    "relatedindicatorsipv4": attacker_ipv4_list_of_dicts,
                    "relatedindicatorsipv6": attacker_ipv6_list_of_dicts,
                    "relatedindicatorsdomain": attacker_domain_list_of_dicts,
                    "relatedindicatorsuri": attacker_uri_list_of_dicts,
                    "relatedindicatorsemail": attacker_email_list_of_dicts,
                    "malwarehash": attacker_hash_list_of_dicts,
                    "relatedindicatorsvuln": attacker_vulner_list_of_dicts
                })
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(gossopka_headers).replace(
                        token, "***************************") + " " + str(json.loads(incident_notification)) + "\r\n"))
                else:
                    pass
                gossopka_response = requests.request("POST", gossopka_url,
                                                     headers=gossopka_headers,
                                                     data=incident_notification, verify=False)
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                else:
                    pass
                gossopka_response_text = json.loads(gossopka_response.text)
                gossopka_response_status_code = str(gossopka_response.status_code)
            else:
                print("Уведомление о компьютерной атаке без технических данных")
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            event_id + " " + "Добавление уведомления о компьютерной атаке в ГосСОПКА без технических сведений\r\n"))
                else:
                    pass
                incident_notification = json.dumps({
                    "company": gossopka_company,
                    "category": gossopka_category,
                    "type": gossopka_type,
                    "activitystatus": gossopka_activitystatus,
                    "assistance": gossopka_assistance,
                    "eventdescription": gossopka_eventdescription,
                    "detectiontool": gossopka_detectiontool,
                    "detecttime": gossopka_detecttime,
                    "endtime": gossopka_endtime,
                    "tlp": gossopka_tlp,
                    "availabilityimpact": gossopka_availabilityimpact,
                    "integrityimpact": gossopka_integrityimpact,
                    "confidentialityimpact": gossopka_confidentialityimpact,
                    "customImpact": gossopka_customimpact,
                    "affectedsystemname": gossopka_affectedsystemname,
                    "affectedsystemcategory": gossopka_affectedsystemcategory,
                    "affectedsystemfunction": gossopka_affectedsystemfunction,
                    "affectedsystemconnection": gossopka_affectedsystemconnection,
                    "location": gossopka_location,
                    "city": gossopka_city
                })
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(gossopka_headers).replace(
                        token, "***************************") + " " + str(json.loads(incident_notification)) + "\r\n"))
                else:
                    pass
                gossopka_response = requests.request("POST", gossopka_url,
                                                     headers=gossopka_headers,
                                                     data=incident_notification, verify=False)
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                else:
                    pass
                gossopka_response_text = json.loads(gossopka_response.text)
                gossopka_response_status_code = str(gossopka_response.status_code)
            if gossopka_response_status_code == '200' or gossopka_response_status_code == '201':
                gossopka_success_updates += 1
                log_uuid = str(gossopka_response_text['data'][0]['uuid'])
                log_identifier = str(gossopka_response_text['data'][0]['identifier']).replace("INC", prefix)
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_info, message_text=(
                            event_id + " " + "Уведомление о компьютерной атаке успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                elif "INFO" in log_level:
                    connector_logger(file_path=file_path, level=level_info, message_text=(
                            event_id + " " + "Уведомление о компьютерной атаке успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                save_success_notification_to_suib_result = str(
                    save_success_notification_to_suib(event_id=event_id, log_uuid=log_uuid,
                                                      log_identifier=log_identifier,
                                                      incident_notification=incident_notification,
                                                      gossopka_response_text=gossopka_response_text))
                print(save_success_notification_to_suib_result)
                if "прошла успешно" in save_success_notification_to_suib_result:
                    suib_success_updates += 1
                else:
                    suib_failed_updates += 1
            else:
                gossopka_failed_updates += 1
                if log_level == 'DEBUG' or log_level == 'INFO' or log_level == 'WARN':
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            event_id + " " + "Возникла ошибка при передаче уведомления о компьютерной атаке в ГосСОПКА\r\n"))
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                        gossopka_headers).replace(token, "***************************") + " " + str(
                        json.loads(incident_notification)) + "\r\n"))
                    connector_logger(file_path=file_path, level=level_warn,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                save_error_notification_to_suib_result = str(
                    save_error_notification_to_suib(event_id=event_id, incident_notification=incident_notification,
                                                    gossopka_response_text=gossopka_response_text))
                print(save_error_notification_to_suib_result)
                if "прошла успешно" in save_error_notification_to_suib_result:
                    suib_success_updates += 1
                else:
                    suib_failed_updates += 1
        elif "Уведомление о наличии уязвимости" in gossopka_category:  # уведомление о наличии уязвимости
            if technical_ready == 'true':
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            event_id + " " + "Добавление уведомления по уязвимости в ГосСОПКА с техническими сведениями\r\n"))
                else:
                    pass
                incident_notification = json.dumps({
                    "company": gossopka_company,
                    "category": gossopka_category,
                    "type": gossopka_type,
                    "activitystatus": gossopka_activitystatus,
                    "assistance": gossopka_assistance,
                    "eventdescription": gossopka_eventdescription,
                    "detectiontool": gossopka_detectiontool,
                    "detecttime": gossopka_detecttime,
                    "endtime": gossopka_endtime,
                    "tlp": gossopka_tlp,
                    "affectedsystemname": gossopka_affectedsystemname,
                    "affectedsystemcategory": gossopka_affectedsystemcategory,
                    "affectedsystemfunction": gossopka_affectedsystemfunction,
                    "affectedsystemconnection": gossopka_affectedsystemconnection,
                    "location": gossopka_location,
                    "city": gossopka_city,
                    "relatedobservablesipv4": injured_ipv4_list_of_dicts,
                    "relatedobservablesipv6": injured_ipv6_list_of_dicts,
                    "relatedobservablesdomain": injured_domain_list_of_dicts,
                    "relatedobservablesuri": injured_uri_list_of_dicts,
                    "relatedobservablesservice": injured_service_port_list_of_dicts,
                    "productinfo": product_info_list_of_dicts,
                    "vulnerabilityid": gossopka_vulnerid,
                    "productCategory": gossopka_product_category
                })
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(gossopka_headers).replace(
                        token, "***************************") + " " + str(json.loads(incident_notification)) + "\r\n"))
                else:
                    pass
                gossopka_response = requests.request("POST", gossopka_url,
                                                     headers=gossopka_headers,
                                                     data=incident_notification, verify=False)
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                else:
                    pass
                gossopka_response_text = json.loads(gossopka_response.text)
                gossopka_response_status_code = str(gossopka_response.status_code)
            else:
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            event_id + " " + "Добавление уведомления по уязвимости в ГосСОПКА без технических сведений\r\n"))
                else:
                    pass
                incident_notification = json.dumps({
                    "company": gossopka_company,
                    "category": gossopka_category,
                    "type": gossopka_type,
                    "activitystatus": gossopka_activitystatus,
                    "assistance": gossopka_assistance,
                    "eventdescription": gossopka_eventdescription,
                    "detectiontool": gossopka_detectiontool,
                    "detecttime": gossopka_detecttime,
                    "endtime": gossopka_endtime,
                    "tlp": gossopka_tlp,
                    "affectedsystemname": gossopka_affectedsystemname,
                    "affectedsystemcategory": gossopka_affectedsystemcategory,
                    "affectedsystemfunction": gossopka_affectedsystemfunction,
                    "affectedsystemconnection": gossopka_affectedsystemconnection,
                    "location": gossopka_location,
                    "city": gossopka_city,
                    "productinfo": product_info_list_of_dicts,
                    "vulnerabilityid": gossopka_vulnerid,
                    "productCategory": gossopka_product_category
                })
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug, message_text=(
                            "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(gossopka_headers).replace(
                        token, "***************************") + " " + str(json.loads(incident_notification)) + "\r\n"))
                else:
                    pass
                gossopka_response = requests.request("POST", gossopka_url,
                                                     headers=gossopka_headers,
                                                     data=incident_notification, verify=False)
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_debug,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                else:
                    pass
                gossopka_response_text = json.loads(gossopka_response.text)
                gossopka_response_status_code = str(gossopka_response.status_code)
            if gossopka_response_status_code == '200' or gossopka_response_status_code == '201':
                gossopka_success_updates += 1
                log_uuid = str(gossopka_response_text['data'][0]['uuid'])
                log_identifier = str(gossopka_response_text['data'][0]['identifier']).replace("INC", prefix)
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_info, message_text=(
                            event_id + " " + "Уведомление об уязвимости успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                elif "INFO" in log_level:
                    connector_logger(file_path=file_path, level=level_info, message_text=(
                            event_id + " " + "Уведомление об уязвимости успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                save_success_notification_to_suib_result = str(
                    save_success_notification_to_suib(event_id=event_id, log_uuid=log_uuid,
                                                      log_identifier=log_identifier,
                                                      incident_notification=incident_notification,
                                                      gossopka_response_text=gossopka_response_text))
                print(save_success_notification_to_suib_result)
                if "прошла успешно" in save_success_notification_to_suib_result:
                    suib_success_updates += 1
                else:
                    suib_failed_updates += 1
            else:
                gossopka_failed_updates += 1
                if log_level == 'DEBUG' or log_level == 'INFO' or log_level == 'WARN':
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            event_id + " " + "Возникла ошибка при передаче уведомления об уязвимости в ГосСОПКА\r\n"))
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                        gossopka_headers).replace(token, "***************************") + " " + str(
                        json.loads(incident_notification)) + "\r\n"))
                    connector_logger(file_path=file_path, level=level_warn,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                save_error_notification_to_suib_result = str(
                    save_error_notification_to_suib(event_id=event_id, incident_notification=incident_notification,
                                                    gossopka_response_text=gossopka_response_text))
                print(save_error_notification_to_suib_result)
                if "прошла успешно" in save_error_notification_to_suib_result:
                    suib_success_updates += 1
                else:
                    suib_failed_updates += 1

        else:
            gossopka_response = requests.request("POST", gossopka_url, headers=gossopka_headers, verify=False)
            if "DEBUG" in log_level:
                connector_logger(file_path=file_path, level=level_warn, message_text=(
                        event_id + " " + "Ошибка передачи уведомления в ГосСОПКА. Поле «Категория уведомления» содержит значение отличное от «Уведомление о компьютерном инциденте», «Уведомление о компьютерной атаке», «Уведомление о наличии уязвимости»\r\n"))
                connector_logger(file_path=file_path, level=level_debug,
                                 message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                connector_logger(file_path=file_path, level=level_info,
                                 message_text=("Завершена обработка уведомлений для добавления в ГосСОПКА\r\n"))
            elif "INFO" in log_level:
                connector_logger(file_path=file_path, level=level_warn, message_text=(
                        event_id + " " + "Ошибка передачи уведомления в ГосСОПКА. Поле «Категория уведомления» содержит значение отличное от «Уведомление о компьютерном инциденте», «Уведомление о компьютерной атаке», «Уведомление о наличии уязвимости»\r\n"))
                connector_logger(file_path=file_path, level=level_info,
                                 message_text=("Завершена обработка уведомлений для добавления в ГосСОПКА\r\n"))
            elif "WARN" in log_level:
                connector_logger(file_path=file_path, level=level_warn, message_text=(
                        event_id + " " + "Ошибка передачи уведомления в ГосСОПКА. Поле «Категория уведомления» содержит значение отличное от «Уведомление о компьютерном инциденте», «Уведомление о компьютерной атаке», «Уведомление о наличии уязвимости»\r\n"))
            else:
                pass

    except requests.exceptions.RequestException as net_error:
        print("ГосСОПКА недоступна: ", net_error)
        if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
            connector_logger(file_path=file_path, level=level_warn,
                             message_text=log_gossopka_test_connect_unavailable)
        time.sleep(error_timeout)
        if log_level == "DEBUG" or log_level == "INFO":
            connector_logger(file_path=file_path, level=level_info,
                             message_text=log_sync_end)
        gossopka_save_error = "Web-сервис ГосСОПКА недоступен"
        return gossopka_save_error
    return gossopka_success_updates, gossopka_failed_updates, suib_success_updates, suib_failed_updates


def save_notifications_to_gossopka(parsed_list):
    file_path = check_folder(log_path=log_path)
    gossopka_url = gossopka_ssl + "://" + gossopka_server_name + ":" + str(gossopka_server_port) + "/api/v2/incidents?"
    gossopka_headers = {
        'accept': 'application/json',
        'x-token': token,
    }
    gossopka_success_updates = 0
    gossopka_failed_updates = 0
    suib_success_updates = 0
    suib_failed_updates = 0
    for i in parsed_list:
        event_id = i['Id']['#text']
        if "DEBUG" in log_level:
            connector_logger(file_path=file_path, level=level_info, message_text=(
                    event_id + " " + "Обработка уведомления для добавления в ГосСОПКА\r\n"))
        elif "INFO" in log_level:
            connector_logger(file_path=file_path, level=level_info, message_text=(
                    event_id + " " + "Обработка уведомления для добавления в ГосСОПКА\r\n"))
        technical_ready = i['GosSOPKATechnicalReady']['#text']
        gossopka_category = i['GosSOPKACategory']['#text']
        gossopka_type = i['GosSOPKAType']['#text']
        if "GosSOPKACompany" in i:
            gossopka_company = i['GosSOPKACompany']['#text']
        else:
            gossopka_company = str(gossopka_organization)
        if "GosSOPKAAssistance" in i:
            gossopka_assistance = i['GosSOPKAAssistance']['#text']
        else:
            gossopka_assistance = ''
        gossopka_tlp = i['GosSOPKATLP']['#text']
        gossopka_detecttime = i['GosSOPKADetectionTime']['#text']
        if "GosSOPKACompletionTime" in i:
            gossopka_endtime = i['GosSOPKACompletionTime']['#text']
        else:
            gossopka_endtime = ''
        gossopka_activitystatus = i['GosSOPKAState']['#text']
        if "GosSOPKADetectedSystem" in i:
            gossopka_detectiontool = i['GosSOPKADetectedSystem']['#text']
        else:
            gossopka_detectiontool = ''
        gossopka_affectedsystemname = i['GosSOPKASystemName']['#text']
        gossopka_affectedsystemcategory = i['GosSOPKASystemOCIIRatingName']['#text']
        gossopka_affectedsystemfunction = i['GosSOPKAScope']['#text']
        if "GosSOPKAInternet" in i:
            gossopka_affectedsystemconnection = i['GosSOPKAInternet']['#text']
        else:
            gossopka_affectedsystemconnection = ''
        gossopka_eventsdescription = i['GosSOPKADescription']
        if isinstance(gossopka_eventsdescription['GosSOPKADescription'], list):
            gossopka_eventdescription = ''
            for events in gossopka_eventsdescription['GosSOPKADescription']:
                gossopka_eventdescription_tolist = events['#text']
                gossopka_eventdescription += gossopka_eventdescription_tolist
                gossopka_eventdescription += '\n'
            gossopka_eventdescription = gossopka_eventdescription[:-1]
        else:
            gossopka_eventdescription = gossopka_eventsdescription['GosSOPKADescription']['#text']
        if "GosSOPKAIntegrityImpact" in i:
            gossopka_integrityimpact = i['GosSOPKAIntegrityImpact']['#text']
        else:
            gossopka_integrityimpact = ''
        if "GosSOPKAAvailabilityImpact" in i:
            gossopka_availabilityimpact = i['GosSOPKAAvailabilityImpact']['#text']
        else:
            gossopka_availabilityimpact = ''
        if "GosSOPKAAvailabilityImpact" in i:
            gossopka_confidentialityimpact = i['GosSOPKAPrivacyImpact']['#text']
        else:
            gossopka_confidentialityimpact = ''
        if "GosSOPKAOtherImpact" in i:
            gossopka_customimpacts = i['GosSOPKAOtherImpact']['GosSOPKAOtherImpact']
            if isinstance(gossopka_customimpacts, list):
                customimpact = ''
                for impacts in gossopka_customimpacts:
                    customimpact_tolist = impacts['#text']
                    customimpact += customimpact_tolist
                    customimpact += '\n'
                gossopka_customimpact = customimpact[:-1]
            else:
                gossopka_customimpact = gossopka_customimpacts['#text']
        else:
            gossopka_customimpact = ''
        gossopka_location = i['GosSOPKARegion']['#text']
        if "GosSOPKACity" in i:
            gossopka_city = i['GosSOPKACity']['#text']
        else:
            gossopka_city = ''
        if "gossopka.products" in i:
            gossopka_products_info = i['gossopka.products']
            gossopka_product_info = gossopka_products_info['gossopka.products']
            if isinstance(gossopka_product_info, list):
                product_info_dict = {}
                product_info_list_of_dicts = []
                for products in gossopka_product_info:
                    if "GosSOPKAProductName" in products:
                        product_name = products['GosSOPKAProductName']['#text']
                    else:
                        product_name = ''
                    if "GosSOPKAProductVersion" in products:
                        product_version = products['GosSOPKAProductVersion']['#text']
                    else:
                        product_version = ''
                    product_info_dict['name'] = product_name
                    product_info_dict['version'] = product_version
                    product_info_list_of_dicts.append(product_info_dict)
                    product_info_dict = {}
            else:
                product_info_dict = {}
                product_info_list_of_dicts = []
                if "GosSOPKAProductName" in gossopka_product_info:
                    product_name = gossopka_product_info['GosSOPKAProductName']['#text']
                else:
                    product_name = ''
                if "GosSOPKAProductVersion" in gossopka_product_info:
                    product_version = gossopka_product_info['GosSOPKAProductVersion']['#text']
                else:
                    product_version = ''
                product_info_dict['name'] = product_name
                product_info_dict['version'] = product_version
                product_info_list_of_dicts.append(product_info_dict)
        else:
            product_info_list_of_dicts = ''
        if "GosSOPKAVulnerId" in i:
            gossopka_vulnerid = i['GosSOPKAVulnerId']['#text']
        else:
            gossopka_vulnerid = ''
        if "GosSOPKAProductCategory" in i:
            gossopka_product_category = i['GosSOPKAProductCategory']['#text']
        else:
            gossopka_product_category = ''
        if "gossopka.injureds.ipv4" in i:
            gossopka_injureds_ipv4 = i['gossopka.injureds.ipv4']
            gossopka_injured_ipv4 = gossopka_injureds_ipv4['gossopka.injureds.ipv4']
            if isinstance(gossopka_injured_ipv4, list):
                injured_ipv4_dict = {}
                injured_ipv4_list_of_dicts = []
                for injureds in gossopka_injured_ipv4:
                    if "GosSOPKAInjuredIPv4" in injureds:
                        injured_ipv4 = injureds['GosSOPKAInjuredIPv4']['#text']
                        injured_ipv4_dict['value'] = injured_ipv4
                        injured_ipv4_list_of_dicts.append(injured_ipv4_dict)
                        injured_ipv4_dict = {}
                    else:
                        injured_ipv4 = ''
                        injured_ipv4_dict = {}
            else:
                injured_ipv4_dict = {}
                injured_ipv4_list_of_dicts = []
                if "GosSOPKAInjuredIPv4" in gossopka_injured_ipv4:
                    injured_ipv4 = gossopka_injured_ipv4['GosSOPKAInjuredIPv4']['#text']
                    injured_ipv4_dict['value'] = injured_ipv4
                    injured_ipv4_list_of_dicts.append(injured_ipv4_dict)
                else:
                    injured_ipv4 = ''
        else:
            injured_ipv4_list_of_dicts = ''
        if "gossopka.injureds.ipv6" in i:
            gossopka_injureds_ipv6 = i['gossopka.injureds.ipv6']
            gossopka_injured_ipv6 = gossopka_injureds_ipv6['gossopka.injureds.ipv6']
            if isinstance(gossopka_injured_ipv6, list):
                injured_ipv6_dict = {}
                injured_ipv6_list_of_dicts = []
                for injureds in gossopka_injured_ipv6:
                    if "GosSOPKAInjuredIPv6" in injureds:
                        injured_ipv6 = injureds['GosSOPKAInjuredIPv6']['#text']
                        injured_ipv6_dict['value'] = injured_ipv6
                        injured_ipv6_list_of_dicts.append(injured_ipv6_dict)
                        injured_ipv6_dict = {}
                    else:
                        injured_ipv6 = ''
                        injured_ipv6_dict = {}
            else:
                injured_ipv6_dict = {}
                injured_ipv6_list_of_dicts = []
                if "GosSOPKAInjuredIPv6" in gossopka_injured_ipv6:
                    injured_ipv6 = gossopka_injured_ipv6['GosSOPKAInjuredIPv6']['#text']
                    injured_ipv6_dict['value'] = injured_ipv6
                    injured_ipv6_list_of_dicts.append(injured_ipv6_dict)
                else:
                    injured_ipv6 = ''
        else:
            injured_ipv6_list_of_dicts = ''
        if "gossopka.injureds.domain" in i:
            gossopka_injureds_domain = i['gossopka.injureds.domain']
            gossopka_injured_domain = gossopka_injureds_domain['gossopka.injureds.domain']
            if isinstance(gossopka_injured_domain, list):
                injured_domain_dict = {}
                injured_domain_list_of_dicts = []
                for injureds in gossopka_injured_domain:
                    if "GosSOPKAInjuredDomain" in injureds:
                        injured_domains = injureds['GosSOPKAInjuredDomain']['#text']
                        injured_domain_dict['value'] = injured_domains
                        injured_domain_list_of_dicts.append(injured_domain_dict)
                        injured_domain_dict = {}
                    else:
                        injured_domains = ''
                        injured_domain_dict = {}
            else:
                injured_domain_dict = {}
                injured_domain_list_of_dicts = []
                if "GosSOPKAInjuredDomain" in gossopka_injured_domain:
                    injured_domains = gossopka_injured_domain['GosSOPKAInjuredDomain']['#text']
                    injured_domain_dict['value'] = injured_domains
                    injured_domain_list_of_dicts.append(injured_domain_dict)
                else:
                    injured_domains = ''
        else:
            injured_domain_list_of_dicts = ''
        if "gossopka.injureds.uri" in i:
            gossopka_injureds_uri = i['gossopka.injureds.uri']
            gossopka_injured_uri = gossopka_injureds_uri['gossopka.injureds.uri']
            if isinstance(gossopka_injured_uri, list):
                injured_uri_dict = {}
                injured_uri_list_of_dicts = []
                for injureds in gossopka_injured_uri:
                    if "GosSOPKAInjuredURI" in injureds:
                        injured_uri = injureds['GosSOPKAInjuredURI']['#text']
                        injured_uri_dict['value'] = injured_uri
                        injured_uri_list_of_dicts.append(injured_uri_dict)
                        injured_uri_dict = {}
                    else:
                        injured_uri = ''
                        injured_uri_dict = {}
            else:
                injured_uri_dict = {}
                injured_uri_list_of_dicts = []
                if "GosSOPKAInjuredURI" in gossopka_injured_uri:
                    injured_uri = gossopka_injured_uri['GosSOPKAInjuredURI']['#text']
                    injured_uri_dict['value'] = injured_uri
                    injured_uri_list_of_dicts.append(injured_uri_dict)
                else:
                    injured_uri = ''
        else:
            injured_uri_list_of_dicts = ''
        if "gossopka.injureds.email" in i:
            gossopka_injureds_email = i['gossopka.injureds.email']
            gossopka_injured_email = gossopka_injureds_email['gossopka.injureds.email']
            if isinstance(gossopka_injured_email, list):
                injured_email_dict = {}
                injured_email_list_of_dicts = []
                for injureds in gossopka_injured_email:
                    if "GosSOPKAInjuredEmail" in injureds:
                        injured_email = injureds['GosSOPKAInjuredEmail']['#text']
                        injured_email_dict['value'] = injured_email
                        injured_email_list_of_dicts.append(injured_email_dict)
                        injured_email_dict = {}
                    else:
                        injured_email = ''
                        injured_email_dict = {}
            else:
                injured_email_dict = {}
                injured_email_list_of_dicts = []
                if "GosSOPKAInjuredEmail" in gossopka_injured_email:
                    injured_email = gossopka_injured_email['GosSOPKAInjuredEmail']['#text']
                    injured_email_dict['value'] = injured_email
                    injured_email_list_of_dicts.append(injured_email_dict)
                else:
                    injured_email = ''
        else:
            injured_email_list_of_dicts = ''
        if "gossopka.injureds.service" in i:
            gossopka_injureds_service = i['gossopka.injureds.service']
            gossopka_injured_service = gossopka_injureds_service['gossopka.injureds.service']
            if isinstance(gossopka_injured_service, list):
                injured_service_port_dict = {}
                injured_service_port_list_of_dicts = []
                for injureds in gossopka_injured_service:
                    if "GosSOPKAInjuredServiceName" in injureds:
                        injured_service = injureds['GosSOPKAInjuredServiceName']['#text']
                    else:
                        injured_service = ''
                    if "GosSOPKAInjuredServicePort" in injureds:
                        injured_port = injureds['GosSOPKAInjuredServicePort']['#text']
                    else:
                        injured_port = ''
                    injured_service_port_dict['name'] = injured_service
                    injured_service_port_dict['value'] = injured_port
                    injured_service_port_list_of_dicts.append(injured_service_port_dict)
                    injured_service_port_dict = {}
            else:
                injured_service_port_dict = {}
                injured_service_port_list_of_dicts = []
                injured_service = gossopka_injured_service['GosSOPKAInjuredServiceName']['#text']
                injured_port = gossopka_injured_service['GosSOPKAInjuredServicePort']['#text']
                injured_service_port_dict['name'] = injured_service
                injured_service_port_dict['value'] = injured_port
                injured_service_port_list_of_dicts.append(injured_service_port_dict)
        else:
            injured_service_port_list_of_dicts = ''
        if "GosSOPKAInjuredsAsPath" in i:
            injured_aspath = i['GosSOPKAInjuredsAsPath']['#text']
        else:
            injured_aspath = ''
        if "gossopka.attackers.ipv4" in i:
            gossopka_attackers_ipv4 = i['gossopka.attackers.ipv4']
            gossopka_attacker_ipv4 = gossopka_attackers_ipv4['gossopka.attackers.ipv4']
            if isinstance(gossopka_attacker_ipv4, list):
                attacker_ipv4_dict = {}
                attacker_ipv4_list_of_dicts = []
                for attackers in gossopka_attacker_ipv4:
                    if "GosSOPKAAttackerIPv4" in attackers:
                        attackers_ipv4 = attackers['GosSOPKAAttackerIPv4']['#text']
                    else:
                        attackers_ipv4 = ''
                    if "GosSOPKAAttackerIPv4Function" in attackers:
                        attackers_ipv4_function = attackers['GosSOPKAAttackerIPv4Function']['#text']
                    else:
                        attackers_ipv4_function = ''
                    if attackers_ipv4 == '':
                        attacker_ipv4_dict = {}
                    else:
                        attacker_ipv4_dict['function'] = attackers_ipv4_function
                        attacker_ipv4_dict['value'] = attackers_ipv4
                        attacker_ipv4_list_of_dicts.append(attacker_ipv4_dict)
                        attacker_ipv4_dict = {}
            else:
                attacker_ipv4_dict = {}
                attacker_ipv4_list_of_dicts = []
                if "GosSOPKAAttackerIPv4" in gossopka_attacker_ipv4:
                    attackers_ipv4 = gossopka_attacker_ipv4['GosSOPKAAttackerIPv4']['#text']
                else:
                    attackers_ipv4 = ''
                if "GosSOPKAAttackerIPv4Function" in gossopka_attacker_ipv4:
                    attackers_ipv4_function = gossopka_attacker_ipv4['GosSOPKAAttackerIPv4Function']['#text']
                else:
                    attackers_ipv4_function = ''
                if attackers_ipv4 == '':
                    pass
                else:
                    attacker_ipv4_dict['function'] = attackers_ipv4_function
                    attacker_ipv4_dict['value'] = attackers_ipv4
                    attacker_ipv4_list_of_dicts.append(attacker_ipv4_dict)
        else:
            attacker_ipv4_list_of_dicts = ''
        if "gossopka.attackers.ipv6" in i:
            gossopka_attackers_ipv6 = i['gossopka.attackers.ipv6']
            gossopka_attacker_ipv6 = gossopka_attackers_ipv6['gossopka.attackers.ipv6']
            if isinstance(gossopka_attacker_ipv6, list):
                attacker_ipv6_dict = {}
                attacker_ipv6_list_of_dicts = []
                for attackers in gossopka_attacker_ipv6:
                    if "GosSOPKAAttackerIPv6" in attackers:
                        attackers_ipv6 = attackers['GosSOPKAAttackerIPv6']['#text']
                    else:
                        attackers_ipv6 = ''
                    if "GosSOPKAAttackerIPv6Function" in attackers:
                        attackers_ipv6_function = attackers['GosSOPKAAttackerIPv6Function']['#text']
                    else:
                        attackers_ipv6_function = ''
                    if attackers_ipv6 == '':
                        attacker_ipv6_dict = {}
                    else:
                        attacker_ipv6_dict['function'] = attackers_ipv6_function
                        attacker_ipv6_dict['value'] = attackers_ipv6
                        attacker_ipv6_list_of_dicts.append(attacker_ipv6_dict)
                        attacker_ipv6_dict = {}
            else:
                attacker_ipv6_dict = {}
                attacker_ipv6_list_of_dicts = []
                if "GosSOPKAAttackerIPv6" in gossopka_attacker_ipv6:
                    attackers_ipv6 = gossopka_attacker_ipv6['GosSOPKAAttackerIPv6']['#text']
                else:
                    attackers_ipv6 = ''
                if "GosSOPKAAttackerIPv6Function" in gossopka_attacker_ipv6:
                    attackers_ipv6_function = gossopka_attacker_ipv6['GosSOPKAAttackerIPv6Function']['#text']
                else:
                    attackers_ipv6_function = ''
                if attackers_ipv6 == '':
                    pass
                else:
                    attacker_ipv6_dict['function'] = attackers_ipv6_function
                    attacker_ipv6_dict['value'] = attackers_ipv6
                    attacker_ipv6_list_of_dicts.append(attacker_ipv6_dict)
        else:
            attacker_ipv6_list_of_dicts = ''
        if "gossopka.attackers.domain" in i:
            gossopka_attackers_domain = i['gossopka.attackers.domain']
            gossopka_attacker_domain = gossopka_attackers_domain['gossopka.attackers.domain']
            if isinstance(gossopka_attacker_domain, list):
                attacker_domain_dict = {}
                attacker_domain_list_of_dicts = []
                for attackers in gossopka_attacker_domain:
                    if "GosSOPKAAttackerDomain" in attackers:
                        attackers_domain = attackers['GosSOPKAAttackerDomain']['#text']
                    else:
                        attackers_domain = ''
                    if "GosSOPKAAttackerDomainFunction" in attackers:
                        attackers_domain_function = attackers['GosSOPKAAttackerDomainFunction'][
                            '#text']
                    else:
                        attackers_domain_function = ''
                    if attackers_domain == '':
                        attacker_domain_dict = {}
                    else:
                        attacker_domain_dict['function'] = attackers_domain_function
                        attacker_domain_dict['value'] = attackers_domain
                        attacker_domain_list_of_dicts.append(attacker_domain_dict)
                        attacker_domain_dict = {}
            else:
                attacker_domain_dict = {}
                attacker_domain_list_of_dicts = []
                if "GosSOPKAAttackerDomain" in gossopka_attacker_domain:
                    attackers_domain = gossopka_attacker_domain['GosSOPKAAttackerDomain']['#text']
                else:
                    attackers_domain = ''
                if "GosSOPKAAttackerDomainFunction" in gossopka_attacker_domain:
                    attackers_domain_function = gossopka_attacker_domain['GosSOPKAAttackerDomainFunction']['#text']
                else:
                    attackers_domain_function = ''
                if attackers_domain == '':
                    pass
                else:
                    attacker_domain_dict['function'] = attackers_domain_function
                    attacker_domain_dict['value'] = attackers_domain
                    attacker_domain_list_of_dicts.append(attacker_domain_dict)
        else:
            attacker_domain_list_of_dicts = ''
        if "gossopka.attackers.uri" in i:
            gossopka_attackers_uri = i['gossopka.attackers.uri']
            gossopka_attacker_uri = gossopka_attackers_uri['gossopka.attackers.uri']
            if isinstance(gossopka_attacker_uri, list):
                attacker_uri_dict = {}
                attacker_uri_list_of_dicts = []
                for attackers in gossopka_attacker_uri:
                    if "GosSOPKAAttackerURI" in attackers:
                        attackers_uri = attackers['GosSOPKAAttackerURI']['#text']
                    else:
                        attackers_uri = ''
                    if "GosSOPKAAttackerURIFunction" in attackers:
                        attackers_uri_function = attackers['GosSOPKAAttackerURIFunction']['#text']
                    else:
                        attackers_uri_function = ''
                    if attackers_uri == '':
                        attacker_uri_dict = {}
                    else:
                        attacker_uri_dict['function'] = attackers_uri_function
                        attacker_uri_dict['value'] = attackers_uri
                        attacker_uri_list_of_dicts.append(attacker_uri_dict)
                        attacker_uri_dict = {}
            else:
                attacker_uri_dict = {}
                attacker_uri_list_of_dicts = []
                if "GosSOPKAAttackerURI" in gossopka_attacker_uri:
                    attackers_uri = gossopka_attacker_uri['GosSOPKAAttackerURI']['#text']
                else:
                    attackers_uri = ''
                if "GosSOPKAAttackerURIFunction" in gossopka_attacker_uri:
                    attackers_uri_function = gossopka_attacker_uri['GosSOPKAAttackerURIFunction']['#text']
                else:
                    attackers_uri_function = ''
                if attackers_uri == '':
                    pass
                else:
                    attacker_uri_dict['function'] = attackers_uri_function
                    attacker_uri_dict['value'] = attackers_uri
                    attacker_uri_list_of_dicts.append(attacker_uri_dict)
        else:
            attacker_uri_list_of_dicts = ''
        if "gossopka.attackers.email" in i:
            gossopka_attackers_email = i['gossopka.attackers.email']
            gossopka_attacker_email = gossopka_attackers_email['gossopka.attackers.email']
            if isinstance(gossopka_attacker_email, list):
                attacker_email_dict = {}
                attacker_email_list_of_dicts = []
                for attackers in gossopka_attacker_email:
                    attackers_email = attackers['GosSOPKAAttackerEmail']['#text']
                    attacker_email_dict['value'] = attackers_email
                    attacker_email_list_of_dicts.append(attacker_email_dict)
                    attacker_email_dict = {}
            else:
                attacker_email_dict = {}
                attacker_email_list_of_dicts = []
                attackers_email = gossopka_attacker_email['GosSOPKAAttackerEmail']['#text']
                attacker_email_dict['value'] = attackers_email
                attacker_email_list_of_dicts.append(attacker_email_dict)
        else:
            attacker_email_list_of_dicts = ''
        if "gossopka.attackers.hash" in i:
            gossopka_attackers_hash = i['gossopka.attackers.hash']
            gossopka_attacker_hash = gossopka_attackers_hash['gossopka.attackers.hash']
            if isinstance(gossopka_attacker_hash, list):
                attacker_hash_dict = {}
                attacker_hash_list_of_dicts = []
                for attackers in gossopka_attacker_hash:
                    attackers_hash = attackers['GosSOPKAAttackerHash']['#text']
                    attacker_hash_dict['value'] = attackers_hash
                    attacker_hash_list_of_dicts.append(attacker_hash_dict)
                    attacker_hash_dict = {}
            else:
                attacker_hash_dict = {}
                attacker_hash_list_of_dicts = []
                attackers_hash = gossopka_attacker_hash['GosSOPKAAttackerHash']['#text']
                attacker_hash_dict['value'] = attackers_hash
                attacker_hash_list_of_dicts.append(attacker_hash_dict)
        else:
            attacker_hash_list_of_dicts = ''
        if "gossopka.attackers.vulner" in i:
            gossopka_attackers_vulner = i['gossopka.attackers.vulner']
            gossopka_attacker_vulner = gossopka_attackers_vulner['gossopka.attackers.vulner']
            if isinstance(gossopka_attacker_vulner, list):
                attacker_vulner_dict = {}
                attacker_vulner_list_of_dicts = []
                for attackers in gossopka_attacker_vulner:
                    attackers_vulner = attackers['GosSOPKAAttackerVulner']['#text']
                    attacker_vulner_dict['value'] = attackers_vulner
                    attacker_vulner_list_of_dicts.append(attacker_vulner_dict)
                    attacker_vulner_dict = {}
            else:
                attacker_vulner_dict = {}
                attacker_vulner_list_of_dicts = []
                attackers_vulner = gossopka_attacker_vulner['GosSOPKAAttackerVulner']['#text']
                attacker_vulner_dict['value'] = attackers_vulner
                attacker_vulner_list_of_dicts.append(attacker_vulner_dict)
        else:
            attacker_vulner_list_of_dicts = ''
        if "GosSOPKAAttackerASN" in i:
            gossopka_attackerasn = i['GosSOPKAAttackerASN']['#text']
        else:
            gossopka_attackerasn = ''
        if "GosSOPKAAttackerAS" in i:
            gossopka_attackeras = i['GosSOPKAAttackerAS']['#text']
        else:
            gossopka_attackeras = ''
        if "GosSOPKAAttackerLIR" in i:
            gossopka_attackerlir = i['GosSOPKAAttackerLIR']['#text']
        else:
            gossopka_attackerlir = ''

        try:

            if "Уведомление о компьютерном инциденте" in gossopka_category:  # уведомление о компьютерном инциденте
                if technical_ready == 'true':
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                event_id + " " + "Добавление уведомления о компьютерном инциденте в ГосСОПКА с техническими сведениями\r\n"))
                    else:
                        pass
                    incident_notification = json.dumps({
                        "company": gossopka_company,
                        "category": gossopka_category,
                        "type": gossopka_type,
                        "activitystatus": gossopka_activitystatus,
                        "assistance": gossopka_assistance,
                        "eventdescription": gossopka_eventdescription,
                        "detectiontool": gossopka_detectiontool,
                        "detecttime": gossopka_detecttime,
                        "endtime": gossopka_endtime,
                        "tlp": gossopka_tlp,
                        "availabilityimpact": gossopka_availabilityimpact,
                        "integrityimpact": gossopka_integrityimpact,
                        "confidentialityimpact": gossopka_confidentialityimpact,
                        "customimpact": gossopka_customimpact,
                        "affectedsystemname": gossopka_affectedsystemname,
                        "affectedsystemcategory": gossopka_affectedsystemcategory,
                        "affectedsystemfunction": gossopka_affectedsystemfunction,
                        "affectedsystemconnection": gossopka_affectedsystemconnection,
                        "location": gossopka_location,
                        "city": gossopka_city,
                        "relatedobservablesipv4": injured_ipv4_list_of_dicts,
                        "relatedobservablesipv6": injured_ipv6_list_of_dicts,
                        "relatedobservablesdomain": injured_domain_list_of_dicts,
                        "relatedobservablesuri": injured_uri_list_of_dicts,
                        "relatedobservablesemail": injured_email_list_of_dicts,
                        "relatedobservablesservice": injured_service_port_list_of_dicts,
                        "relatedobservablesaspath": injured_aspath,
                        "relatedindicatorsipv4": attacker_ipv4_list_of_dicts,
                        "relatedindicatorsipv6": attacker_ipv6_list_of_dicts,
                        "relatedindicatorsdomain": attacker_domain_list_of_dicts,
                        "relatedindicatorsuri": attacker_uri_list_of_dicts,
                        "relatedindicatorsemail": attacker_email_list_of_dicts,
                        "malwarehash": attacker_hash_list_of_dicts,
                        "relatedindicatorsvuln": attacker_vulner_list_of_dicts,
                        "relatedindicatorsasn": gossopka_attackerasn,
                        "relatedindicatorsas": gossopka_attackeras,
                        "relatedindicatorsaslir": gossopka_attackerlir
                    })
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                            gossopka_headers).replace(
                            token, "***************************") + " " + str(
                            json.loads(incident_notification)) + "\r\n"))
                    else:
                        pass
                    gossopka_response = requests.request("POST", gossopka_url,
                                                         headers=gossopka_headers,
                                                         data=incident_notification, verify=False)
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug,
                                         message_text=(
                                                 "Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    else:
                        pass
                    gossopka_response_text = json.loads(gossopka_response.text)
                    gossopka_response_status_code = str(gossopka_response.status_code)
                else:
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                event_id + " " + "Добавление уведомления о компьютерном инциденте в ГосСОПКА без технических сведений\r\n"))
                    else:
                        pass
                    incident_notification = json.dumps({
                        "company": gossopka_company,
                        "category": gossopka_category,
                        "type": gossopka_type,
                        "activitystatus": gossopka_activitystatus,
                        "assistance": gossopka_assistance,
                        "eventdescription": gossopka_eventdescription,
                        "detectiontool": gossopka_detectiontool,
                        "detecttime": gossopka_detecttime,
                        "endtime": gossopka_endtime,
                        "tlp": gossopka_tlp,
                        "availabilityimpact": gossopka_availabilityimpact,
                        "integrityimpact": gossopka_integrityimpact,
                        "confidentialityimpact": gossopka_confidentialityimpact,
                        "customImpact": gossopka_customimpact,
                        "affectedsystemname": gossopka_affectedsystemname,
                        "affectedsystemcategory": gossopka_affectedsystemcategory,
                        "affectedsystemfunction": gossopka_affectedsystemfunction,
                        "affectedsystemconnection": gossopka_affectedsystemconnection,
                        "location": gossopka_location,
                        "city": gossopka_city
                    })
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                            gossopka_headers).replace(
                            token, "***************************") + " " + str(
                            json.loads(incident_notification)) + "\r\n"))
                    else:
                        pass
                    gossopka_response = requests.request("POST", gossopka_url,
                                                         headers=gossopka_headers,
                                                         data=incident_notification, verify=False)
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug,
                                         message_text=(
                                                 "Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    else:
                        pass
                    gossopka_response_text = json.loads(gossopka_response.text)
                    gossopka_response_status_code = str(gossopka_response.status_code)
                if gossopka_response_status_code == "200" or gossopka_response_status_code == "201":
                    gossopka_success_updates += 1
                    log_uuid = str(gossopka_response_text['data'][0]['uuid'])
                    log_identifier = str(gossopka_response_text['data'][0]['identifier']).replace("INC", prefix)
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                event_id + " " + "Уведомление о компьютерном инциденте успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                    elif "INFO" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                event_id + " " + "Уведомление о компьютерном инциденте успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                    save_success_notification_to_suib_result = str(
                        save_success_notification_to_suib(event_id=event_id, log_uuid=log_uuid,
                                                          log_identifier=log_identifier,
                                                          incident_notification=incident_notification,
                                                          gossopka_response_text=gossopka_response_text))
                    print(save_success_notification_to_suib_result)
                    if "прошла успешно" in save_success_notification_to_suib_result:
                        suib_success_updates += 1
                    else:
                        suib_failed_updates += 1
                else:
                    gossopka_failed_updates += 1
                    if log_level == 'DEBUG' or log_level == 'INFO' or log_level == 'WARN':
                        connector_logger(file_path=file_path, level=level_warn, message_text=(
                                event_id + " " + "Возникла ошибка при передаче уведомления о компьютерном инциденте в ГосСОПКА\r\n"))
                        connector_logger(file_path=file_path, level=level_warn, message_text=(
                                "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                            gossopka_headers).replace(token, "***************************") + " " + str(
                            json.loads(incident_notification)) + "\r\n"))
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 "Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    save_error_notification_to_suib_result = str(
                        save_error_notification_to_suib(event_id=event_id, incident_notification=incident_notification,
                                                        gossopka_response_text=gossopka_response_text))
                    print(save_error_notification_to_suib_result)
                    if "прошла успешно" in save_error_notification_to_suib_result:
                        suib_success_updates += 1
                    else:
                        suib_failed_updates += 1

            elif "Уведомление о компьютерной атаке" in gossopka_category:  # уведомление о компьютерной атаке
                if technical_ready == 'true':
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                event_id + " " + "Добавление уведомления о компьютерной атаке в ГосСОПКА с техническими сведениями\r\n"))
                    else:
                        pass
                    incident_notification = json.dumps({
                        "company": gossopka_company,
                        "category": gossopka_category,
                        "type": gossopka_type,
                        "activitystatus": gossopka_activitystatus,
                        "assistance": gossopka_assistance,
                        "eventdescription": gossopka_eventdescription,
                        "detectiontool": gossopka_detectiontool,
                        "detecttime": gossopka_detecttime,
                        "endtime": gossopka_endtime,
                        "tlp": gossopka_tlp,
                        "availabilityimpact": gossopka_availabilityimpact,
                        "integrityimpact": gossopka_integrityimpact,
                        "confidentialityimpact": gossopka_confidentialityimpact,
                        "customimpact": gossopka_customimpact,
                        "affectedsystemname": gossopka_affectedsystemname,
                        "affectedsystemcategory": gossopka_affectedsystemcategory,
                        "affectedsystemfunction": gossopka_affectedsystemfunction,
                        "affectedsystemconnection": gossopka_affectedsystemconnection,
                        "location": gossopka_location,
                        "city": gossopka_city,
                        "relatedobservablesipv4": injured_ipv4_list_of_dicts,
                        "relatedobservablesipv6": injured_ipv6_list_of_dicts,
                        "relatedobservablesdomain": injured_domain_list_of_dicts,
                        "relatedobservablesuri": injured_uri_list_of_dicts,
                        "relatedobservablesemail": injured_email_list_of_dicts,
                        "relatedobservablesservice": injured_service_port_list_of_dicts,
                        "relatedindicatorsipv4": attacker_ipv4_list_of_dicts,
                        "relatedindicatorsipv6": attacker_ipv6_list_of_dicts,
                        "relatedindicatorsdomain": attacker_domain_list_of_dicts,
                        "relatedindicatorsuri": attacker_uri_list_of_dicts,
                        "relatedindicatorsemail": attacker_email_list_of_dicts,
                        "malwarehash": attacker_hash_list_of_dicts,
                        "relatedindicatorsvuln": attacker_vulner_list_of_dicts
                    })
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                            gossopka_headers).replace(
                            token, "***************************") + " " + str(
                            json.loads(incident_notification)) + "\r\n"))
                    else:
                        pass
                    gossopka_response = requests.request("POST", gossopka_url,
                                                         headers=gossopka_headers,
                                                         data=incident_notification, verify=False)
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug,
                                         message_text=(
                                                 "Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    else:
                        pass
                    gossopka_response_text = json.loads(gossopka_response.text)
                    gossopka_response_status_code = str(gossopka_response.status_code)
                else:
                    print("Уведомление о компьютерной атаке без технических данных")
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                event_id + " " + "Добавление уведомления о компьютерной атаке в ГосСОПКА без технических сведений\r\n"))
                    else:
                        pass
                    incident_notification = json.dumps({
                        "company": gossopka_company,
                        "category": gossopka_category,
                        "type": gossopka_type,
                        "activitystatus": gossopka_activitystatus,
                        "assistance": gossopka_assistance,
                        "eventdescription": gossopka_eventdescription,
                        "detectiontool": gossopka_detectiontool,
                        "detecttime": gossopka_detecttime,
                        "endtime": gossopka_endtime,
                        "tlp": gossopka_tlp,
                        "availabilityimpact": gossopka_availabilityimpact,
                        "integrityimpact": gossopka_integrityimpact,
                        "confidentialityimpact": gossopka_confidentialityimpact,
                        "customImpact": gossopka_customimpact,
                        "affectedsystemname": gossopka_affectedsystemname,
                        "affectedsystemcategory": gossopka_affectedsystemcategory,
                        "affectedsystemfunction": gossopka_affectedsystemfunction,
                        "affectedsystemconnection": gossopka_affectedsystemconnection,
                        "location": gossopka_location,
                        "city": gossopka_city
                    })
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                            gossopka_headers).replace(
                            token, "***************************") + " " + str(
                            json.loads(incident_notification)) + "\r\n"))
                    else:
                        pass
                    gossopka_response = requests.request("POST", gossopka_url,
                                                         headers=gossopka_headers,
                                                         data=incident_notification, verify=False)
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug,
                                         message_text=(
                                                 "Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    else:
                        pass
                    gossopka_response_text = json.loads(gossopka_response.text)
                    gossopka_response_status_code = str(gossopka_response.status_code)
                if gossopka_response_status_code == "200" or gossopka_response_status_code == "201":
                    gossopka_success_updates += 1
                    log_uuid = str(gossopka_response_text['data'][0]['uuid'])
                    log_identifier = str(gossopka_response_text['data'][0]['identifier']).replace("INC", prefix)
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                event_id + " " + "Уведомление о компьютерной атаке успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                    elif "INFO" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                event_id + " " + "Уведомление о компьютерной атаке успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                    save_success_notification_to_suib_result = str(
                        save_success_notification_to_suib(event_id=event_id, log_uuid=log_uuid,
                                                          log_identifier=log_identifier,
                                                          incident_notification=incident_notification,
                                                          gossopka_response_text=gossopka_response_text))
                    print(save_success_notification_to_suib_result)
                    if "прошла успешно" in save_success_notification_to_suib_result:
                        suib_success_updates += 1
                    else:
                        suib_failed_updates += 1
                else:
                    gossopka_failed_updates += 1
                    if log_level == 'DEBUG' or log_level == 'INFO' or log_level == 'WARN':
                        connector_logger(file_path=file_path, level=level_warn, message_text=(
                                event_id + " " + "Возникла ошибка при передаче уведомления о компьютерной атаке в ГосСОПКА\r\n"))
                        connector_logger(file_path=file_path, level=level_warn, message_text=(
                                "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                            gossopka_headers).replace(token, "***************************") + " " + str(
                            json.loads(incident_notification)) + "\r\n"))
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 "Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    save_error_notification_to_suib_result = str(
                        save_error_notification_to_suib(event_id=event_id,
                                                        incident_notification=incident_notification,
                                                        gossopka_response_text=gossopka_response_text))
                    print(save_error_notification_to_suib_result)
                    if "прошла успешно" in save_error_notification_to_suib_result:
                        suib_success_updates += 1
                    else:
                        suib_failed_updates += 1

            elif "Уведомление о наличии уязвимости" in gossopka_category:  # уведомление о наличии уязвимости
                if technical_ready == 'true':
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                event_id + " " + "Добавление уведомления по уязвимости в ГосСОПКА с техническими сведениями\r\n"))
                    else:
                        pass
                    incident_notification = json.dumps({
                        "company": gossopka_company,
                        "category": gossopka_category,
                        "type": gossopka_type,
                        "activitystatus": gossopka_activitystatus,
                        "assistance": gossopka_assistance,
                        "eventdescription": gossopka_eventdescription,
                        "detectiontool": gossopka_detectiontool,
                        "detecttime": gossopka_detecttime,
                        "endtime": gossopka_endtime,
                        "tlp": gossopka_tlp,
                        "affectedsystemname": gossopka_affectedsystemname,
                        "affectedsystemcategory": gossopka_affectedsystemcategory,
                        "affectedsystemfunction": gossopka_affectedsystemfunction,
                        "affectedsystemconnection": gossopka_affectedsystemconnection,
                        "location": gossopka_location,
                        "city": gossopka_city,
                        "relatedobservablesipv4": injured_ipv4_list_of_dicts,
                        "relatedobservablesipv6": injured_ipv6_list_of_dicts,
                        "relatedobservablesdomain": injured_domain_list_of_dicts,
                        "relatedobservablesuri": injured_uri_list_of_dicts,
                        "relatedobservablesservice": injured_service_port_list_of_dicts,
                        "productinfo": product_info_list_of_dicts,
                        "vulnerabilityid": gossopka_vulnerid,
                        "productCategory": gossopka_product_category
                    })
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                            gossopka_headers).replace(
                            token, "***************************") + " " + str(
                            json.loads(incident_notification)) + "\r\n"))
                    else:
                        pass
                    gossopka_response = requests.request("POST", gossopka_url,
                                                         headers=gossopka_headers,
                                                         data=incident_notification, verify=False)
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug,
                                         message_text=(
                                                 "Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    else:
                        pass
                    gossopka_response_text = json.loads(gossopka_response.text)
                    gossopka_response_status_code = str(gossopka_response.status_code)
                else:
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                event_id + " " + "Добавление уведомления по уязвимости в ГосСОПКА без технических сведений\r\n"))
                    else:
                        pass
                    incident_notification = json.dumps({
                        "company": gossopka_company,
                        "category": gossopka_category,
                        "type": gossopka_type,
                        "activitystatus": gossopka_activitystatus,
                        "assistance": gossopka_assistance,
                        "eventdescription": gossopka_eventdescription,
                        "detectiontool": gossopka_detectiontool,
                        "detecttime": gossopka_detecttime,
                        "endtime": gossopka_endtime,
                        "tlp": gossopka_tlp,
                        "affectedsystemname": gossopka_affectedsystemname,
                        "affectedsystemcategory": gossopka_affectedsystemcategory,
                        "affectedsystemfunction": gossopka_affectedsystemfunction,
                        "affectedsystemconnection": gossopka_affectedsystemconnection,
                        "location": gossopka_location,
                        "city": gossopka_city,
                        "productinfo": product_info_list_of_dicts,
                        "vulnerabilityid": gossopka_vulnerid,
                        "productCategory": gossopka_product_category
                    })
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug, message_text=(
                                "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                            gossopka_headers).replace(
                            token, "***************************") + " " + str(
                            json.loads(incident_notification)) + "\r\n"))
                    else:
                        pass
                    gossopka_response = requests.request("POST", gossopka_url,
                                                         headers=gossopka_headers,
                                                         data=incident_notification, verify=False)
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_debug,
                                         message_text=(
                                                 "Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    else:
                        pass
                    gossopka_response_text = json.loads(gossopka_response.text)
                    gossopka_response_status_code = str(gossopka_response.status_code)
                if gossopka_response_status_code == "200" or gossopka_response_status_code == "201":
                    gossopka_success_updates += 1
                    log_uuid = str(gossopka_response_text['data'][0]['uuid'])
                    log_identifier = str(gossopka_response_text['data'][0]['identifier']).replace("INC", prefix)
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                event_id + " " + "Уведомление об уязвимости успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                    elif "INFO" in log_level:
                        connector_logger(file_path=file_path, level=level_info, message_text=(
                                event_id + " " + "Уведомление об уязвимости успешно передано в ГосСОПКА. Рег.номер уведомления - " + log_identifier + ", Код уведомления ГосСОПКА - " + log_uuid + "\r\n"))
                    save_success_notification_to_suib_result = str(
                        save_success_notification_to_suib(event_id=event_id, log_uuid=log_uuid,
                                                          log_identifier=log_identifier,
                                                          incident_notification=incident_notification,
                                                          gossopka_response_text=gossopka_response_text))
                    print(save_success_notification_to_suib_result)
                    if "прошла успешно" in save_success_notification_to_suib_result:
                        suib_success_updates += 1
                    else:
                        suib_failed_updates += 1
                else:
                    gossopka_failed_updates += 1
                    if log_level == 'DEBUG' or log_level == 'INFO' or log_level == 'WARN':
                        connector_logger(file_path=file_path, level=level_warn, message_text=(
                                event_id + " " + "Возникла ошибка при передаче уведомления об уязвимости в ГосСОПКА\r\n"))
                        connector_logger(file_path=file_path, level=level_warn, message_text=(
                                "Запрос в ГосСОПКА: " + "POST" + " " + str(gossopka_url) + str(
                            gossopka_headers).replace(token, "***************************") + " " + str(
                            json.loads(incident_notification)) + "\r\n"))
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 "Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    save_error_notification_to_suib_result = str(
                        save_error_notification_to_suib(event_id=event_id,
                                                        incident_notification=incident_notification,
                                                        gossopka_response_text=gossopka_response_text))
                    print(save_error_notification_to_suib_result)
                    if "прошла успешно" in save_error_notification_to_suib_result:
                        suib_success_updates += 1
                    else:
                        suib_failed_updates += 1
            else:
                if "DEBUG" in log_level:
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            event_id + " " + "Ошибка передачи уведомления в ГосСОПКА. Поле «Категория уведомления» содержит значение отличное от «Уведомление о компьютерном инциденте», «Уведомление о компьютерной атаке», «Уведомление о наличии уязвимости»\r\n"))
                    connector_logger(file_path=file_path, level=level_debug,
                                     message_text=("Ответ от ГосСОПКА:" + " " + str(gossopka_response.text) + "\r\n"))
                    connector_logger(file_path=file_path, level=level_info,
                                     message_text=("Завершена обработка уведомлений для добавления в ГосСОПКА\r\n"))
                elif "INFO" in log_level:
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            event_id + " " + "Ошибка передачи уведомления в ГосСОПКА. Поле «Категория уведомления» содержит значение отличное от «Уведомление о компьютерном инциденте», «Уведомление о компьютерной атаке», «Уведомление о наличии уязвимости»\r\n"))
                    connector_logger(file_path=file_path, level=level_info,
                                     message_text=("Завершена обработка уведомлений для добавления в ГосСОПКА\r\n"))
                elif "WARN" in log_level:
                    connector_logger(file_path=file_path, level=level_warn, message_text=(
                            event_id + " " + "Ошибка передачи уведомления в ГосСОПКА. Поле «Категория уведомления» содержит значение отличное от «Уведомление о компьютерном инциденте», «Уведомление о компьютерной атаке», «Уведомление о наличии уязвимости»\r\n"))
                else:
                    pass

        except requests.exceptions.RequestException as net_error:
            print("ГосСОПКА недоступна: ", net_error)
            if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
                connector_logger(file_path=file_path, level=level_warn,
                                 message_text=log_gossopka_test_connect_unavailable)
            time.sleep(error_timeout)
            if log_level == "DEBUG" or log_level == "INFO":
                connector_logger(file_path=file_path, level=level_info,
                                 message_text=log_sync_end)
            gossopka_save_error = "Web-сервис ГосСОПКА недоступен"
            return gossopka_save_error
    return gossopka_success_updates, gossopka_failed_updates, suib_success_updates, suib_failed_updates


# 6.5 Запись в СУИБ успешного добавления уведомлений в ГосСОПКА
def save_success_notification_to_suib(event_id, log_uuid, log_identifier, incident_notification,
                                      gossopka_response_text):
    file_path = check_folder(log_path=log_path)
    gossopka_url = gossopka_ssl + "://" + gossopka_server_name + ":" + str(gossopka_server_port) + "/api/v2/incidents?"
    if "DEBUG" in log_level:
        connector_logger(file_path=file_path, level=level_debug,
                         message_text=(event_id + " " + "Запись в СУИБ успешного добавления в ГосСОПКА\r\n"))
    update_event_id = event_id
    update_uuid = log_uuid
    update_identifier = log_identifier
    update_url = gossopka_url
    update_datetime = str(datetime.today().strftime('%Y-%m-%dT%H:%M:%S')) + delta_timezone
    update_data1 = str(json.loads(incident_notification))
    update_data2 = str(gossopka_response_text)
    suib_url = suib_ssl + "://" + suib_server_name + ":" + str(suib_server_port) + "/SM/7/ws"
    suib_headers = {
        'SOAPAction': '"Update"',
        'Connection': 'Close',
        'Content-Type': 'text/xml;charset=UTF-8',
        'Authorization': 'Basic ' + base64_auth_header
    }
    suib_payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://schemas.hp.com/SM/7\" xmlns:com=\"http://schemas.hp.com/SM/7/Common\" xmlns:xm=\"http://www.w3.org/2005/05/xmlmime\">\r\n   <soapenv:Header/>\r\n   <soapenv:Body>\r\n      <ns:UpdateIncidentNotifyRequest ignoreEmptyElements=\"false\">\r\n         <ns:model>\r\n            <ns:keys>\r\n               <ns:id type=\"String\">" + update_event_id + "</ns:id>\r\n            </ns:keys>\r\n            <ns:instance>\r\n               <ns:GosSOPKASync type=\"Boolean\">true</ns:GosSOPKASync>\r\n               <ns:GosSOPKASyncError type=\"Array\"/>\r\n               <ns:GosSOPKAId type=\"String\">" + update_uuid + "</ns:GosSOPKAId>\r\n               <ns:GosSOPKASyncStatus type=\"String\">Завершено успешно</ns:GosSOPKASyncStatus>\r\n               <ns:GosSOPKASyncDate type=\"DateTime\">" + update_datetime + "</ns:GosSOPKASyncDate>\r\n               <ns:GosSOPKASyncData type=\"Array\">\r\n                  <ns:GosSOPKASyncData type=\"String\">\r\nPOST " + update_url + "\r\n" + update_data1 + "\r\n                  </ns:GosSOPKASyncData>\r\n               </ns:GosSOPKASyncData>\r\n               <ns:GosSOPKAIncidentId type=\"String\">" + update_identifier + "</ns:GosSOPKAIncidentId>\r\n               <ns:GosSOPKAReady type=\"Boolean\">false</ns:GosSOPKAReady>\r\n               <ns:GosSOPKAGetDate type=\"DateTime\">" + update_datetime + "</ns:GosSOPKAGetDate>\r\n               <ns:GosSOPKAGetData type=\"Array\">\r\n                  <ns:GosSOPKAGetData type=\"String\">\r\n{\r\n  \"value\": " + update_data2 + "}\r\n                  </ns:GosSOPKAGetData>\r\n               </ns:GosSOPKAGetData>\r\n            </ns:instance>\r\n         </ns:model>\r\n      </ns:UpdateIncidentNotifyRequest>\r\n   </soapenv:Body>\r\n</soapenv:Envelope>\r\n"
    attempts = 0  # Счетчик ошибок
    while attempts < max_tries:
        print("Попытка записи в СУИБ успешного добавления уведомления ГосСОПКА ")
        try:
            if "DEBUG" in log_level:
                connector_logger(file_path=file_path, level=level_debug, message_text=(
                        "Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(suib_headers).replace(
                    base64_auth_header,
                    "********************") + " " + str(
                    suib_payload.replace("\r\n", "")) + "\r\n"))
            else:
                pass
            suib_response = requests.request("POST", suib_url, headers=suib_headers, data=suib_payload.encode("utf-8"),
                                             timeout=suib_conn_timeout)
            if "DEBUG" in log_level:
                connector_logger(file_path=file_path, level=level_debug,
                                 message_text=("Ответ от СУИБ: " + str(suib_response.text) + "\r\n"))
            else:
                pass
            if "200" in str(suib_response.status_code):
                parsed_text = xmltodict.parse(suib_response.text, encoding='utf-8',
                                              namespace_separator=":")
                suib_update_response_code = \
                    parsed_text['SOAP-ENV:Envelope']['SOAP-ENV:Body']['UpdateIncidentNotifyResponse'][
                        '@returnCode']
                suib_update_response_status = \
                    parsed_text['SOAP-ENV:Envelope']['SOAP-ENV:Body']['UpdateIncidentNotifyResponse']['@status']
                if suib_update_response_code == '0':
                    if log_level == "DEBUG" or log_level == "INFO":
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text=(
                                                 event_id + " " + "Запись в СУИБ успешного добавления в ГосСОПКА прошла успешно\r\n"))
                    suib_event_success = str("Запись " + event_id + " в СУИБ прошла успешно")
                    return suib_event_success
                elif suib_update_response_code == '51':
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ успешного добавления уведомления в ГосСОПКА. Обновляемая запись была изменена\r\n"))
                    elif "INFO" in log_level:
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ успешного добавления уведомления в ГосСОПКА. Обновляемая запись была изменена\r\n"))
                    elif "WARN" in log_level:
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ успешного добавления уведомления в ГосСОПКА. Обновляемая запись была изменена\r\n"))
                    attempts += 1
                    time.sleep(error_timeout)
                elif suib_update_response_code == '9':
                    if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN" or log_level == "ERROR":
                        connector_logger(file_path=file_path, level=level_error,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ успешного добавления уведомления "
                                                                  "в ГосСОПКА. В СУИБ отсутствует объект для записи\r\n"))
                        connector_logger(file_path=file_path, level=level_error,
                                         message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                             suib_headers).replace(base64_auth_header,
                                                                   "********************") + " " + str(
                                             suib_payload.replace("\r\n", "")) + "\r\n"))

                        connector_logger(file_path=file_path, level=level_error,
                                         message_text=("Ответ от СУИБ: " + str(suib_response.text) + "\r\n"))
                    time.sleep(error_timeout)
                    suib_event_null = str("в СУИБ отсутствует объект " + event_id + " для записи")
                    return suib_event_null
                else:
                    if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ успешного добавления уведомления "
                                                                  "в ГосСОПКА\r\n"))
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                             suib_headers).replace(base64_auth_header,
                                                                   "********************") + " " + str(
                                             suib_payload.replace("\r\n", "")) + "\r\n"))

                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=("Ответ от СУИБ: " + str(suib_response.text) + "\r\n"))
                        attempts += 1
                        time.sleep(error_timeout)

            else:
                pass
        except requests.exceptions.RequestException as error:
            print("Web-сервис СУИБ недоступен: " + str(error))
            if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
                connector_logger(file_path=file_path, level=level_warn, message_text=log_suib_test_connect_unavailable)
            attempts += 1
            time.sleep(error_timeout)
    if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN" or log_level == "ERROR":
        connector_logger(file_path=file_path, level=level_error,
                         message_text=(
                                 event_id + " " + "Ошибка записи в СУИБ успешного добавления уведомления "
                                                  "в ГосСОПКА. В СУИБ отсутствует объект для записи\r\n"))
        connector_logger(file_path=file_path, level=level_error,
                         message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(suib_headers).replace(
                             base64_auth_header, "********************") + " " + str(
                             suib_payload.replace("\r\n", "")) + "\r\n"))

        connector_logger(file_path=file_path, level=level_error,
                         message_text=("Ответ от СУИБ: " + str(suib_response.text) + "\r\n"))
    time.sleep(error_timeout)
    suib_event_error = str(
        "Переход к обработке следующего уведомления после " + max_tries + " неудачных попыток записи в СУИБ")
    return suib_event_error


# 6.6 Запись в СУИБ ошибок добавления уведомлений в ГосСОПКА
def save_error_notification_to_suib(event_id, incident_notification, gossopka_response_text):
    file_path = check_folder(log_path=log_path)
    gossopka_url = gossopka_ssl + "://" + gossopka_server_name + ":" + str(gossopka_server_port) + "/api/v2/incidents?"
    if "DEBUG" in log_level:
        connector_logger(file_path=file_path, level=level_debug,
                         message_text=(event_id + " " + "Запись в СУИБ ошибки добавления уведомления в ГосСОПКА\r\n"))
    update_event_id = event_id
    update_url = gossopka_url
    update_datetime = str(datetime.today().strftime('%Y-%m-%dT%H:%M:%S')) + delta_timezone
    update_data1 = str(json.loads(incident_notification))
    update_data2 = str(gossopka_response_text)
    suib_url = suib_ssl + "://" + suib_server_name + ":" + str(suib_server_port) + "/SM/7/ws"
    suib_headers_error = {
        'SOAPAction': '"Update"',
        'Connection': 'Close',
        'Content-Type': 'text/xml;charset=UTF-8',
        'Authorization': 'Basic ' + base64_auth_header
    }
    suib_payload_error = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://schemas.hp.com/SM/7\" xmlns:com=\"http://schemas.hp.com/SM/7/Common\" xmlns:xm=\"http://www.w3.org/2005/05/xmlmime\">\r\n   <soapenv:Header/>\r\n   <soapenv:Body>\r\n      <ns:UpdateIncidentNotifyRequest ignoreEmptyElements=\"false\">\r\n         <ns:model>\r\n            <ns:keys>\r\n               <ns:id type=\"String\">" + update_event_id + "</ns:id>\r\n            </ns:keys>\r\n            <ns:instance>\r\n               <ns:GosSOPKASync type=\"Boolean\">false</ns:GosSOPKASync>\r\n               <ns:GosSOPKASyncError type=\"Array\">\r\n                  <ns:GosSOPKASyncError>\r\nОшибка добавления уведомления в ГосСОПКА\r\n{\r\n  \"value\": " + update_data2 + "\r\n}\r\n                  </ns:GosSOPKASyncError>\r\n               </ns:GosSOPKASyncError>\r\n               <ns:GosSOPKAId type=\"String\"/>\r\n               <ns:GosSOPKASyncStatus type=\"String\">Завершено с ошибкой</ns:GosSOPKASyncStatus>\r\n               <ns:GosSOPKASyncDate type=\"DateTime\">" + update_datetime + "</ns:GosSOPKASyncDate>\r\n               <ns:GosSOPKASyncData type=\"Array\">\r\n                  <ns:GosSOPKASyncData type=\"String\">\r\nPOST " + update_url + "\r\n" + update_data1 + "\r\n                  </ns:GosSOPKASyncData>\r\n               </ns:GosSOPKASyncData>\r\n               <ns:GosSOPKAIncidentId type=\"String\"/>\r\n               <ns:GosSOPKAReady type=\"Boolean\">false</ns:GosSOPKAReady>\r\n            </ns:instance>\r\n         </ns:model>\r\n      </ns:UpdateIncidentNotifyRequest>\r\n   </soapenv:Body>\r\n</soapenv:Envelope>\r\n"
    attempts = 0  # Счетчик ошибок
    while attempts < max_tries:
        print("Попытка записи в СУИБ ошибки добавления уведомления в ГосСОПКА ")
        try:
            if "DEBUG" in log_level:
                connector_logger(file_path=file_path, level=level_debug, message_text=(
                        "Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(suib_headers_error).replace(
                    base64_auth_header,
                    "********************") + " " + str(
                    suib_payload_error.replace("\r\n", "")) + "\r\n"))
            else:
                pass
            suib_response = requests.request("POST", suib_url, headers=suib_headers_error,
                                             data=suib_payload_error.encode("utf-8"), timeout=suib_conn_timeout)
            if "DEBUG" in log_level:
                connector_logger(file_path=file_path, level=level_debug,
                                 message_text=("Ответ от СУИБ: " + str(suib_response.text) + "\r\n"))
            else:
                pass
            if "200" in str(suib_response.status_code):
                parsed_text = xmltodict.parse(suib_response.text, encoding='utf-8',
                                              namespace_separator=":")
                suib_update_response_code = \
                    parsed_text['SOAP-ENV:Envelope']['SOAP-ENV:Body']['UpdateIncidentNotifyResponse'][
                        '@returnCode']
                suib_update_response_status = \
                    parsed_text['SOAP-ENV:Envelope']['SOAP-ENV:Body']['UpdateIncidentNotifyResponse']['@status']
                if suib_update_response_code == '0':
                    if log_level == "DEBUG" or log_level == "INFO":
                        connector_logger(file_path=file_path, level=level_info,
                                         message_text=(
                                                 event_id + " " + "Запись в СУИБ ошибки добавления уведомления в "
                                                                  "ГосСОПКА прошла успешно\r\n"))
                    suib_event_success = str("Запись " + event_id + "в СУИБ ошибки добавления уведомления в ГосСОПКА "
                                                                    "прошла успешно")
                    return suib_event_success
                elif suib_update_response_code == '51':
                    if "DEBUG" in log_level:
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ ошибки добавления уведомления в ГосСОПКА. Обновляемая запись была изменена\r\n"))
                    elif "INFO" in log_level:
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ ошибки добавления уведомления в ГосСОПКА. Обновляемая запись была изменена\r\n"))
                    elif "WARN" in log_level:
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ ошибки добавления уведомления в ГосСОПКА. Обновляемая запись была изменена\r\n"))
                    attempts += 1
                    time.sleep(error_timeout)
                elif suib_update_response_code == '9':
                    if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN" or log_level == "ERROR":
                        connector_logger(file_path=file_path, level=level_error,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ ошибки добавления уведомления в ГосСОПКА. В СУИБ отсутствует объект для записи\r\n"))
                        connector_logger(file_path=file_path, level=level_error,
                                         message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                             suib_headers_error).replace(base64_auth_header,
                                                                         "********************") + " " + str(
                                             suib_payload_error.replace("\r\n", "")) + "\r\n"))

                        connector_logger(file_path=file_path, level=level_error,
                                         message_text=("Ответ от СУИБ: " + str(suib_response.text) + "\r\n"))
                    time.sleep(error_timeout)
                    suib_event_null = str("в СУИБ отсутствует объект " + event_id + " для записи ошибки")
                    return suib_event_null
                else:
                    if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=(
                                                 event_id + " " + "Ошибка записи в СУИБ ошибки добавления уведомления в ГосСОПКА\r\n"))
                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=("Запрос в СУИБ: " + "POST" + " " + suib_url + " " + str(
                                             suib_headers_error).replace(base64_auth_header,
                                                                         "********************") + " " + str(
                                             suib_payload_error.replace("\r\n", "")) + "\r\n"))

                        connector_logger(file_path=file_path, level=level_warn,
                                         message_text=("Ответ от СУИБ: " + str(suib_response.text) + "\r\n"))
                        attempts += 1
                        time.sleep(error_timeout)

            else:
                pass
        except requests.exceptions.RequestException as error:
            print("Web-сервис СУИБ недоступен: " + str(error))
            if log_level == "DEBUG" or log_level == "INFO" or log_level == "WARN":
                connector_logger(file_path=file_path, level=level_warn, message_text=log_suib_test_connect_unavailable)
            attempts += 1
            time.sleep(error_timeout)


run_connector()
