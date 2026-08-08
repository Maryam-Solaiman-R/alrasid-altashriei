from query_engine import build_search_plan
from retrieval_engine import rank_documents, answer_shape
from legislation_index import all_documents, upsert_document
from article_change_engine import applicability
from answer_formatter import format_agent_answer

from live_connectors import CONNECTORS
from live_fetcher import scan_root


def _live_search():
    """
    Search the configured official Saudi sources and return
    newly discovered official candidates.
    """
    findings = []

    for connector in sorted(CONNECTORS, key=lambda x: x.priority):
        for root in connector.roots:
            try:
                result = scan_root(root)

                for candidate in result.get("candidates", []):
                    findings.append({
                        "source_url": candidate.get("url") or candidate.get("href"),
                        "authority": connector.authority,
                        "instrument": "",
                        "document_type": "official_candidate",
                        "title": candidate.get("label", ""),
                        "article_number": "",
                        "text": candidate.get("label", ""),
                        "decision_number": "",
                        "decision_date": "",
                        "publication_date": "",
                        "effective_from": "",
                        "effective_to": "",
                        "transitional_rule": "",
                        "confidence": 0.50,
                    })

            except Exception:
                continue

    return findings


def ask(question: str):
    plan = build_search_plan(question)

    # 1. Search the local legislation index first
    docs = all_documents()
    candidates = rank_documents(question, docs)

    # 2. If local index has no useful result, perform live discovery
    if not candidates:
        live_docs = _live_search()

        # Store discovered official candidates in the local index
        for doc in live_docs:
            try:
                upsert_document(doc)
            except Exception:
                pass

        # Search again using newly discovered material
        docs = all_documents()
        candidates = rank_documents(question, docs)

    shaped = answer_shape(question, candidates)

    formatted = format_agent_answer(
        question,
        plan["analysis"],
        candidates
    )

    return {
        "question": question,
        "understanding": plan["analysis"],
        "search_plan": plan["plan"],
        **shaped,
        "formatted_answer": formatted,
    }


def changed(instrument_or_topic: str = "", limit: int = 50):
    docs = all_documents()

    if instrument_or_topic:
        docs = rank_documents(
            instrument_or_topic,
            docs,
            limit=limit
        )

    docs = sorted(
        docs,
        key=lambda x: (
            x.get("effective_from")
            or x.get("publication_date")
            or ""
        ),
        reverse=True,
    )

    return {
        "count": len(docs[:limit]),
        "items": docs[:limit],
    }
