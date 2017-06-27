import time
import string
import telegram
import random
import threading
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from queue import Queue

bot = telegram.Bot('bot-token')

driver_path = './chromedriver'

options = webdriver.ChromeOptions()
#options.add_argument('headless')
#options.add_argument('disable-gpu')

c_driver = webdriver.Chrome(driver_path, chrome_options=options)
omegle = webdriver.Chrome(driver_path, chrome_options=options)
c_driver.get("http://www.cleverbot.com/")
omegle.get("http://www.omegle.com/")

#send interests
interests = ['sex', 'trump', 'english', 'porn', 'usa', 'female', 'male', '']
interests_input =  omegle.find_element_by_class_name('newtopicinput')

for i in interests:
       #interests_input.send_keys(i)
       interests_input.send_keys(Keys.RETURN);
        
omegle.find_element_by_id('textbtn').click()
msg_count = 0

wait_times = 0
disconnected = False

class oChat(threading.Thread):
        def __init__(self, omegle, init_msg, inboundQ, outboundQ, telebot):
                threading.Thread.__init__(self)
                self.msgs_arrived = 0
                self.o = omegle
                self.init_msg = init_msg
                self.inboundQ = inboundQ
                self.outboundQ = outboundQ
                self.telebot = telebot
                self.disconnect_time = 20
                self.chat_history = []

        def send_msg(self, text):
                if not self.is_connected():
                        return False
                
                self.msg_field.send_keys(''.join([i if ord(i) < 226 else '' for i in text]))
                self.sendbtn.click()
                self.chat_history.append('Bot: %s' %text)

        def is_connected(self):
		try:
		        if len(self.o.find_elements_by_class_name("newchatbtnwrapper")) > 0:
		                return False
		        elif 'stranger' in self.o.find_element_by_class_name('statuslog').text:
		                 return True
		        return False
                except:
			return False

        def msg_count(self):
                self.pull_msg()
                return len(self.msg_list)       

        def run(self):
                self.start_time = time.time()
                while True:
                        time_left = time.time() - self.start_time
                        if self.new_msg() and self.is_connected():
                                self.disconnect_time = 50
                                msg = self.get_latest_msg()
                                self.inboundQ.put(msg)
                                self.chat_history.append('Stranger: %s' %msg)
                                        
                        elif time_left > self.disconnect_time or not self.is_connected():
                                if len(self.chat_history) > 20:
                                        chat_msg = ''
                                        for m in self.chat_history:
                                                chat_msg += m + '\n'
                                        self.telebot.send_message(chat_id='@cleverOmegle', text=chat_msg)

                                self.chat_history = []        
                                self.disconnect_time = 20
                                self.disconnect()
                                self.connect()
				
                               
                        if not self.outboundQ.empty():
                                try:
                                        msg_out = self.outboundQ.get_nowait()
                                except:
                                        pass
                                else:
                                        self.send_msg(msg_out)
                                        self.outboundQ.task_done()

        def new_msg(self):
                if self.msg_count() > self.msgs_arrived:
                        self.msgs_arrived = self.msg_count()
                        self.start_time = time.time()
                        print('[+] New message omegle')
                        return True
                else:
                        return False

        def get_latest_msg(self):
                self.pull_msg()
                return ''.join([i if ord(i) < 226 else '' for i in self.msg_list[-1].find_element_by_tag_name('span').text])
        
        def pull_msg(self):
                self.msg_list = self.o.find_elements_by_class_name("strangermsg")       

        def disconnect(self):
		self.o.get_screenshot_as_file('./screen.png') 
                webdriver.ActionChains(self.o).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.3)
                webdriver.ActionChains(self.o).send_keys(Keys.ESCAPE).perform()
		time.sleep(3)
                print('[-] Disconnected')

        def connect(self):
                self.sendbtn = self.o.find_element_by_class_name('sendbtn')
                self.msg_field = self.o.find_element_by_class_name('chatmsg')
                print('[+] Connected')
                self.send_msg(self.init_msg)
                self.start_time = time.time()
                self.msgs_arrived = self.msg_count()

class cleverbot(threading.Thread):
        def __init__(self, driver, inboundQ, outboundQ):
                threading.Thread.__init__(self)
                self.c = driver
                self.inboundQ = inboundQ
                self.outboundQ = outboundQ
                self.last_text_received = ""
                self.form = self.c.find_element_by_id('avatarform')

        def new_msg(self):
                try:
                        icon = self.c.find_element_by_id('snipTextIcon')
                except:
                        return False

                current = self.get_answer()
                if not current == self.last_text_received and icon.get_attribute('class') == 'yellow':
                        self.last_text_received = current
                        print('[+] New message cleverbot')
                        return True
                else:   
                        return False

        def get_answer(self):
                answer = self.c.find_element_by_id('line1').text
                
                if answer[-1] == '.':
                        return answer[:-1]
                else:
                        return answer

        def send_msg(self, text):
                self.c.find_element_by_css_selector('#avatarform [name=stimulus]').send_keys(text)
                self.form.submit()
                self.last_text_send = text

        def run(self):
                while True:
                        if self.new_msg():
                                responds_wait = random.randint(1, 4)
                                time.sleep(responds_wait)
                                self.outboundQ.put(self.get_answer())

                        if not self.inboundQ.empty():
                                try:
                                        msg_in = self.inboundQ.get_nowait()
                                except:
                                        pass
                                else:
                                        self.send_msg(msg_in)
                                        self.inboundQ.task_done()

def main():
	init_msg = 'female 23'

	inboundQ = Queue()
	outboundQ = Queue()
	threads = []

	oThread = oChat(omegle, init_msg, inboundQ, outboundQ, bot)
	threads.append(oThread)
	oThread.start()

	cThread = cleverbot(c_driver, inboundQ, outboundQ)
	threads.append(cThread)
	cThread.start()

	while True:
		if not oThread.is_alive():
			oThread = oChat(omegle, init_msg, inboundQ, outboundQ, bot)
			threads.append(oThread)
			oThread.start()

		if not cThread.is_alive():
			cThread = cleverbot(c_driver, inboundQ, outboundQ)
			threads.append(cThread)
			cThread.start()

if __name__ == "__main__":
    main()                   
