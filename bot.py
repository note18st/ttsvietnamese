import os
import wave
import telebot
from vieneu import Vieneu

# Lấy token từ biến môi trường
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

print("Đang tải mô hình VieNeu-TTS v3 Turbo...")
tts = Vieneu()
print("Mô hình đã sẵn sàng!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Chào bạn! Tôi là bot Text-to-Speech.\n\n"
        "🛠 **Các lệnh khả dụng:**\n"
        "👉 `/voices` : Xem danh sách giọng có sẵn.\n"
        "👉 `/tts <Nội dung>` : Đọc văn bản.\n"
        "👉 `/tts <Tên giọng> | <Nội dung>` : Đọc bằng giọng bạn chọn.\n"
        "👉 `/podcast <Kịch bản>` : Tạo hội thoại. Cú pháp: `Tên Giọng: Nội dung`.\n"
        "👉 `/clone <Nội dung>` : Reply một tin nhắn thoại để nhân bản giọng."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['voices'])
def handle_voices(message):
    try:
        voices = tts.list_preset_voices()
        reply_text = "🎙 **Danh sách giọng nói có sẵn:**\n\n"
        for label, voice_id in voices:
            reply_text += f"🔹 {label} (Mã: `{voice_id}`)\n"
        bot.reply_to(message, reply_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"Không thể tải danh sách giọng: {str(e)}")

@bot.message_handler(commands=['tts'])
def handle_tts(message):
    raw_text = message.text.replace('/tts', '').strip()
    if not raw_text:
        bot.reply_to(message, "⚠️ Bạn chưa nhập văn bản. Ví dụ: `/tts Xin chào`")
        return

    voice_choice = None
    text_to_speak = raw_text

    if '|' in raw_text:
        parts = raw_text.split('|', 1)
        voice_choice = parts[0].strip()
        text_to_speak = parts[1].strip()

    bot.reply_to(message, f"⏳ Đang tạo âm thanh... Vui lòng đợi.")
    
    try:
        output_file = f"out_tts_{message.chat.id}.wav"
        if voice_choice:
            audio = tts.infer(text=text_to_speak, voice=voice_choice)
        else:
            audio = tts.infer(text=text_to_speak)
            
        tts.save(audio, output_file)

        with open(output_file, 'rb') as audio_file:
            bot.send_audio(message.chat.id, audio_file)
        os.remove(output_file)
    except Exception as e:
        bot.reply_to(message, f"❌ Có lỗi xảy ra: `{str(e)}`")

@bot.message_handler(commands=['podcast'])
def handle_podcast(message):
    script_text = message.text.replace('/podcast', '').strip()
    if not script_text:
        bot.reply_to(message, "⚠️ Bạn chưa nhập kịch bản. Ví dụ:\n`/podcast\nXuân Vĩnh: Nay ăn gì em?\nBình An: Ăn gì cũng được.`", parse_mode='Markdown')
        return

    bot.reply_to(message, "⏳ Đang xử lý kịch bản Podcast. Quá trình này sẽ tạo từng giọng và ghép lại...")
    
    try:
        # Tách kịch bản thành từng dòng
        lines = script_text.split('\n')
        temp_audio_files = []

        # Xử lý từng dòng một
        for index, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Phân tích Tên giọng và Nội dung dựa vào dấu ':'
            if ':' in line:
                parts = line.split(':', 1)
                voice_name = parts[0].strip()
                dialogue = parts[1].strip()
            else:
                # Nếu người dùng quên gõ dấu hai chấm, dùng giọng mặc định
                voice_name = None
                dialogue = line
            
            # Bỏ qua nếu nội dung thoại rỗng
            if not dialogue:
                continue

            temp_file = f"temp_part_{message.chat.id}_{index}.wav"
            
            # Gọi mô hình để tạo âm thanh cho từng câu
            if voice_name:
                audio = tts.infer(text=dialogue, voice=voice_name)
            else:
                audio = tts.infer(text=dialogue)
            
            tts.save(audio, temp_file)
            temp_audio_files.append(temp_file)

        # Ghép tất cả các file âm thanh lại với nhau
        output_file = f"out_podcast_{message.chat.id}.wav"
        with wave.open(output_file, 'wb') as outfile:
            for i, wav_file in enumerate(temp_audio_files):
                with wave.open(wav_file, 'rb') as infile:
                    # Lấy thông số (tần số, số kênh) từ file đầu tiên áp dụng cho file tổng
                    if i == 0:
                        outfile.setparams(infile.getparams())
                    # Ghi dữ liệu âm thanh vào file tổng
                    outfile.writeframes(infile.readframes(infile.getnframes()))

        # Gửi file podcast hoàn chỉnh cho người dùng
        with open(output_file, 'rb') as final_audio:
            bot.send_audio(message.chat.id, final_audio, title="Podcast", performer="VieNeu-TTS")

        # Dọn dẹp bộ nhớ: xóa file tổng và các file tạm thời
        os.remove(output_file)
        for temp_file in temp_audio_files:
            os.remove(temp_file)

    except Exception as e:
        bot.reply_to(message, f"❌ Có lỗi khi tạo podcast: `{str(e)}`")

@bot.message_handler(commands=['clone'])
def handle_clone(message):
    if not message.reply_to_message or not (message.reply_to_message.voice or message.reply_to_message.audio):
        bot.reply_to(message, "⚠️ **Hướng dẫn:** Reply một tin nhắn thoại và gõ `/clone <Nội dung>`", parse_mode='Markdown')
        return

    text_to_speak = message.text.replace('/clone', '').strip()
    if not text_to_speak:
        bot.reply_to(message, "⚠️ Bạn chưa nhập nội dung cần đọc.")
        return

    bot.reply_to(message, "⏳ Đang nhân bản giọng nói...")

    try:
        if message.reply_to_message.voice:
            file_id = message.reply_to_message.voice.file_id
        else:
            file_id = message.reply_to_message.audio.file_id

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        ref_audio_path = f"ref_{message.chat.id}.ogg"
        with open(ref_audio_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        output_file = f"out_clone_{message.chat.id}.wav"
        
        audio = tts.infer(text=text_to_speak, ref_audio=ref_audio_path)
        tts.save(audio, output_file)

        with open(output_file, 'rb') as audio_file:
            bot.send_audio(message.chat.id, audio_file, title="Giọng Clone")

        os.remove(ref_audio_path)
        os.remove(output_file)

    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi nhân bản: `{str(e)}`")

print("Bot đang chạy...")
bot.infinity_polling()
