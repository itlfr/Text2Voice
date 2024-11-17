from flask import Flask, render_template, request, redirect, url_for
from gtts import gTTS
from langdetect import detect  # استيراد مكتبة langdetect
import os
import time
import threading

app = Flask(__name__)

# تأكد من وجود المجلد static/audio
if not os.path.exists("static/audio"):
    os.makedirs("static/audio")

# دالة لحذف الملفات القديمة
def delete_old_audio_files():
    while True:
        # الحصول على الوقت الحالي
        current_time = time.time()

        # البحث عن الملفات في مجلد الصوتيات
        for filename in os.listdir("static/audio"):
            file_path = os.path.join("static/audio", filename)
            if os.path.isfile(file_path):
                # الحصول على وقت التعديل الأخير للملف
                file_creation_time = os.path.getmtime(file_path)
                
                # إذا كان الملف قديم (أكثر من ساعه)، يتم حذفه
                if current_time - file_creation_time > 60*60:
                    os.remove(file_path)
                    print(f"Deleted old file: {filename}")

        # الانتظار ساعه قبل الفحص مرة أخرى
        time.sleep(60*60)

# بدء عملية الحذف في الخلفية عند بدء السيرفر
def start_cleanup_thread():
    cleanup_thread = threading.Thread(target=delete_old_audio_files)
    cleanup_thread.daemon = True  # التأكد من أن الخيط لا يمنع السيرفر من الإغلاق
    cleanup_thread.start()

# تشغيل الحذف التلقائي عند بدء السيرفر
start_cleanup_thread()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # استلام النص واللغة من النموذج
        text = request.form['text']
        language = request.form['language']
        
        # إذا اختار المستخدم "auto"، يتم اكتشاف اللغة تلقائيًا
        if language == 'auto':
            try:
                detected_language = detect(text)
            except:
                detected_language = 'en'  # في حالة حدوث خطأ، افترض أن اللغة هي الإنجليزية
        else:
            detected_language = language

        # إعادة توجيه المستخدم إلى صفحة الانتظار مع النص واللغة المكتشفة
        return render_template('loading.html', text=text, language=detected_language)
    
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    start_time = time.time()  # بداية قياس الوقت
    text = request.form['text']
    language = request.form['language']
    tts = gTTS(text=text, lang=language)
    audio_file = f"static/audio/output_{int(time.time())}.mp3"
    tts.save(audio_file)
    processing_time = round(time.time() - start_time, 2)  # نهاية القياس
    return redirect(url_for('result', audio_file=audio_file, processing_time=processing_time))


@app.route('/result')
def result():
    audio_file = request.args.get('audio_file')
    processing_time = request.args.get('processing_time')

    # تحقق مما إذا كان الملف الصوتي موجودًا
    if not os.path.exists(audio_file):
        # إذا كان الملف غير موجود، إعادة توجيه المستخدم إلى صفحة الإشعار
        return render_template('file_not_found.html')

    return render_template('result.html', audio_file=audio_file, processing_time=processing_time)

if __name__ == "__main__":
	app.run(host='0.0.0.0',port=8080,debug=True)