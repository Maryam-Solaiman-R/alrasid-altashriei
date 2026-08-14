# الراصد التشريعي — وكيل بحث وتحليل بالذكاء الاصطناعي
يستخدم OpenAI Responses API مع أداة Web Search. لا يخزن اللوائح مسبقًا؛ يبحث وقت السؤال في المصادر الرسمية المختارة.
## Render
Build: `pip install -r requirements.txt`
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
Environment: `OPENAI_API_KEY` إلزامي. `OPENAI_MODEL` اختياري (الافتراضي `gpt-5.6`).


## Word export safe patch
Word styling updated only. Search button JavaScript and Excel export are preserved from the verified working build.
