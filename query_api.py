from fastapi import APIRouter
from pydantic import BaseModel

from query_engine import build_search_plan
from legislation_index import all_documents
from retrieval_engine import rank_documents, answer_shape

router = APIRouter(prefix="/api/v1", tags=["natural-language"])


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
def query(req: QueryRequest):
    question = req.question.strip()

    # 1. فهم السؤال وبناء خطة البحث
    search_plan = build_search_plan(question)

    # 2. جلب جميع المواد المفهرسة
    documents = all_documents()

    # 3. البحث والترتيب حسب صلة النص بالسؤال
    candidates = rank_documents(question, documents, limit=8)

    # 4. تكوين الإجابة من أفضل النتائج
    answer = answer_shape(question, candidates)

    return {
        "status": answer.get("status"),
        "question": question,
        "search_plan": search_plan,
        "answer": answer,
        "documents_searched": len(documents),
        "candidates_found": len(candidates),
    }
