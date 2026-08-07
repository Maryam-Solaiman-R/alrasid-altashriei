import os, tempfile, importlib
from pathlib import Path
import backend_app as b

# isolate test DB
fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd); os.unlink(path)
b.DB=Path(path); b.init_db()

base=b.ArticleVersionUpsert(
    instrument_name='لائحة اختبار عامة', article_number='10',
    text_value='يجوز للجهة إتمام الإجراء خلال ثلاثين يوما.', valid_from='2025-01-01',
    decision_number='1', decision_date='2025-01-01', source_url='https://example.gov.sa/old')
new=b.ArticleVersionUpsert(
    instrument_name='لائحة اختبار عامة', article_number='10',
    text_value='يجوز للجهة إتمام الإجراء خلال ستين يوما.', valid_from='2026-06-01',
    decision_number='2', decision_date='2026-06-01', source_url='https://example.gov.sa/new')
b.add_article_version(base); b.add_article_version(new)
rows=b._version_rows('لائحة اختبار عامة','10')
assert rows[0]['valid_to']=='2026-06-01', rows
assert rows[1]['valid_to'] is None, rows
old=b.applicability('لائحة اختبار عامة','10','2026-05-20')
cur=b.applicability('لائحة اختبار عامة','10','2026-06-20')
assert 'ثلاثين' in old['version']['text_value'], old
assert 'ستين' in cur['version']['text_value'], cur
print('OK v0.8: version closure + temporal applicability passed')
