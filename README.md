# الراصد التشريعي — وكيل بحث وتحليل بالذكاء الاصطناعي
يستخدم OpenAI Responses API مع Web Search للبحث وقت السؤال في المصادر الرسمية المختارة.

## التحسينات
- عرض Markdown كعناوين وجداول فعلية في الواجهة.
- تصدير Word عربي RTL بهوية الراصد وروابط المصادر.
- تصدير Excel عربي RTL بهوية الراصد، جداول منظمة وروابط قابلة للنقر.
- التصدير يستخدم نتيجة البحث الموجودة ولا يعيد استدعاء الذكاء الاصطناعي، لتجنب تكلفة بحث إضافية.

## Render
Build: `pip install -r requirements.txt`
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
Environment: `OPENAI_API_KEY` إلزامي. `OPENAI_MODEL` اختياري (الافتراضي `gpt-5.6`).
