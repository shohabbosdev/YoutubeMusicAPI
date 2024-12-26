import requests
import telebot  
from telebot.types import InlineKeyboardButton
from telegram_bot_pagination import InlineKeyboardPaginator  
from config import key, token

bot = telebot.TeleBot(token, parse_mode='html')

# Foydalanuvchi qidiruvlarini saqlash uchun dictionary
user_searches = {}

def search_songs(singer):
    try:
        url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&key={key}&type=video&maxResults=50&q={singer}'
        response = requests.get(url)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        if not data.get('items'):
            return None
        sanagich=0
        results = []
        for item in data['items']:
            video_id = item['id'].get('videoId', '')
            snippet = item.get('snippet', {})
            
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            title = snippet.get('title', 'Noma\'lum')
            published_at = snippet.get('publishedAt', '').split('T')[0]
            
            page_content = f"<b>{sanagich+1}.</b> 🎵 <b>{title}</b>\n"
            page_content += f"📅 Chiqarilgan sana: {published_at}\n"
            page_content += f"🔗 <a href='{video_url}'>YouTube'da ko'rish</a>"
            sanagich+=1
            results.append(page_content)
            
        return results
        
    except Exception as e:
        return None

@bot.message_handler(commands=['start'])  
def start(message):
    welcome_text = """
🎵 <b>Musiqa Qidirish Botiga Xush Kelibsiz!</b>

Qo'shiq yoki qo'shiqchi nomini yuboring va men sizga YouTube'dan topilgan natijalarni ko'rsataman.

Masalan:
- Uzmir
- Ummon
- Yulduz Usmonova
- Xamdam Sobirov
"""
    bot.send_message(message.chat.id, welcome_text)


def send_song_page(message, results, page=1):
    paginator = InlineKeyboardPaginator(
        len(results),
        current_page=page,
        data_pattern='song#{page}'
    )

    paginator.add_after(
        InlineKeyboardButton('🔍 Yangi qidiruv', callback_data='new_search')
    )

    bot.send_message(
        message.chat.id,
        results[page-1],
        reply_markup=paginator.markup,
        disable_web_page_preview=False
    )
    

@bot.callback_query_handler(func=lambda call: call.data.split('#')[0]=='song')
def songs_page_callback(call):
    # Foydalanuvchining qidiruv natijalarini olish
    results = user_searches.get(call.message.chat.id)
    
    if not results:
        bot.answer_callback_query(call.id, "Qidiruv natijasi topilmadi. Iltimos, qaytadan qidiring.")
        return

    page = int(call.data.split('#')[1])
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    send_song_page(call.message, results, page)

@bot.callback_query_handler(func=lambda call: call.data == 'new_search')
def new_search_callback(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    # Foydalanuvchining eski qidiruv natijalarini o'chirish
    if call.message.chat.id in user_searches:
        del user_searches[call.message.chat.id]
    bot.send_message(call.message.chat.id, "Yangi qo'shiq yoki ijrochi nomini yuboring:")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if len(message.text) < 2:
        bot.reply_to(message, "Iltimos, kamida 2 ta so'z kiriting!")
        return
        
    searching_message = bot.send_message(
        message.chat.id,
        "🔍 Qidirilmoqda..."
    )
    
    results = search_songs(message.text)
    
    try:
        bot.delete_message(message.chat.id, searching_message.message_id)
    except:
        pass
        
    if not results:
        bot.send_message(
            message.chat.id,
            "❌ Qo'shiqlar topilmadi yoki xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
        )
        return
    
    # Foydalanuvchining qidiruv natijalarini saqlash
    user_searches[message.chat.id] = results
    send_song_page(message, results)

def main():
    try:
        print("Bot ishga tushdi...")
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        main()

if __name__ == '__main__':
    main()