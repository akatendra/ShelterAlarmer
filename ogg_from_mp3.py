from pydub import AudioSegment

sound = AudioSegment.from_file("Imperskiy_Marsh_Zvezdnye_voyny.mp3")
clip = sound[:4.5 * 1000]  # milliseconds
# clip.export("alert.ogg", format="ogg", codec="libopus", bitrate="64k")
clip.export("alert.mp3", format="mp3", bitrate="96k")
# sound.export("alert.ogg", format="ogg", codec="libopus", bitrate="64k")