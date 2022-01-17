from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
import functions as fun
from datetime import date, datetime, timedelta

from config import TOKEN, ADMIN, ADMIN_PASSWORD

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    qari_name = State()
    surah_num = State()
    feedback = State()

    page_num = State()
    quran = State()

    


#----------------------------file handling-------------------------#
with open("data/languages.json") as file:
	lan_data = json.load(file)

with open("data/user_info.json") as file:
	user_info = json.load(file)

with open("data/pictures.json") as file:
	pictures = json.load(file)





#----------------------------start command---------------------------#
@dp.message_handler(commands=["start", "help"])
async def process_start_command(message: types.Message):
	if str(message.from_user.id) not in user_info:  #proccessing the user languageo
		user_lan = message.from_user.language_code
		if user_lan in lan_data:
			user_info[str(message.from_user.id)] = {"language": user_lan}	
		else:
			user_info[str(message.from_user.id)] = {"language": "uz"}
		user_info[str(message.from_user.id)]["first_name"] = message.from_user.first_name
		with open("data/user_info.json", "w") as file:
				json.dump(user_info, file) 
	user_lan = user_info[str(message.from_user.id)]["language"]
	if message.text == "/start":
		msg = fun.text_update(text=lan_data[user_lan]["greeting"], name123=message.from_user.first_name)
		names = lan_data[user_lan]["first_btns"]
		await message.answer(lan_data[user_lan]["basmala"])
		await message.answer(msg, reply_markup=fun.reply_key(names=names, types=types, row=2))
	else: 
		msg = lan_data[user_lan]["help"]
		await message.answer(msg)

	#adding to the db
	name = message.from_user.first_name
	u_id = message.chat.id
	fun.add_user(u_id, name)


@dp.message_handler(commands=["language"])
async def change_language(message: types.Message):
	user_lan = user_info[str(message.from_user.id)]["language"]
	msg = lan_data[user_lan]["lan_change"]
	btn_data = {}
	for lan in lan_data[user_lan]["languages"]:
		btn_data[lan] = f"language_{lan_data[user_lan]['languages'][lan]}"
	btn = fun.get_inline(btn_data, types, 2)
	await message.answer(msg, reply_markup=btn)


@dp.message_handler(commands=["feedback"])
async def sending_feedback(message: types.Message):
	user_lan = user_info[str(message.from_user.id)]["language"]
	msg = lan_data[user_lan]["feedback"]
	await message.reply(msg, reply_markup=types.ReplyKeyboardRemove())
	await Form.feedback.set()

@dp.message_handler(commands=["find"])
async def find_user(message: types.Message):
	if message.from_user.id == int(ADMIN):
		user_id = message.text.split()[1]
		if user_id in user_info:
			await message.answer(f"User found✅\nName: {user_info[user_id]['first_name']}")
		else:
			await message.answer("User not found")


#-------------------------inline button handlers----------------------#
@dp.callback_query_handler(Text(startswith="language_"))
async def change_language(call: types.CallbackQuery):
	user_lan = user_info[str(call.from_user.id)]["language"]
	code = call.data.split("_")[1]
	user_info[str(call.from_user.id)]["language"] = code
	with open("data/user_info.json", "w") as file:
		json.dump(user_info, file)
	msg = lan_data[code]["lan_change_response"]
	text = ""
	for lan in lan_data[user_lan]["languages"]:
		if lan_data[user_lan]["languages"][lan] == code:
			text = fun.text_update(msg, langu123=lan)
	await call.message.edit_text(text)




@dp.callback_query_handler(text="show_users")
async def sending_num_users(call: types.CallbackQuery):
	user_lan = user_info[str(call.from_user.id)]["language"]
	number = len(fun.get_users())
	msg = fun.text_update(lan_data[user_lan]["users"], number1223=str(number))
	await call.message.answer(msg)


@dp.callback_query_handler(text="show_users_data")
async def sending_users(call: types.CallbackQuery):
	users = fun.get_users()
	msg = ""
	for u_id, name in users:
		msg += f"{name}: {u_id}\n"
	msg = fun.get_limit_words(msg)
	for m in msg:
		await call.message.answer(m)
		

@dp.callback_query_handler(text="add_quran")
async def adding_quran(call: types.CallbackQuery):
	await bot.send_message(call.message.chat.id, "Send the photo of qori and his name in caption.", reply_markup=fun.reply_key(["Main menu"], types))
	await Form.quran.set()




#prayer times choosing region
@dp.callback_query_handler(text_contains="region_")
async def selecting_region(call: types.CallbackQuery):
	user_lan = user_info[str(call.from_user.id)]["language"]
	region_id = call.data.split("_")[1]
	region = call.data.split("_")[2]
	msg = lan_data[user_lan]["selected_region"]
	btn_data = {}
	count = 0
	for time in lan_data[user_lan]["today_tomw"]:
		btn_data[time] = f"choose_day_{region_id}_{count}_{region}"
		count += 1
	await call.message.edit_text(msg, reply_markup=fun.get_inline(btn_data, types, 2))

	user_info[str(call.message.chat.id)]["region"] = region
	with open("data/user_info.json", "w") as file:
		json.dump(user_info, file)


#choosing today or tomorrow
@dp.callback_query_handler(text_contains="choose_day_")
async def selecting_time(call: types.CallbackQuery):
	user_lan = user_info[str(call.from_user.id)]["language"]
	region_id = call.data.split("_")[2]
	region = call.data.split("_")[4]
	time = int(call.data.split("_")[3])
	yesterday = datetime.now() - timedelta(days=1)
	yesterday = yesterday.strftime('%Y-%m-%d')
	ins_date = 0
	if time == 0:
		ins_date = date.today()
	else:
		tomorrow = datetime.now() + timedelta(days=1)
		ins_date = tomorrow.strftime('%Y-%m-%d')

	data = []
	data_exist = fun.search_prayer_time(int(region_id), ins_date)          # searching prayer time from db
	if data_exist == None:         #prayer time doesn't found in db
		data = fun.prayer_times(region=region_id, day=time)
		if data == "Error":
			return await call.message.edit_text(lan_data[user_lan]["error_msg"])
		prayer_times_db = "_".join(data)                               #modifing data to save as text format as ("12:45_15:00")
		fun.insert_prayer_time(int(region_id), ins_date, prayer_times_db, yesterday)
	else:                           #prayer time does found in db
		data = data_exist[0].split("_")     
	msg = f"{region}: {data[0]}\n"
	count = 0
	for name in lan_data[user_lan]["prayer_names"]:
		count += 1
		msg += f"\n{name}: {data[count]}"
	await call.message.edit_text(msg)
	await bot.send_message(chat_id=call.message.chat.id, text=lan_data[user_lan]["prayer_info"], reply_markup=fun.reply_key([lan_data[user_lan]["back"][1]], types))


@dp.callback_query_handler(text="select_other_region")
async def select_other_region(call: types.CallbackQuery):
	user_lan = user_info[str(call.from_user.id)]["language"]
	msg = lan_data[user_lan]["regions_txt"]
	data = {}
	for region, index in lan_data[user_lan]["regions"].items():
		data[region] = f"region_{index}_{region}"
	btn = fun.get_inline(data, types, 2)
	await call.message.edit_text(msg, reply_markup=btn) 






#hadis section

@dp.callback_query_handler(Text(startswith="read_hadis_"))
async def display_whole_hadis(call: types.CallbackQuery):
	await call.answer(cache_time=60)
	user_lan = user_info[str(call.from_user.id)]["language"]
	url = call.data.split("_")[-1]
	num_messages = int(call.data.split("_")[-2])
	message_num = int(call.data.split("_")[-3])
	before = message_num - 1
	after = num_messages - message_num
	for i in range(before):
		await bot.delete_message(call.message.chat.id, call.message.message_id-i-1)
	for i in range(after):
		await bot.delete_message(call.message.chat.id, call.message.message_id+i+1)

	hadis_text = fun.get_hadis_text(url)
	if hadis_text == "Error":
		return await call.message.answer(lan_data[user_lan]["error_msg"])
	btn = fun.reply_key(lan_data[user_lan]["back_side"], types, 2)
	for msg in hadis_text: 
		await bot.send_message(chat_id=call.message.chat.id, text=msg, reply_markup=btn)







#-------------------------------text handler---------------------------#
#main menu
menu = [lan_data[lan]["back"][1] for lan in lan_data]
@dp.message_handler(lambda message: message.text in menu, state="*")
async def back_to_menu(message: types.Message, state: FSMContext):
	await state.finish()
	user_lan = user_info[str(message.from_user.id)]["language"]
	names = lan_data[user_lan]["first_btns"]
	await message.reply("Ok", reply_markup=fun.reply_key(names, types, 2))



#check the admin
@dp.message_handler(lambda message: message.text == ADMIN_PASSWORD and message.chat.id == int(ADMIN))
async def checking_the_admin(message: types.Message):
	user_lan = user_info[str(message.from_user.id)]["language"]
	msg = fun.text_update(lan_data[user_lan]["admin_greeting"], check_stick="✅")
	btn_data = {
	"Users #": "show_users",
	"Users data": "show_users_data",
	"Add quran" : "add_quran"
	}
	btn = fun.get_inline(btn_data, types, 2)
	await message.answer(msg, reply_markup=btn)



#Quran button pressed
quron_btn = [lan_data[lan]["first_btns"][0] for lan in lan_data]
@dp.message_handler(lambda message: message.text in quron_btn)
async def quron_btn_pressed(message: types.Message):
	user_lan = user_info[str(message.from_user.id)]["language"]
	msg = lan_data[user_lan]["names_txt"]
	await Form.qari_name.set()
	names = lan_data[user_lan]["names"]
	await message.answer(lan_data[user_lan]["surah"])
	await message.answer(msg, reply_markup=fun.reply_key(names, types, 2))


#choosing qari
@dp.message_handler(state=Form.qari_name)
async def process_age(message: types.Message, state: FSMContext):
	user_lan = user_info[str(message.from_user.id)]["language"]
	name = message.text
	if name not in lan_data[user_lan]["names"]:
		return
	async with state.proxy() as data:
		data["qari_name"] = name
	await Form.next()
	msg = lan_data[user_lan]["quran_btn_text"]
	btn = lan_data[user_lan]["back"]
	try:
		await bot.send_photo(message.chat.id, pictures[name], parse_mode="html")      #send qori picture
	except:
		pass
	await message.answer(msg, reply_markup=fun.reply_key(btn, types, 2))



@dp.message_handler(lambda message: not message.text.isdigit() or int(message.text) > 114, state=Form.surah_num)
async def surah_num_invalid(message: types.Message, state: FSMContext):
	user_lan = user_info[str(message.from_user.id)]["language"]
	if message.text == lan_data[user_lan]["back"][0]:                       #if the user pressed back button
		await state.finish()
		names = lan_data[user_lan]["names"]
		await Form.qari_name.set()
		return await message.reply("Ok", reply_markup=fun.reply_key(names, types, 2))
	elif message.text == lan_data[user_lan]["back"][1]:
		await state.finish()
		names = lan_data[user_lan]["first_btns"]
		return await message.reply("Ok", reply_markup=fun.reply_key(names, types, 2))
		
	"""
	If surah number is invalid
	"""
	return await message.reply(lan_data[user_lan]["invalid_surah_num"])


#sending surah
@dp.message_handler(lambda message: message.text.isdigit(), state=Form.surah_num)
async def process_surah(message: types.Message, state: FSMContext):
	user_lan = user_info[str(message.from_user.id)]["language"]
	async with state.proxy() as data:
		who = lan_data[user_lan]["names"].index(data["qari_name"])
		index = 114 * who
	surah_num = int(message.text) + 1 + index
	await bot.forward_message(chat_id=message.chat.id, from_chat_id="@quran_bot_uchun", message_id=surah_num)
	

@dp.message_handler(state=Form.feedback)
async def feedback(message: types.Message, state: FSMContext):
	user_lan = user_info[str(message.from_user.id)]["language"]
	back = [lan_data[i]["back"][0] for i in lan_data]
	if message.text in back:
		await state.finish()
		names = lan_data[user_lan]["first_btns"]
		await message.reply("Ok", reply_markup=fun.reply_key(names, types, 2))
	else:
		btn = fun.reply_key([lan_data[user_lan]["back"][0]], types)
		await bot.forward_message(chat_id=-1001586835899, from_chat_id=message.chat.id, message_id=message.message_id)
		await message.answer(lan_data[user_lan]["feedback2"], reply_markup=btn)





#-----------------------prayer times--------------------
namoz_btn = [lan_data[lan]["first_btns"][1] for lan in lan_data]
@dp.message_handler(lambda message: message.text in namoz_btn)
async def prayer_times(message: types.Message):
	user_lan = user_info[str(message.from_user.id)]["language"]
	try:
		region = user_info[str(message.chat.id)]["region"]
		msg = fun.text_update(lan_data[user_lan]["selected_region2"], region123=region)
		region_id = lan_data[user_lan]["regions"][region]
		btn_data = {}
		count = 0
		for time in lan_data[user_lan]["today_tomw"]:
			btn_data[time] = f"choose_day_{region_id}_{count}_{region}"
			count += 1

		btn_data[lan_data[user_lan]["select_other_region"]] = "select_other_region"
		btn = fun.get_inline(btn_data, types, 2)
		await message.answer(msg, reply_markup=btn)

	except:
		msg = lan_data[user_lan]["regions_txt"]
		data = {}
		for region, index in lan_data[user_lan]["regions"].items():
			data[region] = f"region_{index}_{region}"
		btn = fun.get_inline(data, types, 2)
		await message.answer(msg, reply_markup=btn) 




#-----------------------------HADITH-------------------------#
hadith_btn = [lan_data[lan]["first_btns"][2] for lan in lan_data]
@dp.message_handler(lambda message: message.text in hadith_btn)
async def hadith_button(message: types.Message):
	user_lan = user_info[str(message.from_user.id)]["language"]
	try:
		current_page = user_info[str(message.from_user.id)]["current_page"]
		page_one = fun.find_page(current_page)
		if current_page == 1:
			await message.reply("Ok", reply_markup=fun.reply_key(lan_data[user_lan]["back_next"][1:3], types, 2))
		elif current_page == 20:
			btn_data = [lan_data[user_lan]["back_next"][0], lan_data[user_lan]["back_next"][2]]
			await message.reply("Ok", reply_markup=fun.reply_key(btn_data, types, 2))
		else:
			await message.reply("Ok", reply_markup=fun.reply_key(lan_data[user_lan]["back_next"], types, 2))
	except:
		page_one = fun.find_page("1")
		current_page = 1
		await message.reply("Ok", reply_markup=fun.reply_key(lan_data[user_lan]["back_next"][1:3], types, 2))
	
	if page_one == "Error":
		return await message.answer(lan_data[user_lan]["error_msg"])
	titles = list()
	photos = list()
	stat = True
	count = 0
	for hadis in page_one:
		count += 1
		title = hadis[0]
		url = hadis[1]
		if hadis[-1][0] == "/":
			photo = f"islom.uz{hadis[-1]}"
		else:
			photo = hadis[-1]
			stat = False
		btn_data = {lan_data[user_lan]["read_hadis_btn"]: f"read_hadis_{count}_{len(page_one)}_{url}"}
		btn = fun.get_inline(btn_data, types)
		a = await bot.send_photo(message.chat.id, photo, title, reply_markup=btn)
		if photo[:8] == "islom.uz": 
			titles.append(title)
			photos.append(a["photo"][-1]["file_id"])
	if stat:
		fun.update_photo(titles, photos)
	user_info[str(message.from_user.id)]["current_page"] = current_page
	with open("data/user_info.json", "w") as file:
		json.dump(user_info, file)






back_p1 = [lan_data[i]["back_side"][0] for i in lan_data]
back_p = [lan_data[i]["back_next"][0] for i in lan_data]
next_p = [lan_data[i]["back_next"][1] for i in lan_data]
buttons = back_p1 + back_p + next_p
@dp.message_handler(lambda message: message.text in buttons)
async def process_age(message: types.Message):
	user_lan = user_info[str(message.from_user.id)]["language"]
	current_page = user_info[str(message.from_user.id)]["current_page"]
	direction = message.text
	if current_page != 20 and direction not in back_p1:
		for i in range(1, 13):
			await bot.delete_message(message.chat.id, message.message_id - i)
	elif current_page == 20 and direction not in back_p1:
		for i in range(1, 7):
			await bot.delete_message(message.chat.id, message.message_id - i)
	if direction in back_p1 and current_page == 1:
		await message.reply("Ok", reply_markup=fun.reply_key(lan_data[user_lan]["back_next"][1:3], types, 2))
	elif direction in back_p1 and current_page == 21:
		btn_data = [lan_data[user_lan]["back_next"][0], lan_data[user_lan]["back_next"][2]]
		await message.reply("Ok", reply_markup=fun.reply_key(btn_data, types, 2))
	elif direction in back_p1 and 1<current_page<21:
		await message.reply("Ok", reply_markup=fun.reply_key(lan_data[user_lan]["back_next"], types, 2))
	elif direction in [lan_data[i]["back_next"][0] for i in lan_data] and current_page == 2:
		current_page = 1
		await message.reply("Ok", reply_markup=fun.reply_key(lan_data[user_lan]["back_next"][1:3], types, 2))
	elif direction in [lan_data[i]["back_next"][1] for i in lan_data] and current_page == 20:
		btn_data = [lan_data[user_lan]["back_next"][0], lan_data[user_lan]["back_next"][2]]
		await message.reply("Ok", reply_markup=fun.reply_key(btn_data, types, 2))
		current_page = 21
	else:
		await message.reply("Ok", reply_markup=fun.reply_key(lan_data[user_lan]["back_next"], types, 2))
		if direction in [lan_data[i]["back_next"][1] for i in lan_data]:
			current_page += 1
		else:
			current_page -= 1
	page_one = fun.find_page(current_page)
	if page_one == "Error":
		return await message.answer(lan_data[user_lan]["error_msg"])
	titles = list()
	photos = list()
	stat = True
	count = 0
	for hadis in page_one:
		count += 1
		title = hadis[0]
		url = hadis[1]
		if hadis[-1][0] == "/":
			photo = f"islom.uz{hadis[-1]}"
		else:
			photo = hadis[-1]
			stat = False
		btn_data = {lan_data[user_lan]["read_hadis_btn"]: f"read_hadis_{count}_{len(page_one)}_{url}"}
		btn = fun.get_inline(btn_data, types)
		a = await bot.send_photo(message.chat.id, photo, title, reply_markup=btn)
		if photo[:8] == "islom.uz": 
			titles.append(title)
			photos.append(a["photo"][-1]["file_id"])
	if stat:
		fun.update_photo(titles, photos)
	user_info[str(message.from_user.id)]["current_page"] = current_page
	with open("data/user_info.json", "w") as file:
		json.dump(user_info, file)




#admin adding new quran audio to the db
@dp.message_handler(state=Form.quran, content_types=["photo"])
async def adding_quran_audio(message: types.Message, state: FSMContext):
	photo = message.photo[-1].file_id
	qari_name = message.caption
	for lan in lan_data:
		lan_data[lan]["names"].append(qari_name)
	with open("data/languages.json", "w") as file:
		json.dump(lan_data, file)
	pictures[qari_name] = photo
	with open("data/pictures.json", "w") as file:
		json.dump(pictures, file)
	await state.finish()
	await message.answer("✅")


if __name__ == '__main__':
	executor.start_polling(dp)