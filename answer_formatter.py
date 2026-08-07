def format_agent_answer(question, understanding, candidates):
    out={"question":question,"understanding":understanding,"answer_status":"needs_live_search","findings":[]}
    for c in candidates:
        out["findings"].append({"instrument":c.get("instrument"),"article_number":c.get("article_number"),
          "authority":c.get("authority"),"relevance":c.get("relevance"),
          "text_excerpt":(c.get("text") or "")[:700],"decision_number":c.get("decision_number"),
          "decision_date":c.get("decision_date"),"effective_from":c.get("effective_from"),
          "effective_to":c.get("effective_to"),"transitional_rule":c.get("transitional_rule"),
          "source_url":c.get("source_url"),"confidence":c.get("confidence")})
    if out["findings"]: out["answer_status"]="candidate_materials_found"
    return out
