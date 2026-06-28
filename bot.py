import os
import telebot
from vieneu import Vieneu

# Lấy token từ biến môi trường (an toàn bảo mật, không ghi trực tiếp token vào mã)
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Khởi tạo mô hình VieNeu-TTS (sẽ tự động chạy trên CPU của GitHub)
print("Đang tải mô hình VieNeu-TTS...")
tts = Vieneu()
print("Mô hình đã sẵn sàng!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Tin nhắn chào mừng khi bạn bấm /start
    bot.reply_to(message, "Chào bạn! Gửi lệnh /tts kèm theo văn bản để tôi đọc cho bạn nghe nhé. Ví dụ: /tts Xin chào bạn.")

@bot.message_handler(commands=['tts'])
def handle_tts(message):
    # Lấy nội dung sau lệnh /tts
    text = message.text.replace('/tts', '').strip()

    if not text:
        bot.reply_to(message, "Bạn chưa nhập văn bản. Vui lòng dùng lệnh: /tts <nội dung>")
        return

    bot.reply_to(message, f"Đang tạo giọng nói cho: '{text}'. Vui lòng đợi một chút...")

    try:
        # Tạo file audio từ văn bản
        output_file = "output.wav"
        audio = tts.infer(text)
        tts.save(audio, output_file)

        # Gửi file âm thanh lại cho người dùng trên Telegram
        with open(output_file, 'rb') as audio_file:
            bot.send_audio(message.chat.id, audio_file)

        # Xóa file sau khi gửi xong để dọn dẹp bộ nhớ
        os.remove(output_file)
    except Exception as e:
        bot.reply_to(message, f"Có lỗi xảy ra trong quá trình tạo giọng nói: {str(e)}")

print("Bot đang chạy... Hãy nhắn tin cho bot trên Telegram!")
# Giữ cho bot chạy liên tục để lắng nghe tin nhắn
bot.infinity_polling()
