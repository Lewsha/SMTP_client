import socket
import ssl
import base64
import argparse
import random
import os
import string


"""СПРАВКА ПО КОДАМ ОТВЕТОВ СЕРВЕРА
Первая цифра сообщает о результате запроса:

2.*.* - Операция успешно завершена и можно посылать следующую команду
3.*.* - Промежуточный ответ, означающий что команда была принята SMTP сервером, но пока не исполнена и 
сервер ожидает дополнительной информации. В ответ на это клиенту следует передать команду, содержащую 
требуемую информацию. Обычно такой ответ можно получить на команду с последовательным выполнением, 
например DATA
4.*.* - Отказ. Сообщение о временных проблемах. Команда не принята, операция не выполнена, 
однако сервер считает, что причина, по которой команда не выполнена, временная, и клиент может 
повторить операцию позднее. Понятие временная растяжимое и точно нигде не определено, обычно 
время повторной попытки зависит от настройки отправляющей команду стороны. Ответы подобного типа 
применяются, например, при фильтрации спама при помощи так называемых "серых списков", 
когда сервер отказывается принимать письмо, отправляя в первый раз ответ о временной ошибке. 
Если в роли клиента выступает правильно настроенный сервер пересылки, то он повторит отправку,
 и письмо будет пропущено.
5.*.* - Отказ. Сообщение о том что команда не принята, операция не выполнена.

Вторая цифра ответа показывает нам категорию ошибки:
*.0.* - Синтаксическая ошибка. Команда некорректна.
*.1.* - Отклик на запрос информации (например, справка или состояние).
*.2.* - Отклики, относящиеся к каналу передачи.
*.3.* - Не задан.
*.4.* - Не задан.
*.5.* - Отклики показывают состояние принимающей почтовой системы по отношению к запрошенной 
передаче или другим действиям почтовой системы.

 Третья цифра позвляет дополнительно уточнить информацию по каждому ответу. 
 Текстовая часть сообщения не стандартизирована, но обычно несет в себе полезную для 
 понимания причин случившегося информацию.
 
Собственно сам список возможных откликов:
211- Состояние системы или системная справка.
214 - Информация о том, как работать с сервером, описание нестандартных команд и т.д.
220 - Служба готова к работе.
221 - Служба закрывает канал передачи данных.
235 - Успешная аутентификация на сервере.
250 - Выполнение почтовой команды успешно окончено.
251 - Нелокальный пользователь.
252 - Невозможно проверить наличие почтового ящика для пользователя, но сообщение принято, 
и сервер попытается его доставить.
354 - Начало приема сообщения. Сообщение должно заканчиваться точкой на новой строке и новой строкой.
421 - Работа с сервером невозможна. Произойдет закрытие канала связи (может быть ответом на любую 
команду, если серверу нужно закрыть соединение).
450 - Запрошенная команда не принята – недоступен почтовый ящик (почтовый ящик временно занят) .
451 - Запрошенная команда прервана – локальная ошибка при обработке команды.
452 - Запрошенная команда невозможна – недостаточно дискового пространства.
454 - Аутентификация невозможна по причине временного сбоя сервера.
455 - Сервер не может принять параметры.
500 - Синтаксическая ошибка, команда не распознана (также этот отклик может означать, что длина 
команды слишком большая).
501 - Синтаксическая ошибка в команде или аргументе.
502 - Команда распознана, но её реализация сервером не поддерживается.
503 - Неверная последовательность команд.
504 - Параметр команды сервером не поддерживается.
530 - Сервер требует аутентификации для выполнения запрошенной команды.
534 - Данный отклик означает, что выбранный механизм аутентификации для данного пользователя 
является не достаточно надежным.
535 - Аутентификация отклонена сервером (например, ошибка в кодировании данных).
538 - Выбранный метод аутентификации возможен только при зашифрованном канале связи.
550 - Запрошенная операция невозможна – почтовый ящик недоступен (почтовый ящик не найден 
или нет доступа; команда отклонена локальной политикой безопасности).
551 - Нелокальный пользователь.
552 - Запрошенная почтовая команда прервана – превышено выделенное на сервере пространство.
553 - Запрошенная почтовая команда прервана – недопустимое имя почтового ящика (возможно 
синтаксическая ошибка в имени).
554 - Неудачная транзакция или отсутствие SMTP сервиса (при открытии сеанса передачи данных).
555 - Параметры команды MAIL FROM или RCPT TO не удалось распознать или их поддержка не реализована."""


HOST = 'smtp.yandex.ru'  # адрес почтового сервера яндекс
PORT_SSL = 465  # защищенный порт smtp.yandex.ru (по стандарту - 587)
TXT = False  # флаг, находится ли письмо в файле LETTER.txt, или оно будет вводиться прямо в консоли
TIMEOUT = 10  # таймаут
CLIENT_NAME = 'smtpclient'  # имя, которым наш клиент представится серверу
BOUNDARY_ALPHABET = string.ascii_letters + string.digits  # алфивит для разделителя между
# разными типами контента письма
BOUNDARY_LEN = 20  # длина разделителя
with open('CONFIGS/HEADER_FORMAT', 'r') as format_file:
    HEADER_FORMAT = format_file.read()  # Считываем формат заголовка
with open('CONFIGS/ATTACHMENT_FORMAT', 'r') as format_file:
    ATTACHMENT_FORMAT = format_file.read()  # Считываем формат для вложений
with open('CONFIGS/TERMINAL_FORMAT', 'r') as format_file:
    TERMINAL_FORMAT = format_file.read()  # Считываем формат концовочки письмеца


def send(channel, message):
    """Метод для отправки наших сообщений серверу"""
    channel.write(message + '\n')  # это посылка (channel - это файло-подобный объект, по факту - наш сокет)
    channel.flush()  # очищаем буфер


def recv(channel):
    """Метод для приема ответов от сервера"""
    """В наш файло-подобный объект будет что-то записано, 
    пока можем, читаем"""
    while True:
        line = channel.readline()  # Считываем строку
        ret_code = int(line[:3])  # вычленяем код ответа
        if line[3] != '-':  # как только добрались до конца принятого сообщения, выходим
            break
    return ret_code  # возвращаем код ответа


def generate_boundary():
    """Метод генерации разделителя между разными частями контента письма"""
    """Просто генерим случайную строку указанной длины и возвращаем"""
    return ''.join(
        [random.choice(BOUNDARY_ALPHABET) for i in range(BOUNDARY_LEN)])


def generate_message(mail_from, mail_to, mail_subject, mail_body, attachments):
    """Метод для генерации письма"""
    boundary = generate_boundary()  # Генерируем разделитель
    mail_body_b64 = base64.b64encode(mail_body.encode('utf8')).decode()  # Переводим текст письма в base64
    mail_subject = '=?utf-8?B?{}?='.format(
        base64.b64encode(mail_subject.encode()).decode())  # Переводим тему письма в base64,
    # не забывая вставить его в указатель кодировки
    message_header = HEADER_FORMAT.format(mail_from=mail_from,
                                          mail_to=mail_to,
                                          mail_subject=mail_subject,
                                          mail_body_base64=mail_body_b64,
                                          boundary=boundary)  # В считанный заранее
    # заголовок письма подставляем нужные данные

    message_attachments = []  # Создаем массив для вложений
    for file_name, file_content in attachments.items():  # Правильно вставляем файлы вложений
        file_name = '=?utf-8?B?{}?='.format(
            base64.b64encode(file_name.encode()).decode())  # Переводим название файла в base64
        file_type = '{type}/{value}'.format(type=file_content[0],
                                            value=file_content[1])  # устанавливаем тип данных
        attachment = ATTACHMENT_FORMAT.format(file_name=file_name,
                                              file_content_base64=file_content[2],
                                              boundary=boundary,
                                              file_type=file_type)  # Вставляем нужную инфу в формат вложения
        message_attachments.append(attachment)  # добавляем в созданный массив наше вложение

    message_terminal = TERMINAL_FORMAT.format(boundary=boundary)  # добавляем концовочку письма
    return ''.join([message_header] + message_attachments + [message_terminal])  # возвращаем наше письмо


def authentication(channel):
    """Метод для прохождения аутентификации"""
    send(channel, 'AUTH LOGIN')  # отправляем серверу команду AUTH LOGIN
    recv(channel)  # принимаем ответ
    login = input('Enter login: ')  # просим пользователя ввести логин
    send(channel, base64.b64encode(login.encode()).decode())  # переводим логин в base64 и отправляем
    recv(channel)  # получаем ответ
    password = input('Enter pass: ')  # теперь то же самое проворачиваем с паролем
    send(channel, base64.b64encode(password.encode()).decode())
    ret_code = recv(channel)  # получаем код ответа
    if ret_code // 100 != 2:
        raise Exception('Login or password wrong')  # Если код не двухсотый,
        # то что-то пошло не так, возвращаем ошибку


def mail_preparation(channel):
    """Метод для подготовки письма к отправке"""
    mail_from = input('Mail from: ')  # просим ввести адрес отправителя
    send(channel, 'MAIL FROM: <{}>'.format(mail_from))  # отправляем серваку команду MAIL FROM
    ret_code = recv(channel)  # получаем код ответа
    if ret_code // 100 != 2:
        raise Exception('MAIL FROM error')  # если код ответа не двухсотый, то что-то не так
    mail_to = input('Mail to: ')  # то же самое для ввода получателя
    send(channel, 'RCPT TO: <{}>'.format(mail_to))
    ret_code = recv(channel)
    if ret_code // 100 != 2:
        raise Exception('RCPT TO error')
    send(channel, 'DATA')  # отправляем команду DATA (для посылки самого письма)
    ret_code = recv(channel)  # получаем код ответа
    if ret_code // 100 in [1, 4, 5]:
        raise Exception('DATA error')  # если код ответа среди сотых, четырехсотых и пятисотых, то ошибочка
    return mail_from, mail_to  # возвращаем адресата и получателя


def files_preparation():
    """Метод, переводящий файлы в base64"""
    """ПРИМЕЧЕНИЕ: если расширения файла не будет в нашем словаре, то файл не будет зашит в результат и,
    соответственно, не будет отправлен"""
    files = {}  # создаем словарь под это дело

    """Словарь, сопоставляющий популярным расширениям тип данных"""
    extensions = {'image': {'png': 'png', 'gif': 'gif', 'ico': 'x-icon', 'jpeg': 'jpeg', 'jpg': 'jpeg',
                            'svg': 'svg+xml', 'tiff': 'tiff', 'tif': 'tiff', 'webp': 'webp', 'bmp': 'bmp'},
                  'video': {'avi': 'x-msvideo', 'mp3': 'mpeg', 'mpeg': 'mpeg', 'ogv': 'ogg', 'webm': 'webm'},
                  'application': {'zip': 'zip', 'xml': 'xml', 'bin': 'octet-stream', 'bz': 'x-bzip',
                                  'doc': 'msword', 'epub': 'epub+zip', 'js': 'javascript', 'json': 'json',
                                  'pdf': 'pdf', 'ppt': 'vnd.ms-powerpoint', 'rar': 'x-rar-compressed',
                                  'sh': 'x-sh', 'tar': 'x-tar'},
                  'audio': {'wav': 'x-wav', 'oga': 'ogg'},
                  'text': {'css': 'css', 'csv': 'csv', 'html': 'html', 'htm': 'html', 'txt': 'plain'}}

    for filename in os.listdir('ATTACHMENTS'):  # проходимся по файлам в директории
        for (data_type, exts) in extensions.items():
            ext = filename.split('.')[-1]  # забираем от имени файла его расширение
            if ext in exts.keys():  # Если расширение есть в нашем списке, то переводим в base64
                with open('ATTACHMENTS/{file}'.format(file=filename), "rb") as file:  # открываем на считывание байтов
                    files[filename] = [data_type, exts[ext], base64.b64encode(file.read()).decode()]  # в base64
    return files  # возвращаем словарь с файлами уже в base64


def send_letter():
    """Метод для посылки письма"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # создаем udp-сокет
    sock.settimeout(TIMEOUT)  # устанавливаем ему тайм-аут в указанную величину
    sock = ssl.wrap_socket(sock)  # оборачиваем сокет в ssl
    sock.connect((HOST, PORT_SSL))  # коннектимся к серваку
    channel = sock.makefile('rw', newline='\r\n')  # превращаем сокет в файл-подобный объект
    recv(channel)  # принимаем ответ от сервака
    files = files_preparation()  # подготавливаем файлы к отправке, если они есть
    print('Was found {} files in ATTACHMENTS directory'.format(len(files)))  # пишем, сколько файлов
    # мы нашли и подготовили
    send(channel, 'EHLO {}'.format(CLIENT_NAME))  # здороваемся с серваком
    recv(channel)  # принимаем ответ
    authentication(channel)  # авторизуемся
    mail_from, mail_to = mail_preparation(channel)  # договариваемся с сервером на отправку письма,
    # получая заодно у пользователя адреса отправителя и получателя
    mail_subject = input('Enter mail subject: ')  # просим пользователя ввести тему письма
    if TXT:  # если нужно взять текст письма из файла, то берем из файла
        with open('LETTER.TXT') as letter_file:
            mail_body = letter_file.read()
    else:  # иначе пусть пользователь вводит прямо в консоли
        mail_body = input('Enter text of letter: ')  # просим пользователя ввести текст письма
    mail = generate_message(mail_from, mail_to, mail_subject,
                            mail_body, files)  # из полученных данных формируем письмо
    channel.write(mail)  # отправляем (хоть мы работаем с файл-подобным объектом, но это все еще наш сокет)
    channel.flush()  # затираем буфер
    ret_code = recv(channel)  # получаем код ответа сервера
    if ret_code // 100 != 2:
        raise Exception('Sending error')  # если код не двухсотый, то печалька, что-то с отправкой не так
    send(channel, 'QUIT')  # завершаем сессию отправкой команды QUIT
    recv(channel)  # принимаем ответ


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()  # Создаем парсер, а затем пихаем в него аргументы
    argparser.add_argument('--txt',
                           action='store_true',
                           help='take message text from file LETTER.txt')
    args = argparser.parse_args()  # парсим аргументы
    TXT = args.txt  # смотрим, брать ли текст письма из файла
    try:
        send_letter()  # пробуем отправить сообщение согласно ключам
        print('Successful')  # в случае успеха сообщаем об этом
    except KeyboardInterrupt:
        print('Досвидос!')  # прощаемся, если пользователь в процессе сам прекратил работу до завершения
    except Exception as error:
        print('Error:', error)  # принтуем, если вдруг какая ошибка
