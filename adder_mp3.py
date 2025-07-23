from pydub import AudioSegment

# Загружаем 1-секундный mp3
one_sec = AudioSegment.from_mp3("tuturu.mp3")

# Повторяем 5 раз
five_sec = one_sec * 4

# Сохраняем
five_sec.export("tuturu_4sec.mp3", format="mp3", bitrate="96k")

print("✅ Склеено и сохранено в beep_5sec.mp3")
