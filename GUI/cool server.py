import socket
from selenium import webdriver
import time
file = open('name&pass.txt')
name, password = file.read().split('\n')
url = 'https://accounts.google.com/ServiceLogin/identifier?service=mail&passive=true&rm=false&continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&ss=1&scc=1&ltmpl=default&ltmplcache=2&emr=1&osid=1&flowName=GlifWebSignIn&flowEntry=ServiceLogin'

data = 'enter_gmail'
if data.startswith('enter_gmail'):
    driver = webdriver.Chrome(r'C:\Users\AMIT\Downloads\chromedriver_win32 (2)\chromedriver.exe')
    driver.set_page_load_timeout(10)
    driver.get(url)
    inputElement = driver.find_element_by_id("identifierId")
    inputElement.send_keys(name)
    button = driver.find_elements_by_id('identifierNext')[0]
    button.click()

    time.sleep(1)
    inputElement = driver.find_element_by_name('password')
    inputElement.send_keys(password)

    time.sleep(0.05)
    button = driver.find_element_by_id('passwordNext')
    button.click()
    input()
    driver.close()
        # inputElement = driver.find_element_by_id("input-wrap")
        # inputElement.send_keys(text)

# server_socket= socket.socket()
# server_socket.bind(("0.0.0.0", 2345))
# server_socket.listen(1)

# client, address= server_socket.accept()
# data = ''
# while data != "exit":
#     break
    # data = client.recv(1024).decode()

