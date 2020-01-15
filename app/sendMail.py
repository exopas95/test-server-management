import smtplib
from email.mime.text import MIMEText

def send_mail(receiver, content):
    text = content
    smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp.login('yoonbin31@gmail.com','evcalpcfvjgkteov')
    message = MIMEText(text)
    message['Subject'] = 'TS management notifier : Please relocate TS'
    message['From'] = 'TSmanagement@gmail.com'
    message['To'] = receiver
    smtp.sendmail('TSmanagement@gmail.com', receiver, message.as_string())
    smtp.quit()



