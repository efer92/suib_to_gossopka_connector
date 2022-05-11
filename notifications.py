from datetime import datetime

level_debug = "DEBUG"
level_info = "INFO"
level_warn = "WARN"
level_error = "ERROR"
level_fatal = "FATAL"

log_module_start = "***НАЧАЛО РАБОТЫ ИНТЕГРАЦИОННОГО МОДУЛЯ МЕЖДУ ГОССОПКА И СУИБ***\r\n"
log_module_end = "***ОКОНЧАНИЕ РАБОТЫ ИНТЕГРАЦИОННОГО МОДУЛЯ МЕЖДУ ГОССОПКА И СУИБ***\r\n"
log_sync_start = "==НАЧАЛО СИНХРОНИЗАЦИИ ДАННЫХ МЕЖДУ ГОССОПКА И СУИБ==\r\n"
log_sync_end = "==ОКОНЧАНИЕ СИНХРОНИЗАЦИИ ДАННЫХ МЕЖДУ ГОССОПКА И СУИБ==\r\n"
log_notifications_add = "~~Добавление новых уведомлений в ГосСОПКА~~\r\n"
log_gossopka_test_connect = "Проверка возможности подключения к ГосСОПКА\r\n"
log_gossopka_test_connect_error = "Ошибка подключения к ГосСОПКА\r\n"
log_gossopka_test_connect_success = "Выполнено успешное подключение к ГосСОПКА\r\n"
log_gossopka_test_connect_credentials_error = "Указаны неверные учетные данные для авторизации в ГосСОПКА\r\n"
log_gossopka_test_connect_unavailable = "Web-сервис ГОССОПКА недоступен\r\n"
log_suib_test_connect = "Проверка возможности подключения к СУИБ\r\n"
log_suib_test_connect_unavailable = "Web-сервис СУИБ недоступен\r\n"
log_suib_test_connect_success = "Выполнено успешное подключение к СУИБ\r\n"
log_suib_test_connect_error = "Ошибка подключения к СУИБ\r\n"
log_suib_test_connect_failure = "Получен статус FAILURE при выполнении запроса в СУИБ\r\n"
log_suib_session_limit_user = "В СУИБ использованы все доступные подключения (достигнут предел сессий) пользователя\r\n"
log_suib_session_limit_server = "В СУИБ использованы все доступные подключения (достигнут предел сессий) сервера\r\n"
log_suib_test_connect_critical = "Возникла критическая ошибка при выполнении запроса в СУИБ\r\n"
log_suib_get_notifications = "Получение новых уведомлений из СУИБ для добавления в ГосСОПКА\r\n"
log_suib_null_notifications = "В СУИБ не найдено уведомлений для передачи в ГосСОПКА\r\n"
log_suib_get_notifications_error = "Возникла ошибка при поиске уведомлений в СУИБ для добавления в ГосСОПКА\r\n"
log_suib_notifications_success = "Завершена обработка уведомлений для добавления в ГосСОПКА\r\n"


def connector_logger(file_path, level, message_text):
    log_date = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    file = open(file_path, "a")
    file.write(log_date + " " + "|" + " " + level + " " + "|" + " " + message_text)
    file.close()
