from aiogram import Bot, Dispatcher, executor, types, exceptions
from aiogram.utils.exceptions import BadRequest
from mcipc.query import Client
import os.path
import hashlib
import asyncio
import os

address = os.getenv('ADDRESS')
port = os.getenv('PORT')
token = os.getenv('TOKEN')
admin = os.getenv('ADMIN')
channel = os.getenv('CHANNEL')

bot = Bot(token)
dp = Dispatcher(bot)

def create_file(filename):
    dir_exist = os.path.exists('data')
    if dir_exist is False:
        os.mkdir('data')
    file_exists = os.path.isfile(filename)
    if file_exists is False:
        f = open(filename, 'w')
        
def get_last_id():
    with open('data/lastid.txt', 'r') as f:
        return f.read() 

def get_last_message():
    with open('data/lastmsg.txt', 'r') as f:
        return f.read()

def get_online_players():
    with Client(address, int(port)) as client:
        full_stats = client.stats(full=True)
        return full_stats['players']

def get_message():
    message = 'Players are now online:\n\n'
    players = get_online_players()
    if len(players) == 0:
        return f'{message}No one is playing now...'        
    else:
        for i, name in enumerate(players, 1):
            message += f'{str(i)}. {name}\n'
        return message[:-1]

@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    if message.chat.id == int(admin):
        await message.reply(text=f'The bot is working.\nCurrent message_id — {get_last_id()}.')
        msg = await bot.send_message(chat_id=channel, text='Message to edit...')
        with open('data/lastid.txt', 'w') as f:
            f.write(str(msg.message_id))
    else:
        await message.reply(text="Sorry, you are not an admin.")

@dp.inline_handler()
async def inline(inline_query: types.InlineQuery):
    input_content = types.InputTextMessageContent(get_message())
    result_id: str = hashlib.md5(get_message().encode()).hexdigest()
    item = types.InlineQueryResultArticle(
        id=result_id,
        title=f'Players online: {len(get_online_players())}',
        input_message_content=input_content)
    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)

async def update_message():
    last_id = get_last_id()
    while True:
        try:
            await asyncio.sleep(120)
            if get_message() != get_last_message():
                msg = await bot.edit_message_text(text=get_message(), chat_id=channel, message_id=last_id)
                with open('data/lastmsg.txt', 'w') as f:
                    f.write(str(msg.text))
                continue
        except BadRequest:
            last_id = get_last_id()
            await bot.send_message(chat_id=admin, text="An error occurred.\nClick /start to fix it. Maybe it won't help.")
            await asyncio.sleep(600)

async def on_startup(_):
    asyncio.create_task(update_message())
            
if __name__ == '__main__':
    create_file('data/lastid.txt')
    create_file('data/lastmsg.txt')
    executor.start_polling(dp, on_startup=on_startup)