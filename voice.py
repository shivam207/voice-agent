from kokoro import KPipeline
# from IPython.display import display, Audio
import soundfile as sf
import numpy as np
import io
# 🇺🇸 'a' => American English, 🇬🇧 'b' => British English
# 🇯🇵 'j' => Japanese: pip install misaki[ja]
# 🇨🇳 'z' => Mandarin Chinese: pip install misaki[zh]

pipeline = KPipeline(lang_code='a')

def text_to_speech(text):
    generator = pipeline(
    text, voice='af_heart', # <= change voice here
    speed=1, split_pattern=r'\n+'
    )
    audio_chunks = []
    for i, (gs, ps, audio) in enumerate(generator):
        audio_chunks.append(audio)
    
    full_audio = np.concatenate(audio_chunks)
    rate = 24000
    sf.write(f'output.wav', full_audio, 24000) # save each audio file
    
    with io.BytesIO() as bio:
        sf.write(bio, full_audio, rate, format='WAV')  # Write WAV to BytesIO
        audio_bytes = bio.getvalue()

    return audio_bytes
