import seleniumrequests
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import smtplib

from TestEmail import retrieve_passcode
from TextNotifications import send_text_through_email

BASE_URL = 'https://classes.usc.edu/term-20221/classes/'
DEPARTMENTS = ['itp']
# SECTION_NUMBERS = ['32025']
# SECTION_NUMBERS = ['31833']

REFRESH_INT = 4.2
REGISTER_INT = 60

last_register = datetime.now().timestamp() - REGISTER_INT - 1


def wait_until(driver, url):
    if driver.current_url != url:
        WebDriverWait(driver, 10).until(EC.url_changes(url))


def register_for_class():
    try:
        BASE_SCHEDULE_URL = 'https://webreg.usc.edu/myCoursebin/SchdUnschRmv?act=Sched&section='

        USERNAME = ''
        PASSWORD = ''

        options = Options()
        options.headless = True

        driver = seleniumrequests.Chrome(options=options)

        driver.get('https://my.usc.edu/')

        wait_until(driver, "https://login.usc.edu/")
        time.sleep(2)

        username_input_elem = driver.find_element_by_id('username')
        password_input_elem = driver.find_element_by_id('password')
        login_button_elem = driver.find_element_by_xpath('/html/body/div/div/div[1]/div/div/div/div/form/div/button')
        username_input_elem.send_keys(USERNAME)
        password_input_elem.send_keys(PASSWORD)
        login_button_elem.click()

        time.sleep(4)

        driver.switch_to.frame(driver.find_element_by_id('duo_iframe'))

        gv_dropdown_elem = driver.find_element_by_xpath("//option[text()='Mobile (XXX-XXX-1234)']")
        gv_dropdown_elem.click()
        time.sleep(0.25)

        print(gv_dropdown_elem.text)
        device_index = gv_dropdown_elem.get_attribute('value')

        fieldset_elem = driver.find_element_by_xpath("//fieldset[@data-device-index='" + device_index + "']")
        # print(fieldset_elem.text)

        enter_passcode_button_elem = fieldset_elem.find_element_by_id('passcode')
        enter_passcode_button_elem.click()
        time.sleep(0.25)

        print(enter_passcode_button_elem.text)

        text_new_codes_button_elem = driver.find_element_by_xpath("//button[contains(text(),'Text me new codes')]")
        text_new_codes_button_elem.click()
        current_timestamp = time.time()
        print(f'Current Timestamp: {current_timestamp}')

        time.sleep(0.25)
        time.sleep(1)

        # print(text_new_codes_button_elem.text)

        passcode = retrieve_passcode(current_timestamp)

        print(passcode)

        passcode_input_elem = fieldset_elem.find_element_by_class_name('passcode-input')
        passcode_input_elem.send_keys(passcode + Keys.ENTER)

        time.sleep(0.25)

        wait_until(driver, "https://my.usc.edu/")
        time.sleep(4)

        print(driver.current_url)

        driver.get("https://my.usc.edu/portal/oasis/webregbridge.php")
        wait_until(driver, "https://webreg.usc.edu/Terms")
        print("At terms")
        time.sleep(1)

        driver.get("https://webreg.usc.edu/Terms/termSelect?term=20221")
        wait_until(driver, "https://webreg.usc.edu/Departments")
        print("At Departments")
        time.sleep(1)

        driver.get("https://webreg.usc.edu/myCourseBin")
        wait_until(driver, "https://webreg.usc.edu/myCourseBin")
        print("At Course Bin")
        time.sleep(1)

        for section in SECTION_NUMBERS:
            driver.get(BASE_SCHEDULE_URL + section)
            time.sleep(1)

        driver.get("https://webreg.usc.edu/Register")
        print("Registering")
        time.sleep(10)

        # jsrequest = '''procRegSubmt();'''
        # result = driver.execute_script(jsrequest);

        # print(result)

        response = driver.request('POST', 'https://webreg.usc.edu/RegResp', data={})
        # print()
        soup = BeautifulSoup(response.content, "html.parser")
        result = soup.find("div", {"class": "content-wrapper-regconfirm"})
        print(result.text)

        # submit_elem = WebDriverWait(driver, 30).until(
        #     EC.presence_of_element_located((By.ID, "SubmitButton"))
        # )
        # submit_elem = driver.find_element_by_xpath('//*[@id="SubmitButton"]')
        # submit_elem.click()
        wait_until(driver, "https://webreg.usc.edu/RegResp")
        # time.sleep(2)
        # response_elem = driver.find_element_by_xpath('/html/body/div/div[2]/div/div/div/div/div')
        # print(response_elem.text)
        time.sleep(10)

        driver.quit()
    except Exception as e:
        print('An exception occurred: {}'.format(e))


def main():
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

            # send_text = True
            if send_text and last_register + REGISTER_INT < time.time():
                last_text = time.time()
                send_text_through_email(text_message)
                register_for_class()
                print(f'REGISTERING and Sending Text Message "{text_message}"')
            elif send_text:
                print(f'Text was recently sent on {datetime.fromtimestamp(last_text).strftime("%Y-%M-%d:%H:%M:%S")}')
            else:
                print(f'All courses are currently full, no registration will take place')
            print("\n########################################\n")
            time.sleep(REFRESH_INT)
        except Exception as e:
            print('An exception occurred: {}'.format(e))


if __name__ == "__main__":
    main()
