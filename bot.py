import cv2
import pytesseract

import requests
from bs4 import BeautifulSoup as BS

import logging

from aiogram import Bot, executor, Dispatcher, types

from config import API_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def get_words(text):
    words = set(map(lambda w: w.lower(), text.split()))
    words = list(filter(lambda w: w.isalpha() and len(w) > 1, words))
    return words


def get_text_from_photo(photo_path):
    # открытие фото
    img = cv2.imread(photo_path)
    # преобразование в rgb
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # показать фото:
    # cv2.imshow('Result', img)
    # cv2.waitKey(0)
    config = r'--oem 3 --psm 6'
    return pytesseract.image_to_string(img, config=config)


def parse_translate_audio(word):
    url = f'https://wooordhunt.ru/word/{word}'
    r = requests.get(url)
    html = BS(r.content, 'html.parser')

    title = html.find('title').string
    if title.startswith('Упс'):
        return False

    translate = html.select('.t_inline_en')
    if not len(translate):
        return False
    translate = translate[0].text

    audio_url = html.select('#audio_us source')
    if not audio_url:
        return False
    audio_url = audio_url[0]['src']
    audio_url = f'https://wooordhunt.ru/{audio_url}'
    return {
        'translate': translate,
        'audio_url': audio_url,
    }


def get_photoes_urls(word):
    url = f'https://www.google.com/search?q={word}+image&sxsrf=ALeKk03PhvNT1Rt5OnHd6TnJLh3Ig_grXw:1604484781814&source=lnms&tbm=isch&sa=X&ved=2ahUKEwiXmt7L0-jsAhWyBxAIHTrKA34Q_AUoAXoECAYQAw&biw=1848&bih=981'
    r = requests.get(url)
    html = BS(r.content, 'html.parser')
    images = html.select('img')[1:4]
    return list(map(lambda i: i['src'], images))


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    # reply - ответ на сообщение
    await message.reply("Hi!\nI'm english_cards bot!\n Type /help for know my functions.")


@dp.message_handler(content_types=['photo'])
async def get_sticker_id(photo: types.PhotoSize):
    file_id = photo.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    photo_path = file_info.file_path
    await bot.download_file_by_id(file_id, photo_path)
    
    text_from_photo = get_text_from_photo(photo_path)
    words = get_words(text_from_photo)

    for word in words:
        d = parse_translate_audio(word)
        if d:
            media = []
            photoes = get_photoes_urls(word)

            i = 0
            while i < len(photoes):
                if i == 0:
                    media.append(types.InputMediaPhoto(photoes[i], caption=f'<b>{word}</b> - <i>{d["translate"]}</i>', parse_mode=types.ParseMode.HTML))
                else:
                    media.append(types.InputMediaPhoto(photoes[i]))
                i += 1

            # for photo_url in photoes:
            #     media.append(types.InputMediaPhoto(photo_url, caption=f'<b>{word}</b> - <i>{d["translate"]}</i>', parse_mode=types.ParseMode.HTML))

            # await bot.send_message(chat_id=photo.chat.id, text=f'<b>{word}</b> - <i>{d["translate"]}</i>', parse_mode=types.ParseMode.HTML)
            await bot.send_media_group(chat_id=photo.chat.id, media=media)
            await bot.send_audio(chat_id=photo.chat.id, audio=d['audio_url'])


@dp.message_handler(commands=['group'])
async def process_group_command(message: types.Message):
    media = [types.InputMediaPhoto('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTdHGQK-txQEVDsQbodeD6OCm2d43X2gATUthchIBs0vvTHDD2yJ9kvQjUWKFk&amp;s', caption='<b>apapap</b>', parse_mode=types.ParseMode.HTML)]
    
    media.append(types.InputMediaPhoto('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTdHGQK-txQEVDsQbodeD6OCm2d43X2gATUthchIBs0vvTHDD2yJ9kvQjUWKFk&amp;s'))
    await bot.send_media_group(message.from_user.id, media)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    # print(parse_translate_audio('attention'))
