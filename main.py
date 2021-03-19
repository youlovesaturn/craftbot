from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import BadRequest
from mcipc.query import Client
import aiofiles
import asyncio
import os.path
import hashlib
import os

address = os.getenv('ADDRESS')
port = os.getenv('PORT')
token = os.getenv('TOKEN')
admin = os.getenv('ADMIN')
channel = os.getenv('CHANNEL')

bot = Bot(token)
dp = Dispatcher(bot)

async def create_file(filename):
    dir_exist = os.path.exists('data')
    if dir_exist is False:
        os.mkdir('data')
    file_exists = os.path.isfile(filename)
    if file_exists is False:
        await aiofiles.open(filename, 'w')

async def read_from_file(filename):
    async with aiofiles.open(filename, 'r') as f:
        return await f.read() 

async def write_to_file(filename, text):
    async with aiofiles.open(filename, 'w') as f:
        await f.write(text)

async def get_online_players():
    with Client(address, int(port)) as client:
        full_stats = client.stats(full=True)
        await asyncio.sleep(0)
        return full_stats['players']

async def get_message():
    message = 'Players are now online:\n\n'
    players = await get_online_players()
    if len(players) == 0:
        return f'{message}No one is playing now...'        
    else:
        for i, name in enumerate(players, 1):
            message += f'{str(i)}. {name}\n'
        return message[:-1]

@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    if message.chat.id == int(admin):
        await message.reply(text='The bot is working.')
        msg = await bot.send_message(chat_id=channel,
                                     text='Message to edit...',
                                    )
        await write_to_file('data/lastid.txt', str(msg.message_id))
    else:
        await message.reply(text="Sorry, you are not an admin.")

@dp.inline_handler()
async def inline(inline_query: types.InlineQuery):
    message = await get_message()
    online_players = await get_online_players()
    input_content = types.InputTextMessageContent(message)
    result_id: str = hashlib.md5(message.encode()).hexdigest()
    item = types.InlineQueryResultArticle(id=result_id,
                                          title=f'Players online: {len(online_players)}',
                                          input_message_content=input_content,
                                         )
    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)

async def update_message():
    last_id = await read_from_file('data/lastid.txt')
    while True:
        try:
            await asyncio.sleep(120)
            message = await get_message()
            last_message = await read_from_file('data/lastmsg.txt')
            if message != last_message:
                msg = await bot.edit_message_text(text=message,
                                                  chat_id=channel,
                                                  message_id=last_id,
                                                 )
                await write_to_file('data/lastmsg.txt', str(msg.text))
                continue
        except BadRequest:
            await bot.send_message(chat_id=admin,
                                   text="An error occurred.\nClick /start to try to fix it.",
                                  )
            last_id = await read_from_file('data/lastid.txt')
            await asyncio.sleep(600)

async def on_startup(_):
    await create_file('data/lastid.txt')
    await create_file('data/lastmsg.txt')
    asyncio.create_task(update_message())
            
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)