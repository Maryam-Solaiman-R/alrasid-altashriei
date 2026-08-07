
from query_engine import build_search_plan
from retrieval_engine import rank_documents, answer_shape
from legislation_index import all_documents
from article_change_engine import applicability
from answer_formatter import format_agent_answer

def ask(question:str):
    plan=build_search_plan(question)
    docs=all_documents()
    candidates=rank_documents(question,docs)
    shaped=answer_shape(question,candidates)
    formatted=format_agent_answer(question,plan["analysis"],candidates)
    return {"question":question,"understanding":plan["analysis"],"search_plan":plan["plan"],**shaped,"formatted_answer":formatted}
def changed(instrument_or_topic:str="", limit:int=50):
    docs=all_documents()
    if instrument_or_topic:
        docs=rank_documents(instrument_or_topic,docs,limit=limit)
    docs=sorted(docs,key=lambda x:(x.get("effective_from") or "",x.get("publication_date") or ""),reverse=True)
    return {"count":len(docs[:limit]),"items":docs[:limit]}
