from email.mime.text import MIMEText
from email.header import Header
import smtplib

def send(func):
    """ Избавляет от дублирования кода """
    def wrapper(self, mail, code):
        func(self, mail, code)
        msg = MIMEText(self.body, 'plain', 'utf-8')
        msg['Subject'] = Header(self.subject, 'utf-8')
        self.smtpObj.sendmail("pyssword.server@gmail.com", self.mail, msg.as_string())
        self.smtpObj.quit()
    return wrapper
 

class Sender():
    def __init__(self):
        """ Подключаемся к почтовому клиенту гугл """
        self.smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        self.smtpObj.starttls()
        self.smtpObj.login("pyssword.server@gmail.com","invoker123")
    
    @send
    def send_reg(self, mail, code):
        """Отправка сообщения о регистрации """
        self.subject = "Код Регистрации в приложении"
        self.body = "Здравствуйте. Этот адрес указан для регистрации. Если вы вводили адрес - используйте код ниже, в противном случае игнорируйте сообщение\nВаш код: {}".format(code)
        self.mail = mail

    @send
    def send_rec(self, mail, code):
        """ Отправка сообщения с кодом восстановления пароля"""
        self.subject = "Код восстановления пароля"
        self.body = "Здравствуйте. К вашему аккаунту пытаются восстановить доступ. Если это вы - используйте код ниже, в противном случае игнорируйте сообщение\nВаш код: {}".format(code)
        self.mail = mail