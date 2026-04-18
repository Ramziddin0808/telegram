import asyncio
import os
import uuid
import logging
import io
import qrcode
from dotenv import load_dotenv
from PIL import Image
from rembg import remove
from deep_translator import GoogleTranslator
import wikipedia
from gtts import gTTS
import yt_dlp
import imageio_ffmpeg as ffmpeg

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
)

# FFmpeg yo'lini sozlash
ffmpeg_path = ffmpeg.get_ffmpeg_exe()

load_dotenv()
TOKEN = os.getenv('TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') # .env fayliga qo'shishni unutmang

bot = Bot(token=TOKEN)
dp = Dispatcher()
wikipedia.set_lang('uz')

# Foydalanuvchi holatlarini saqlash
user_state = {}
user_lang = {}

# --- KLAVIATURALAR ---
menyu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Aloqa"), KeyboardButton(text="menyu")]],
    resize_keyboard=True
)

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Wikipedia', callback_data='wiki')],
    [InlineKeyboardButton(text=' Tarjimon', callback_data='nima')],
    [InlineKeyboardButton(text='▶️ YouTubedan video', callback_data="youtube")],
    [InlineKeyboardButton(text="🧼 Fonni olib tashlash", callback_data="rbg")],
    [InlineKeyboardButton(text="👩‍💻 QRCode yaratish", callback_data="qr")],
    [InlineKeyboardButton(text="🎵 Musiqani yuklash", callback_data='music')]
])

wiki_lang = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Rus tili', callback_data='lang_ru')],
    [InlineKeyboardButton(text='Ingliz tili', callback_data='lang_en')],
    [InlineKeyboardButton(text='Uzbek tili', callback_data='lang_uz')]
])

lang_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Ingliz tili', callback_data='inglis')],
    [InlineKeyboardButton(text="Arab tili", callback_data='artili')],
    [InlineKeyboardButton(text='Rus tili', callback_data='ruscha')],
    [InlineKeyboardButton(text="Nemis tili", callback_data="nemis")]
])

# --- YORDAMCHI FUNKSIYALAR ---
def make_qr(text: str):
    filename = f"{uuid.uuid4()}.png"
    img = qrcode.make(text)
    img.save(filename)
    return filename

# --- HANDLERLAR ---
@dp.message(F.text == '/start')
async def start(message: Message):
    await message.answer(f"Assalomu aleykum {message.from_user.full_name}!", reply_markup=menyu)

@dp.message(F.text == "menyu")
async def show_menu(message: Message):
    await message.answer("Vazifani tanlang:", reply_markup=keyboard)

@dp.message(F.text == 'Aloqa')
async def contact(message: Message):
    await message.answer("Admin: @Ramziddin0808")

# --- CALLBACKLAR ---
@dp.callback_query(F.data == "qr")
async def qr_mode(call: CallbackQuery):
    user_state[call.from_user.id] = "qr"
    await call.message.answer("QR kod uchun matn yoki link yuboring:")
    await call.answer()

@dp.callback_query(F.data == "rbg")
async def rbg_mode(call: CallbackQuery):
    user_state[call.from_user.id] = "rbg"
    await call.message.answer("🧽 Rasm yuboring, fonni olib tashlayman.")
    await call.answer()

@dp.callback_query(F.data == "wiki")
async def wiki_mode(call: CallbackQuery):
    user_state[call.from_user.id] = "wiki"
    await call.message.answer("Wikipedia uchun mavzu kiriting:", reply_markup=wiki_lang)
    await call.answer()

@dp.callback_query(F.data == "youtube")
async def yt_mode(call: CallbackQuery):
    user_state[call.from_user.id] = "youtube"
    await call.message.answer("YouTube linkini yuboring:")
    await call.answer()

@dp.callback_query(F.data == "music")
async def music_mode(call: CallbackQuery):
    user_state[call.from_user.id] = "music"
    await call.message.answer("YouTube linkini yuboring (MP3 qilib beraman):")
    await call.answer()

@dp.callback_query(F.data == "nima")
async def translate_menu(call: CallbackQuery):
    await call.message.answer("Tarjima tilini tanlang:", reply_markup=lang_buttons)
    await call.answer()

# --- TARJIMON VA WIKI TILLARI ---
@dp.callback_query(F.data.in_({"ruscha", "nemis", "inglis", "artili"}))
async def set_translate_lang(call: CallbackQuery):
    user_state[call.from_user.id] = call.data
    await call.message.answer(f"Rejim faollashdi. Matn yuboring.")
    await call.answer()

@dp.callback_query(F.data.startswith("lang_"))
async def set_wiki_lang(call: CallbackQuery):
    l_code = call.data.split("_")[1]
    wikipedia.set_lang(l_code)
    await call.message.answer(f"Wikipedia tili {l_code} ga o'zgartirildi.")
    await call.answer()

# --- RASM QAYTA ISHLASH (REMBG) ---
@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    if user_state.get(user_id) == "rbg":
        msg = await message.answer("⏳ Ishlanmoqda...")
        try:
            os.makedirs("images", exist_ok=True)
            path = f"images/{message.photo[-1].file_id}.jpg"
            await bot.download(message.photo[-1], destination=path)
            
            img = Image.open(path)
            result = remove(img)
            out_path = path.replace(".jpg", ".png")
            result.save(out_path)
            
            await message.answer_photo(photo=FSInputFile(out_path), caption="Tayyor! ✅")
            os.remove(path)
            os.remove(out_path)
        except Exception as e:
            await message.answer(f"Xatolik: {e}")
        user_state[user_id] = None
    else:
        await message.answer("Rasmni qayta ishlash uchun menyudan 'Fonni olib tashlash'ni tanlang.")

# --- ASOSIY ROUTER (TEXT HANDLER) ---
@dp.message()
async def main_router(message: Message):
    user_id = message.from_user.id
    state = user_state.get(user_id)

    if not message.text: return

    # 1. QR CODE
    if state == "qr":
        qr_file = make_qr(message.text)
        await message.answer_photo(photo=FSInputFile(qr_file), caption="QR kod tayyor!")
        os.remove(qr_file)
        user_state[user_id] = None

    # 2. WIKIPEDIA
    elif state == "wiki":
        await message.answer("🔍 Qidirilmoqda...")
        try:
            summary = wikipedia.summary(message.text, sentences=2)
            await message.answer(summary)
        except:
            await message.answer("Ma'lumot topilmadi.")
        user_state[user_id] = None

    # 3. TARJIMON
    elif state in ["ruscha", "nemis", "inglis", "artili"]:
        targets = {"ruscha": "ru", "nemis": "de", "inglis": "en", "artili": "ar"}
        target_lang = targets[state]
        try:
            trans = GoogleTranslator(source='auto', target=target_lang).translate(message.text)
            await message.answer(f"Tarjima:\n{trans}")
            tts = gTTS(text=trans, lang=target_lang)
            tts.save("voice.mp3")
            await message.answer_audio(audio=FSInputFile("voice.mp3"))
            os.remove("voice.mp3")
        except:
            await message.answer("Tarjimada xatolik.")

    # 4. YOUTUBE VIDEO
    elif state == "youtube":
        if "youtube.com" in message.text or "youtu.be" in message.text:
            msg = await message.answer("⏳ Video yuklanmoqda (480p)...")
            try:
                file_id = str(uuid.uuid4())
                filename = f"{file_id}.mp4"
                ydl_opts = {
                    'extractor_args': {
    'youtube': {
        'player_client': ['android', 'web'],
        'player_skip': ['configs', 'js'],
    }
},
                    'format': 'best[height<=480]/best',
                    'outtmpl': filename,
                    'cookiefile': 'cookies.txt',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'noplaylist': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([message.text])
                
                await message.answer_video(video=FSInputFile(filename), caption="Video tayyor! ✅")
                os.remove(filename)
                await msg.delete()
            except Exception as e:
                await message.answer(f"Xatolik: YouTube blokladi yoki link xato.")
            user_state[user_id] = None

    # 5. MUSIC (MP3)
    elif state == "music":
        if "youtube.com" in message.text or "youtu.be" in message.text:
            msg = await message.answer("🎵 Musiqa tayyorlanmoqda...")
            try:
                file_id = str(uuid.uuid4())
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f"{file_id}.%(ext)s",
                    'cookiefile': 'cookies.txt',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([message.text])
                
                audio_file = f"{file_id}.mp3"
                await message.answer_audio(audio=FSInputFile(audio_file), caption="Musiqa tayyor! 🎵", request_timeout=300)
                os.remove(audio_file)
                await msg.delete()
            except Exception as e:
                await message.answer(f"Xatolik: Musiqani yuklab bo'lmadi.")
            user_state[user_id] = None

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    if not os.path.exists('cookies.txt'):
        print("⚠️ DIQQAT: cookies.txt topilmadi! YouTube funksiyasi ishlamasligi mumkin.")
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
