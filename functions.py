from bs4 import BeautifulSoup
import requests
from datetime import datetime
import sqlite3




def text_update(text, **variables):
	#replace variables in the text with it value
	for var, new_val in variables.items():
		text = text.replace(var, new_val)
	return text


def reply_key(names: list, types, row=1):
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
	keyboards = [types.KeyboardButton(text=name) for name in names]
	f = lambda A, n=row: [A[i:i+n] for i in range(0, len(A), n)]
	names = f(keyboards)
	for name in names:
		keyboard.add(*name)
	return keyboard



def get_inline(data, types, row=1):
	buttons = []
	keyboard = types.InlineKeyboardMarkup(row_width=row)
	for lan, call_data in data.items():
		buttons.append(types.InlineKeyboardButton(text=lan, callback_data=call_data))
	keyboard.add(*buttons)
	return keyboard


def prayer_times(region: str, day: int):
	month = datetime.now().month
	year = datetime.now().year
	url = f"http://islom.uz/vaqtlar/{region}/{month}"
	result = requests.get(url)
	if result.status_code != 200:
		return "Error"

	doc = BeautifulSoup(result.text, "html.parser")
	if day == 0:
		tags = doc.find("tr", class_=["juma bugun", "p_day bugun"])
	else:
		tags = doc.find_all("tr", class_=["juma erta", "p_day erta"])[0]
	td_tags = tags.find_all("td")
	data = [i.string for i in td_tags]
	date = f"{year}.{month}.{data[1]}"
	data = data[3:]
	data.insert(0, date)
	return data



def insert_prayer_time(city_num, date, data, yesterday):
	conn = sqlite3.connect("data/prayer_times_info.db")
	c = conn.cursor()
	c.execute("INSERT INTO prayer_times VALUES (?, ?, ?)", (city_num, date, data))
	c.execute("DELETE FROM prayer_times WHERE date_=:yesterday", {"yesterday": yesterday})
	conn.commit()
	conn.close()
	return


def search_prayer_time(city_num, date):
	conn = sqlite3.connect("data/prayer_times_info.db")
	c = conn.cursor()
	c.execute("SELECT data FROM prayer_times WHERE city_num=:city_num AND date_=:date_",
		{"city_num": city_num, "date_": date})
	data = c.fetchone()
	conn.close()
	return data

	



def find_page(page_num: str):

	#check db for existing hadis
	conn = sqlite3.connect("data/hadis.db")
	c = conn.cursor()
	c.execute("SELECT * FROM hadis WHERE page=:page", {"page": page_num})
	data = c.fetchall()
	if any(data):
		return data

	url = f"https://islom.uz/maqolalar/51/{page_num}"
	result = requests.get(url)
	if result.status_code != 200:
		return "Error"

	doc = BeautifulSoup(result.text, "html.parser")
	rows = doc.find_all("div", class_="title_maqola_2")
	images = doc.find_all("img", class_="image_state")
	data = []
	for i in range(len(rows)):
		values = (rows[i].a.string, rows[i].a["href"], page_num, None, images[i]["src"])
		data.append(values)
		c.execute("INSERT INTO hadis VALUES (?, ?, ?, ?, ?)", values)
		conn.commit()
	conn.close()
	return data


def update_photo(titles, file_ids):
	conn = sqlite3.connect("data/hadis.db")
	c = conn.cursor()
	for i in range(len(file_ids)):
		c.execute("UPDATE hadis SET photo=:photo WHERE title=:title",
			{"photo": file_ids[i], "title": titles[i]})
		conn.commit()
	conn.close()


def adding_hadis_db(text, url):
	conn = sqlite3.connect("data/hadis.db")
	c = conn.cursor()
	c.execute("UPDATE hadis SET h_text=:h_text WHERE url=:url",
			{"h_text": text, "url": url})
	conn.commit()
	conn.close()


def search_hadis_db(url):
	conn = sqlite3.connect("data/hadis.db")
	c = conn.cursor()
	c.execute("SELECT h_text FROM hadis WHERE url=:url", {"url": url})
	text = c.fetchone()
	conn.close()
	return text

def get_hadis_text(url):
	search_term = url
	url = f"https://islom.uz{url}"
	stat = True
	text = search_hadis_db(search_term)[0]
	if text:
		stat = False
		text = [text]
	if stat:
		result = requests.get(url)
		if result.status_code != 200:
			return "Error"

		doc = BeautifulSoup(result.text, "html.parser")
		hadis_text = doc.find("div", class_="inmaqola_text").find_all("p")
		hadis_text = [row.text for row in hadis_text]
		h_text = "\n\n".join(hadis_text) + f"\n\nМанба: https://islom.uz/maqolalar/51/1"
		text = [h_text]
		adding_hadis_db(h_text, search_term)

	while len(text[-1]) >= 4096:
		before = text[-1][:4096]
		index = before.rfind("\n\n")
		before = text[-1][:index]
		after = text[-1][index:]
		text.remove(text[-1])
		text.append(before)
		text.append(after)

	return text



def add_user(u_id, name):
	conn = sqlite3.connect("data/users.db")
	c = conn.cursor()
	try:
		c.execute("INSERT INTO users VALUES(?, ?)", (u_id, name))
	except:
		pass
	conn.commit()
	conn.close()

def get_users():
	conn = sqlite3.connect("data/users.db")
	c = conn.cursor()
	c.execute("SELECT * FROM users")
	users = c.fetchall()
	conn.close()
	return users



def get_limit_words(text):
	text = [text]
	while len(text[-1]) >= 4096:
		before = text[-1][:4096]
		index = before.rfind("\n")
		before = text[-1][:index]
		after = text[-1][index:]
		text.remove(text[-1])
		text.append(before)
		text.append(after)
	return text
