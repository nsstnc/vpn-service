import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def send_email(self, subject, body, to_email):
        """Отправляет электронное письмо.

        :param subject: Тема письма.
        :param body: Содержание письма.
        :param to_email: Адрес получателя.
        :param from_email: Адрес отправителя.
        :param password: Пароль от почтового ящика отправителя.
        """
        # Создаем объект сообщения
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Добавляем текстовое содержимое письма
        msg.attach(MIMEText(body, 'plain'))

        # Настраиваем SMTP сервер
        server = smtplib.SMTP('smtp.mail.ru', 587)
        server.starttls()

        try:
            # Входим в почтовый ящик отправителя
            server.login(self.email, self.password)
            # Отправляем письмо
            server.sendmail(self.email, to_email, msg.as_string())
            print('Письмо отправлено успешно!')
        except Exception as e:
            print(f'Ошибка при отправке письма: {e}')
        finally:
            server.quit()

