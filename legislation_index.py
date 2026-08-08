import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("legislation_index.db")


def init_index():
    con = sqlite3.connect(DB)

    con.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            source_url TEXT,
            authority TEXT,
            instrument TEXT,
            document_type TEXT,
            title TEXT,
            article_number TEXT,
            text_value TEXT,
            decision_number TEXT,
            decision_date TEXT,
            publication_date TEXT,
            effective_from TEXT,
            effective_to TEXT,
            transitional_rule TEXT,
            confidence REAL DEFAULT 0,
            UNIQUE(source_url, article_number, text_value)
        )
    """)

    con.commit()
    con.close()


def upsert_document(d):
    init_index()
    con = sqlite3.connect(DB)

    con.execute("""
        INSERT OR REPLACE INTO documents (
            source_url,
            authority,
            instrument,
            document_type,
            title,
            article_number,
            text_value,
            decision_number,
            decision_date,
            publication_date,
            effective_from,
            effective_to,
            transitional_rule,
            confidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        d.get("source_url"),
        d.get("authority"),
        d.get("instrument"),
        d.get("document_type"),
        d.get("title"),
        d.get("article_number"),
        d.get("text_value") or d.get("text"),
        d.get("decision_number"),
        d.get("decision_date"),
        d.get("publication_date"),
        d.get("effective_from"),
        d.get("effective_to"),
        d.get("transitional_rule"),
        d.get("confidence", 0),
    ))

    con.commit()
    con.close()


def all_documents():
    init_index()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    rows = [
        dict(row)
        for row in con.execute("""
            SELECT
                id,
                source_url,
                authority,
                instrument,
                document_type,
                title,
                article_number,
                text_value AS text,
                decision_number,
                decision_date,
                publication_date,
                effective_from,
                effective_to,
                transitional_rule,
                confidence
            FROM documents
        """)
    ]

    con.close()
    return rows
