from source_adapters import adapter_for
from diff_engine import word_diff
from backend_app import uqn_parse

html='''<html><body>
<a href="/decisions-and-regulations/4001126">تعديل اللائحة التنفيذية لنظام المنافسات والمشتريات الحكومية</a>
<a href="/news/1">خبر عام</a>
</body></html>'''
a=adapter_for('https://www.uqn.gov.sa/decisions-and-regulations')
rows=a.discover(html,'https://www.uqn.gov.sa/decisions-and-regulations')
assert rows and rows[0].url.endswith('/4001126')
assert rows[0].score > 0.5

d=word_diff('يجب تقديم الضمان خلال عشرة أيام','يجب تقديم الضمان خلال خمسة عشر يوم عمل')
assert d['similarity'] < 1
assert d['changes']

fixture='''قرار وزير المالية رقم (1097) بتاريخ 9/12/1447هـ
تعديل المواد (88) و(111) و(114) و(132) من اللائحة التنفيذية لنظام المنافسات والمشتريات الحكومية.
يعمل به ابتداء من تاريخه.'''
p=uqn_parse(fixture,'https://www.uqn.gov.sa/decisions-and-regulations/4001123')
assert p['decision_number']=='1097'
assert p['article_numbers']==['88','111','114','132']
print('OK v0.7')
