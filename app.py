from flask import Flask, request, jsonify
import os
import json
from datetime import datetime, timezone
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("ERROR: GROQ_API_KEY not found! Please set it in your environment variables.")


client = Groq(api_key=api_key)


CHAT_LOG_FILE = os.path.join(os.getcwd(), 'chat_log.jsonl')

def save_chat_log(user_message, assistant_message):
    chat_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_message": user_message,
        "assistant_message": assistant_message
    }
    with open(CHAT_LOG_FILE, 'a') as f:
        f.write(json.dumps(chat_entry) + "\n")

def load_chat_history():
    """Load the entire chat history from the log file."""
    if not os.path.exists(CHAT_LOG_FILE):
        return []
    chat_records = []
    with open(CHAT_LOG_FILE, 'r') as f:
        for line in f:
            try:
                chat_records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return chat_records

PROMPTS = {
        "الخدمات المتاحة": (
            "خدماتنا المتاحة:\n"
            "السباكة\n"
            "الكهرباء\n"
            "التكييف\n"
            "النجارة\n"
            "-------------------------\n"
            "كيف يمكنني مساعدتك؟"
        ),
        "إزاي أحجز فني": (
            "طريقة الحجز:\n"
            "يمكنك حجز فني عبر:\n"
            "1- تطبيق FixMate\n"
            "2- التواصل مع خدمة العملاء مباشرةً"
        ),
        "كام سعر": (
            "الأسعار:\n"
            "تختلف الأسعار حسب الخدمة المطلوبة.\n"
            "يُرجى التواصل معنا لمعرفة التفاصيل الدقيقة."
        ),
        "الفني هيوصل خلال قد إيه": (
            "وقت الوصول:\n"
            "يعتمد على الفني المتاح وموقعك.\n"
            "عادةً ما يكون بين 30 إلى 60 دقيقة."
        ),
        "إزاي أكلم خدمة العملاء": (
            "خدمة العملاء:\n"
            "يمكنك التواصل معنا عبر:\n"
            "- الهاتف\n"
            "- تطبيق FixMate\n"
            "لحصول على المساعدة الفورية."
        ),
        "ينفع أغير ميعاد الحجز": (
            "تعديل الحجز:\n"
            "نعم، يمكنك تعديل أو إلغاء الحجز عبر التطبيق.\n"
            "يجب أن يتم التعديل قبل الموعد بساعتين على الأقل."
        ),
        "هل في ضمان على الإصلاحات": (
            "الضمان:\n"
            "جميع خدماتنا مضمونة لمدة 30 يومًا من تاريخ التنفيذ.\n"
            "لضمان الجودة والراحة."
        ),
        "إزاي أدفع": (
            "طرق الدفع:\n"
            "نوفر الدفع النقدي والإلكتروني عبر التطبيق\n"
            "لمزيد من السهولة والراحة."
        ),
        "عندي ماس كهربائي في البيت": (
            "هذه حالة طارئة!\n"
            "سيتم توجيهك إلى أقرب فني متاح فورًا.\n"
            "هل تريد المتابعة؟"
        )
    }

def get_fixmate_response(user_message):
    for key in PROMPTS:
        if key in user_message:
            return PROMPTS[key]

    return generate_ai_response(user_message)

def generate_ai_response(user_message):
    messages = [
        {"role": "system", "content": "أنت مساعد ذكي خاص بمنصة FixMate. يجب أن تكون إجاباتك دقيقة ومباشرة دون إضافة أي معلومات غير مطلوبة."},
        {"role": "user", "content": user_message}
    ]

    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_completion_tokens=200,
            top_p=1,
            stop=None,
            stream=False,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception:
        return "عذرًا، حدث خطأ أثناء معالجة سؤالك. يرجى المحاولة مرة أخرى لاحقًا."


@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint to handle incoming messages and generate responses."""

    if request.content_type != 'application/json':
        return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 415

    data = request.get_json(force=True)  # 🔄 تغيير silent=True إلى force=True

    print("Received Data:", data)  # ✅ تتبع البيانات المستلمة

    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    new_user_message = data['message']
    assistant_message = get_fixmate_response(new_user_message)

    save_chat_log(new_user_message, assistant_message)

    return jsonify({"assistant_message": assistant_message})


@app.route('/history', methods=['GET'])
def history():
    """Endpoint to fetch all chat history."""
    chat_history = load_chat_history()
    return jsonify({"chat_history": chat_history})


@app.route('/')
def home():
    return "Flask App is Running on Vercel!"


# ✅ دعم تشغيل Flask على Vercel
def handler(event, context):
    return app(event, context)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
