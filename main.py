import asyncio
import os
from deep_translator import GoogleTranslator
import wikipedia
from aiogram import Bot, Dispatcher, F,types
from aiogram.types import Message,ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,FSInputFile
from gtts import gTTS
from aiogram.types import BufferedInputFile
from google import genai
from dotenv import load_dotenv
from rembg import remove
from PIL import Image
import imageio_ffmpeg as ffmpeg
import uuid
from moviepy import VideoFileClip
import io
import qrcode
import logging
import yt_dlp
import imageio_ffmpeg as ffmpeg

ffmpeg_path = ffmpeg.get_ffmpeg_exe()


load_dotenv()

TOKEN = os.getenv('TOKEN')

bot = Bot(token=TOKEN)
wikipedia.set_lang('uz')
dp = Dispatcher()
GEMINI_API_KEY = 'AIzaSyDhG9IkBsn6SNyS6j-FvNqaWaJkgvFzPJg'

#foydalanuvchilarni saqlash
user_mode = {}
user_images = {}
user_lang = {}
user_state = {}
client = genai.Client(api_key=GEMINI_API_KEY)


menyu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Aloqa"), KeyboardButton(text="menyu")],         
              ],
    resize_keyboard=True
)

wiki_lang = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Rus tili',callback_data='lang_ru')],
    [InlineKeyboardButton(text='Inglis tili',callback_data='lang_en')],
    [InlineKeyboardButton(text='Nemis tili',callback_data='lang_ne')],
    [InlineKeyboardButton(text='Yapon tili',callback_data='lang_ja')],
    [InlineKeyboardButton(text='Arab tili',callback_data='lang_ar')] ])

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Wikipedia', callback_data='wiki')],
    [InlineKeyboardButton(text=' Tarjimon', callback_data='nima')],
    [InlineKeyboardButton(text='▶️ youtubdan videoni yuklash',callback_data="youtube")],
    [InlineKeyboardButton(text="🧼 Fonni olib tashlash",callback_data="rbg")],
    [InlineKeyboardButton(text="👩‍💻 qrcode yaratish",callback_data="qr")],
    [InlineKeyboardButton(text="🎵 Musiqani topish",callback_data='music')]
])



lang = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Inglis tili',callback_data='inglis')],
    [InlineKeyboardButton(text="Arab tili",callback_data='artili')],
    [InlineKeyboardButton(text='Rus tili',callback_data='ruscha')],
    [InlineKeyboardButton(text="Nemis tili",callback_data="nemis")],
    [InlineKeyboardButton(text="Yapon tili",callback_data="yapon")]
])


wikipedia.set_lang('uz')
@dp.message(F.text == '/start')
async def start(message: Message):
    await message.answer(f"Assalomu aleykum {message.from_user.full_name}", reply_markup=menyu)

@dp.message(F.text == "menyu")
async def yordam(message: Message):
    await message.answer("Vazifani tanlang", reply_markup=keyboard)

#wikipedia
@dp.callback_query(F.data == 'wiki')
async def wiki_mode(callback: CallbackQuery):
    user_state[callback.from_user.id] = 'wiki'
    await callback.message.answer_photo(photo='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQKJMsaA28A32PrOKnj_PqUF1PezvB1bAygtQ&s')
    await callback.message.answer("Wikipedia rejimi faollashdi. Mavzu kiriting:",reply_markup=wiki_lang)
    await callback.answer()


@dp.message(lambda message: user_state.get(message.from_user.id) == 'wiki')
async def wikipedia_uz(message: Message):
    await message.answer("Wikipedia qidirilmoqda...")
    try:
        resport = wikipedia.summary(message.text, sentences=2)
        await message.answer(resport)
    except:
        await message.answer("Kiritilgan mavzu topilmadi.")
    user_state[message.from_user.id] = None 
#tarjimon
@dp.callback_query(F.data == 'lang_ru')
async def lang_ru(callback: CallbackQuery):
    wikipedia.set_lang('ru')
    user_lang[callback.from_user.id] = 'ru'
    await callback.message.edit_text("siz rus tilini tanladingiz 🇷🇺")
    await callback.answer()     

@dp.callback_query(F.data == 'lang_en')
async def lang_ens(callback:CallbackQuery):
    wikipedia.set_lang('en')
    user_lang[callback.from_user.id] = 'en'
    await callback.message.edit_text("siz ingliz tilini tanlandingiz 🇺🇸")
    await callback.answer()

@dp.callback_query(F.data == "lang_ne")
async def lang_ne(callback:CallbackQuery):
    wikipedia.set_lang('ne')
    user_lang[callback.from_user.id] = 'ne'
    await callback.message.edit_text("siz nemis tilini tanladingiz 🇩🇪")


@dp.callback_query(F.data == "lang_ja")
async def lang_ja(callback:CallbackQuery):
    wikipedia.set_lang('ja')
    user_lang[callback.from_user.id] = 'ja'
    await callback.message.edit_text("siz yaponiya tilini tanladingiz 🇯🇵")

@dp.callback_query(F.data == 'lang_ar')
async def lang_ar(callback:CallbackQuery):
    wikipedia.set_lang('ar')
    user_lang[callback.from_user.id] = 'ar'
    await callback.message.edit_text("siz arab tili tanladingiz 🇪🇭")

@dp.callback_query(F.data == "nima")
async def tarjimon_mode(callback: CallbackQuery):
    await callback.message.answer(f"tilni tanlang",reply_markup=lang)

#wikipedia
@dp.callback_query(F.data == "ruscha")
async def rus(callback:CallbackQuery):
    user_state[callback.from_user.id] = "ruscha"
    await callback.message.answer_photo(photo="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRUl1238XhZH88BXkg2RQDJES2OYc7dFq1LvQ&s",caption="Rus tili ishga tushdi")
    await callback.message.answer("tajimayi rejimi ishga tushdi (UZ -> RU) foalashdi")
    await callback.answer()

@dp.message(lambda message: user_state.get(message.from_user.id) == "ruscha")
async def rusch(message:Message):
    try:
        translation = GoogleTranslator(source='auto',target='ru').translate(message.text)
        await message.answer(f"tarjimon: \n {translation}")
        tts = gTTS(text=translation,lang='ru')
        tts.save("voice.mp3")
        audio = FSInputFile("voice.mp3")
        await message.answer_audio(audio)
    except:
        await message.answer("tarjimada xatolik")

@dp.callback_query(F.data == "nemis")
async def nemis(callback:CallbackQuery):
    user_state[callback.from_user.id] = "nemis"
    await callback.message.answer_photo(photo="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQacIt2DPCU6KNY9lAJATGR27QGYKvQ5fs2mQ&s",caption="Nemis tili ishga tushdi")
    await callback.message.answer("tarjima ishga tushdi (UZ -> NEMIS) foalshdi")
    await callback.answer()
@dp.message(lambda message: user_state.get(message.from_user.id) == "nemis")
async def nemis(message:Message):
    try:
        translation = GoogleTranslator(source='auto',target='de').translate(message.text)
        await message.answer(f"tarjimon: \n {translation}")
        tts = gTTS(text=translation,lang='de')
        tts.save("voise.mp3")
        audio = FSInputFile("voise.mp3")
        await message.answer_audio(audio)
    except:
        await message.answer("tarjimada xatolik")

@dp.callback_query(F.data == "yapon")
async def yapan(callback:CallbackQuery):
    user_state[callback.from_user.id] = "yapon"
    await callback.message.answer_photo(photo="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXWpp0Ms1XTfivKpVnyBrbB0YtAI3fZGLgGQ&s",caption="yapon tili ishga tushdi")
    await callback.message.answer("tarjima ishga tushdi (UZ -> YAPON) foalshdi")
    await callback.answer()
@dp.message(lambda message: user_state.get(message.from_user.id) == "yapon")
async def yapon(message:Message):
    try:
        translation = GoogleTranslator(source='auto',target='ja').translate(message.text)
        await message.answer(f"tarjimon: \n {translation}")
        tts = gTTS(text=translation,lang='ja')
        tts.save("voise.mp3")
        audio = FSInputFile("voise.mp3")
        await message.answer_audio(audio)
    except:
        await message.answer("tarjimada xatolik")

@dp.callback_query(F.data == "inglis")
async def inglis(callback:CallbackQuery):
    user_state[callback.from_user.id] = 'inglis'
    await callback.message.answer_photo(photo='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSfTuQzpDQyA07GTh8u-tgixSwDhgRMZYC9qw&s',caption="tarjimon tili inglis tili ")
    await callback.message.answer("tarjima (UZ -> ING)")
    await callback.answer()

@dp.message(lambda message: user_state.get(message.from_user.id) == 'inglis')
async def inglis(message:Message):
    try:
        translation = GoogleTranslator(source='auto',target='en').translate(message.text)
        await message.answer(f'tarjimon \n {translation}')
        tts = gTTS(text=translation,lang='en')
        tts.save("voise.mp3")
        audio = FSInputFile("voise.mp3")
        await message.answer_audio(audio)
    except:
        await message.answer("tarjimada xatolik")

@dp.callback_query(F.data == 'artili')
async def arab_call(callback:CallbackQuery):
    user_state[callback.from_user.id] = 'artili'
    await callback.message.answer_photo(photo='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6ZPIR9rYhCI2WJK4SjCil-GZ6UfXsMOVzLQ&s',caption=f'tarjimon uzbek tili')
    await callback.message.answer("tarjimon (UZ -> ARAB TILI) ")
    await callback.answer()
@dp.message(lambda message: user_state.get(message.from_user.id) == 'artili')
async def arab_mess(message:Message):
    try:
        translation = GoogleTranslator(source='auto',target='ar').translate(message.text)
        await message.answer(f'tarjimon \n {translation}')
        tts = gTTS(text=translation,lang='ar')
        tts.save("voise.mp3")
        audio = FSInputFile("voise.mp3")
        await message.answer_audio(audio)
    except:
        await message.answer("tarjimada xatolik")

    
@dp.message(F.text == 'Aloqa')
async def Aloqa(message: Message):
    await message.answer("Aloqa: @Ramziddin0808")

#-------- YOUTUBE -----------
@dp.callback_query(F.data == "youtube")
async def yt_mode(call: CallbackQuery):
    user_state[call.from_user.id] = "youtube"
    await call.message.answer("YouTube link tashlang")
    await call.answer()
#----------- suniy intelekt
@dp.callback_query(F.data == "ai")
async def ai_mode(call: CallbackQuery):
    user_state[call.from_user.id] = "ai"
    await call.message.answer("🤖 AI mode ON. Savol yozing")
    await call.answer()
#--------- MUSIC BOT ---------
@dp.callback_query(F.data == "music")
async def music_mode(call: CallbackQuery):
    user_state[call.from_user.id] = "music"
    await call.message.answer("Video, link yoki audio yubor 🎵")
    await call.answer() 

def extract_audio(file_path: str):
    audio_path = f"{uuid.uuid4()}.mp3"

    video = VideoFileClip(file_path)
    video.audio.write_audiofile(audio_path)

    return audio_path

#------------ QRCODE-----
@dp.callback_query(F.data == "qr")
async def qr_mode(call: CallbackQuery):
    user_state[call.from_user.id] = "qr"
    await call.message.answer("Link va Text yuboring")
    await call.answer()


def make_qr(text: str):
    filename = f"{uuid.uuid4()}.png"
    img = qrcode.make(text)
    img.save(filename)
    return filename

# ---------------- SINGLE MESSAGE HANDLER ----------------
@dp.message()
async def router(message: Message):
    user_id = message.from_user.id
    state = user_state.get(user_id)
    state = user_state.get(user_id)
    # ---------------- AI ----------------
    if state == "ai":
        await message.answer("⏳ O‘ylayapman...")

        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=message.text
            )

            await message.answer(response.text)

        except Exception as e:
            print("ERROR:", e)

            if "429" in str(e):
                await message.answer("⏳ Limit tugadi, keyinroq urin")
            else:
                await message.answer("❌ AI xatolik")

        return
       
    # ---------------- QR ----------------
    if state == "qr":
        try:
            file_path = make_qr(message.text)

            await message.answer_photo(
                photo=FSInputFile(file_path),
                caption="QR tayyor ✅"
            )

            os.remove(file_path)

        except Exception as e:
            print(e)
            await message.answer("❌ QR xatolik")

        return

    # ---------------- YOUTUBE ----------------
    if state == "youtube":
    url = message.text.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        await message.answer("❌ To‘g‘ri YouTube link yubor")
        return

    await message.answer("⏳ Yuklanmoqda...")

    try:
        filename = f"{uuid.uuid4()}.mp4"

        ydl_opts = {
            "format": "best[height<=480]/best",
            "outtmpl": filename,
            "noplaylist": True,
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await message.answer_video(FSInputFile(filename))
        os.remove(filename)

    except Exception as e:
        print("YT ERROR:", e)
        await message.answer(f"❌ Xatolik:\n{str(e)[:200]}")
#-------- MUSIC -----------

    state = user_state.get(message.from_user.id)

    if state != "music":
        return

    await message.answer("⏳ Tekshirilmoqda...")

    try:
        # ---------------- LINK ----------------
        if message.text and message.text.startswith("http"):

            url = message.text

            await message.answer("🔗 Yuklanmoqda,kuting(3-5 minut bo'lishi mumkin)...")

            file_id = str(uuid.uuid4())

            ydl_opts = {
                'format': 'bestaudio[abr<=128]/bestaudio',
                'socket_timeout': 30,
                'outtmpl': f"{file_id}.%(ext)s",
                'ffmpeg_location': ffmpeg_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # 🔥 REAL FILE TOPISH
            audio_file = None
            for f in os.listdir():
                if f.startswith(file_id) and f.endswith(".mp3"):
                    audio_file = f
                    break

            if not audio_file:
                await message.answer("❌ Audio topilmadi")
                return

            await message.answer_audio(
                FSInputFile(audio_file),
                request_timeout=120,
                caption="🎵 Musiqa tayyor"
            )

            os.remove(audio_file)
            return

        # ---------------- FILE ----------------
        file = None

        if message.video:
            file = await bot.download(message.video)

        elif message.audio:
            file = await bot.download(message.audio)

        elif message.voice:
            file = await bot.download(message.voice)

        else:
            await message.answer("❌ Video, audio yoki link yuboring")
            return

        await message.answer("⏳ Fayl ishlanmoqda...")

        await message.answer_document(FSInputFile(file.name))
    except Exception as e:
        print("ERROR:", e)
        await message.answer("❌ Xatolik yuz berdi")
# ---------------- AI ----------------
    if state == "ai":
        await message.answer("⏳ O‘ylayapman...")

        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=message.text
            )

            await message.answer(response.text)

        except Exception as e:
            print("ERROR:", e)

            if "429" in str(e):
                await message.answer("⏳ Limit tugadi, keyinroq urin")
            else:
                await message.answer("❌ AI xatolik")

        return
#---------------- 🧼 Fonni olib tashlash -------
@dp.callback_query(F.data == "rbg")
async def bg_mode(call: CallbackQuery):
    user_id = call.from_user.id
    user_state[user_id] = "rbg"   
    await call.message.answer("🧽 Rasm yuboring, orqa fon olib tashlanadi\n\n⏳ Rasm yuborganingizdan keyin darhol ishlaydi.")
    await call.answer()

    
@dp.message(F.photo)
async def photo_handler(message: Message):
    user_id = message.from_user.id

    # Eng muhim qism — rbg rejimi faol bo'lsa, birinchi navbatda shu ishlasin
    if user_state.get(user_id) == "rbg":
        await message.answer("⏳ ishlanmoqda... Orqa fon olib tashlanmoqda, biroz kuting...")

        try:
            # papka yaratish (xatolik bo'lmasligi uchun)
            os.makedirs("images", exist_ok=True)

            file = await bot.get_file(message.photo[-1].file_id)
            path = f"images/{message.photo[-1].file_id}.jpg"

            await bot.download_file(file.file_path, path)

            img = Image.open(path)
            result = remove(img)

            out = path.replace(".jpg", ".png")
            result.save(out)

            # FSInputFile ishlatish — tavsiya etiladi
            await message.answer_photo(
                photo=FSInputFile(out), 
                caption="✅ Orqa fon olib tashlandi! Tayyor."
            )

            # tozalash
            if os.path.exists(path):
                os.remove(path)
            if os.path.exists(out):
                os.remove(out)

            # rejimni tozalash
            user_state[user_id] = None

        except Exception as e:
            await message.answer(f"❌ Xatolik yuz berdi: {str(e)[:200]}")
            logging.error(f"Background remove error: {e}")
        
        return   # Muhim! Boshqa handlerlarga o'tmasin

    # Eski kodni saqlab qoldim (boshqa holatlar uchun)
    if user_mode.get(user_id) != "rbg":
        await message.answer("Avval menyudan 🧼 Fonni olib tashlash ni bosing")
        return

    await message.answer("⏳ ishlanmoqda...")

    try:
        file = await bot.get_file(message.photo[-1].file_id)
        path = f"images/{message.photo[-1].file_id}.jpg"

        await bot.download_file(file.file_path, path)

        img = Image.open(path)
        result = remove(img)

        out = path.replace(".jpg", ".png")
        result.save(out)

        await message.answer_photo(photo=FSInputFile(out), caption="Tayyor ✅")

        if os.path.exists(path):
            os.remove(path)
        if os.path.exists(out):
            os.remove(out)

    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
        logging.error(e)


async def main():
    print("Bot ishlamoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
