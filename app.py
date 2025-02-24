from flask import Flask, request, jsonify
import os
from datetime import datetime, timezone
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("ERROR: GROQ_API_KEY not found! Please set it in your environment variables.")


client = Groq(api_key=api_key)


chat_history = []

def save_chat_log(user_message, assistant_message):
    chat_history.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_message": user_message,
        "assistant_message": assistant_message
    })

PROMPTS = {
    "الخدمات المتاحة": "خدماتنا المتاحة: السباكة الكهرباء التكييف النجارة كيف يمكنني مساعدتك؟",
    "إزاي أحجز فني": "طريقة الحجز: يمكنك حجز فني عبر 1- تطبيق FixMate 2- التواصل مع خدمة العملاء مباشرةً",
    "كام سعر": "الأسعار: تختلف الأسعار حسب الخدمة المطلوبة. يُرجى التواصل معنا لمعرفة التفاصيل الدقيقة.",
    "الفني هيوصل خلال قد إيه": "وقت الوصول: يعتمد على الفني المتاح وموقعك. عادةً ما يكون بين 30 إلى 60 دقيقة.",
    "إزاي أكلم خدمة العملاء": "خدمة العملاء: يمكنك التواصل معنا عبر - الهاتف - تطبيق FixMate لحصول على المساعدة الفورية.",
    "ينفع أغير ميعاد الحجز": "تعديل الحجز: نعم، يمكنك تعديل أو إلغاء الحجز عبر التطبيق. يجب أن يتم التعديل قبل الموعد بساعتين على الأقل.",
    "هل في ضمان على الإصلاحات": "الضمان: جميع خدماتنا مضمونة لمدة 30 يومًا من تاريخ التنفيذ. لضمان الجودة والراحة.",
    "إزاي أدفع": "طرق الدفع: نوفر الدفع النقدي والإلكتروني عبر التطبيق لمزيد من السهولة والراحة.",
    "عندي ماس كهربائي في البيت": "هذه حالة طارئة! سيتم توجيهك إلى أقرب فني متاح فورًا. هل تريد المتابعة؟"
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
    """معالجة الطلبات القادمة والردود"""
    try:
        data = request.get_json(force=True, silent=True)

        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' in request body"}), 400

        new_user_message = data['message']
        assistant_message = get_fixmate_response(new_user_message)

        save_chat_log(new_user_message, assistant_message)

        return jsonify({
            "assistant_message": assistant_message,
        })

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

@app.route('/history', methods=['GET'])
def history():
    return jsonify({"chat_history": chat_history})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
