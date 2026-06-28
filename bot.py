import os
import telebot
from vieneu import Vieneu

# Lấy token từ biến môi trường
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Khởi tạo mô hình VieNeu-TTS (Mặc định là v3 Turbo)
print("Đang tải mô hình VieNeu-TTS v3 Turbo...")
tts = Vieneu()
print("Mô hình đã sẵn sàng!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Chào bạn! Tôi là bot Text-to-Speech được hỗ trợ bởi mô hình **VieNeu-TTS v3 Turbo**.\n\n"
        "🛠 **Các lệnh khả dụng:**\n"
        "👉 `/voices` : Xem danh sách các giọng đọc hiện có.\n"
        "👉 `/tts <Nội dung>` : Đọc văn bản bằng giọng mặc định (Bình An).\n"
        "👉 `/tts <Tên giọng> | <Nội dung>` : Đọc văn bản bằng giọng bạn chọn.\n\n"
        "💡 *Ví dụ:* `/tts Xuân Vĩnh | Xin chào mọi người`"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['voices'])
def handle_voices(message):
    try:
        # Lấy danh sách giọng từ mô hình
        voices = tts.list_preset_voices()
        reply_text = "🎙 **Danh sách giọng nói có sẵn:**\n\n"
        
        for label, voice_id in voices:
            reply_text += f"🔹 {label} (Mã: `{voice_id}`)\n"
            
        reply_text += "\n📌 *Lưu ý:* Gõ đúng Mã (hoặc Tên) để sử dụng giọng nhé!"
        bot.reply_to(message, reply_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"Không thể tải danh sách giọng nói: {str(e)}")

@bot.message_handler(commands=['tts'])
def handle_tts(message):
    # Lấy nội dung sau lệnh /tts
    raw_text = message.text.replace('/tts', '').strip()

    if not raw_text:
        bot.reply_to(message, "⚠️ Bạn chưa nhập văn bản. Hãy dùng lệnh: `/tts <nội dung>` hoặc `/tts <Tên giọng> | <nội dung>`", parse_mode='Markdown')
        return

    voice_choice = None
    text_to_speak = raw_text

    # Kiểm tra xem người dùng có truyền tên giọng qua dấu '|' không
    if '|' in raw_text:
        parts = raw_text.split('|', 1)
        voice_choice = parts[0].strip()
        text_to_speak = parts[1].strip()

    if voice_choice:
        bot.reply_to(message, f"⏳ Đang tạo âm thanh với giọng **{voice_choice}**...\n📝 Nội dung: '{text_to_speak}'", parse_mode='Markdown')
    else:
        bot.reply_to(message, f"⏳ Đang tạo âm thanh bằng giọng **Mặc định**...\n📝 Nội dung: '{text_to_speak}'", parse_mode='Markdown')

    try:
        output_file = "output.wav"
        
        # Nếu có voice_choice thì truyền vào, không thì dùng mặc định
        if voice_choice:
            audio = tts.infer(text=text_to_speak, voice=voice_choice)
        else:
            audio = tts.infer(text=text_to_speak)
            
        tts.save(audio, output_file)

        # Gửi file âm thanh lại cho người dùng
        with open(output_file, 'rb') as audio_file:
            bot.send_audio(message.chat.id, audio_file)

        # Xóa file sau khi gửi xong
        os.remove(output_file)
    except Exception as e:
        bot.reply_to(message, f"❌ Có lỗi xảy ra. Vui lòng kiểm tra lại Tên giọng hoặc Nội dung.\nLỗi chi tiết: `{str(e)}`", parse_mode='Markdown')

print("Bot đang chạy... Hãy nhắn tin cho bot trên Telegram!")
bot.infinity_polling()
