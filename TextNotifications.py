import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BASE_URL = 'https://classes.usc.edu/term-20221/classes/'
DEPARTMENTS = ['itp']
SECTION_NUMBERS = ['32025']

REFRESH_INT = 42
TEXT_INT = 300

last_text = datetime.now().timestamp() - TEXT_INT - 1


def send_text_through_email(message: str):
    try:
        smtp_user = ""
        smtp_password = ""
        server = 'smtp.gmail.com'
        port = 587
        msg = MIMEMultipart("alternative")
        msg["Subject"] = 'Spots Opened'
        msg["From"] = smtp_user
        msg["To"] = '123456789@mms.cricketwireless.net'
        msg.attach(MIMEText('\n' + message, 'plain'))
        s = smtplib.SMTP(server, port)
        s.ehlo()
        s.starttls()
        s.login(smtp_user, smtp_password)
        s.sendmail(smtp_user, '123456789@mms.cricketwireless.net', msg.as_string())
        s.quit()
    except Exception as e:
        print('An exception occurred: {}'.format(e))


if __name__ == "__main__":
    send_text_through_email("Program Started")
    while True:
        try:
            current_time = datetime.now()
            print(f'Current Time is {current_time.strftime("%Y-%M-%d:%H:%M:%S")}')
            send_text = False
            text_message = ""
            for department in DEPARTMENTS:
                curr_url = BASE_URL + department
                page = requests.get(curr_url)

                soup = BeautifulSoup(page.content, "html.parser")

                for section in SECTION_NUMBERS:
                    result = soup.find("tr", section)
                    print(f'Section Found: {section} {result.text}')

                    if result is not None:
                        is_full = result.find("div", "closed")
                        if is_full is None:
                            message = f'Section {section} in Department {department} is has spots open at {current_time.strftime("%Y-%M-%d:%H:%M:%S")}'
                            send_text = True
                        else:
                            message = f'Section {section} in Department {department} is full at {current_time.strftime("%Y-%M-%d:%H:%M:%S")}'
                        text_message += message + "\n"
                        print(message)

            if send_text and last_text + TEXT_INT < time.time():
                last_text = time.time()
                send_text_through_email(text_message)
                print(f'Sending Text Message "{text_message}"')
            elif send_text:
                print(f'Text was recently sent on {datetime.fromtimestamp(last_text).strftime("%Y-%M-%d:%H:%M:%S")}')
            else:
                print(f'All courses are currently full, no texts will be sent')
            print("\n########################################\n")
            time.sleep(REFRESH_INT)
        except Exception as e:
            print('An exception occurred: {}'.format(e))

