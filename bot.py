import time
import string
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

c_driver = webdriver.Chrome('./chromedriver')
omegle = webdriver.Chrome('./chromedriver')
c_driver.get("http://www.cleverbot.com/")
omegle.get("http://www.omegle.com/")

#omegle init
omegle.find_element_by_class_name('newtopicinput').send_keys('')
omegle.find_element_by_id('textbtn').click()
msg_count = 0

wait_times = 0
disconnected = False

class oChat():
	def __init__(self, omegle, init_msg):
		self.msgs_arrived = 0		

		self.o = omegle
		self.printable = set(string.printable)
		self.sendbtn = self.o.find_element_by_class_name('sendbtn')
    		self.msg_field = self.o.find_element_by_class_name('chatmsg')
		print('[+] Connected')
		time.sleep(3)
		self.send_msg(init_msg)

	def send_msg(self, text):
		if not self.is_connected():
			return False
		self.msg_field.send_keys(text)
    		self.sendbtn.click()

	def is_connected(self):
		if len(self.o.find_elements_by_class_name("newchatbtnwrapper")) > 0:
			return False
		
		return True
		
	def msg_count(self):
		self.pull_msg()
		return len(self.msg_list)	

	def new_msg(self):
		if self.msg_count() > self.msgs_arrived:
			self.msgs_arrived = self.msg_count()
			print('[+] New message omegle')
			return True
		else:
			return False

	def get_latest_msg(self):
		self.pull_msg()
		return filter(lambda x: x in self.printable, self.msg_list[-1].find_element_by_tag_name('span').text)
	
	def pull_msg(self):
		self.msg_list = self.o.find_elements_by_class_name("strangermsg")	

	def disconnect(self):
		webdriver.ActionChains(self.o).send_keys(Keys.ESCAPE).perform()
		time.sleep(0.3)
		webdriver.ActionChains(self.o).send_keys(Keys.ESCAPE).perform()
		print('[-] Disconnected')

class cleverbot():
	def __init__(self, driver):
		self.c = driver
		self.last_text_received = ""
		self.form = self.c.find_element_by_id('avatarform')

	def new_msg(self):
		try:
			self.c.find_element_by_css_selector('#line1 #snipTextIcon')
		except:
			return False

		current = self.get_answer()
		if not current == self.last_text_received:
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


oc = oChat(omegle, 'w 23')
cbot = cleverbot(c_driver)
disconnect_time = 20

while True:
    	while not oc.new_msg() and wait_times < disconnect_time and oc.is_connected():
		time.sleep(0.5)
		wait_times += 1
		print('[-] Disconnecting in %s' % (disconnect_time - wait_times))

	if oc.is_connected() and wait_times < disconnect_time:
		disconnect_time = 60
		cbot.send_msg(oc.get_latest_msg())
		
		while not cbot.new_msg():
			pass
		oc.send_msg(cbot.get_answer())
	else:
		disconnect_time = 20
		oc.disconnect()
		oc = oChat(omegle, 'w 23')
	
	wait_times = 0

