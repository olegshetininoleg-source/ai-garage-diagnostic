import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template
from scipy.signal import butter, filtfilt, hilbert
from scipy.stats import kurtosis
import telebot
from telebot.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, MenuButtonWebApp

# ==========================================
# 🤖 НАСТРОЙКИ ТЕЛЕГРАМ БОТА
# ==========================================
TOKEN = "8645219490:AAF1s6ePsBJODfRduO9L2s3MbNsAHlbLkkU"
bot = telebot.TeleBot(TOKEN)

# Устанавливаем системную кнопку слева внизу
try:
    bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(type='web_app', text='🛠 AI Scanner', web_app=WebAppInfo(url="https://softhunterpro.com/ai-car-diagnostic-app/"))
    )
except Exception as e:
    pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    inline_markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url="https://softhunterpro.com/ai-car-diagnostic-app/")
    inline_markup.add(InlineKeyboardButton(text="🛠️ Open AI Scanner", web_app=web_app))
    text = "Hello! I am the AI-Garage Assistant 🤖\n\nI can help you diagnose engine noises (belt squeal, valve tick, knocking) and save you $100+ on mechanic fees.\n\nClick the button below to launch our Free Neural Scanner directly!"
    bot.send_message(message.chat.id, text, reply_markup=inline_markup)

@bot.message_handler(content_types=['audio', 'voice', 'document'])
def handle_audio(message):
    inline_markup = InlineKeyboardMarkup()
    inline_markup.add(InlineKeyboardButton(text="Start AI Scan on Website", url="https://softhunterpro.com/ai-car-diagnostic-app/"))
    text = "Got it! 🎧 To process this sound through our full neural network and get specific Amazon part recommendations, please upload it to our web scanner 👇"
    bot.reply_to(message, text, reply_markup=inline_markup)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    inline_markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url="https://softhunterpro.com/ai-car-diagnostic-app/")
    inline_markup.add(InlineKeyboardButton(text="🛠️ Open AI Scanner", web_app=web_app))
    bot.reply_to(message, "Please click the button below to diagnose your engine sound!", reply_markup=inline_markup)


# ==========================================
# ⚙️ НАСТРОЙКИ СЕРВЕРА И НЕЙРОСЕТИ
# ==========================================
app = Flask(__name__)

class EngineAnalyzer:
    def bandpass_filter(self, audio, sr, low=100, high=4000):
        nyq = 0.5 * sr
        b, a = butter(4, [low / nyq, high / nyq], btype='band')
        return filtfilt(b, a, audio)

    def compute_envelope(self, audio):
        analytic = hilbert(audio)
        return np.abs(analytic)

    def process(self, audio, sr=22050):
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.03:
            return {"type": "low_signal", "rpm": 0, "probabilities": { "normal_operation": 0, "belt_squeal": 0, "valve_clatter": 0 }, "recommendation": "Audio signal too low. Please hold your device closer to the engine block."}
        
        filtered = self.bandpass_filter(audio, sr)
        k = kurtosis(filtered)
        env = self.compute_envelope(filtered)
        peak_count = np.sum(env > (np.mean(env) + 2 * np.std(env)))
        freqs = np.fft.rfftfreq(len(audio), d=1 / sr)
        amps = np.abs(np.fft.rfft(audio))
        low_zone = (freqs >= 15) & (freqs <= 50)
        
        if np.any(low_zone):
            base_freq = freqs[low_zone][np.argmax(amps[low_zone])]
            rpm = int((base_freq * 60) / 2)
        else:
            rpm = 800
        
        if rpm < 500 or rpm > 1200: 
            rpm = 825
            
        score_knock = min(max(k, 0) / 5, 0.5) 
        score_knock += min(peak_count / 1000, 0.5)
        prob_knock = int(score_knock * 100)
        
        high_idx = np.searchsorted(freqs, 2000)
        high_energy = np.max(amps[high_idx:]) if len(amps[high_idx:]) > 0 else 0
        snr_ratio = high_energy / (np.mean(amps) + 1e-9)
        prob_squeal = 0
        
        if snr_ratio > 15 and high_energy > 0.2:
            prob_squeal = min(int((snr_ratio / 40) * 100), 95)
            
        prob_normal = max(100 - prob_knock - prob_squeal, 5)
        
        diag_type = "normal_operation"
        rec = "Normal engine operation. No critical noises detected."
        amazon_query = "obd2+scanner+diagnostic+tool"
        
        if prob_knock > 45 and prob_knock > prob_squeal:
            diag_type = "valve_clatter"
            rec = "Metallic knocking detected. Inspect hydraulic lifters or valve clearances."
            amazon_query = "hydraulic+lifter+additive+treatment"
        elif prob_squeal > 45:
            diag_type = "belt_squeal"
            rec = "High-frequency squeal detected. Check serpentine/alternator belt tension."
            amazon_query = "serpentine+belt+conditioner+spray"

        # Формируем твою личную партнерскую ссылку
        affiliate_tag = "amazon014e11-20"
        amazon_link = f"https://www.amazon.com/s?k={amazon_query}&tag={affiliate_tag}"

        return {
            "type": diag_type, 
            "rpm": rpm, 
            "probabilities": {"normal_operation": prob_normal, "belt_squeal": prob_squeal, "valve_clatter": prob_knock}, 
            "recommendation": rec,
            "amazon_link": amazon_link
        }

analyzer = EngineAnalyzer()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    try:
        with wave.open(file, 'rb') as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
            if wf.getnchannels() > 1:
                audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)
            sr = wf.getframerate()
        return jsonify(analyzer.process(audio, sr))
    except Exception as e:
        return jsonify({"error": f"Error reading file: {str(e)}"}), 500

# ==========================================
# 🌐 МАГИЯ WEBHOOK (СВЯЗЬ ТЕЛЕГРАМА И СЕРВЕРА)
# ==========================================
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/set_webhook")
def webhook():
    bot.remove_webhook()
    webhook_url = request.host_url + TOKEN
    bot.set_webhook(url=webhook_url)
    return f"✅ Webhook успешно установлен! Бот слушает сервер.", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
