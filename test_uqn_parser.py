from backend_app import extract_uqn

URL = 'https://www.uqn.gov.sa/decisions-and-regulations/4001123'
if __name__ == '__main__':
    data = extract_uqn(URL)
    print(data['title'])
    print(data['decision_number'], data['decision_date_hijri'])
    print(data['publication_date_hijri'], data['publication_date_gregorian'])
    print(data['articles'])
    print(data['effective_rule'])
