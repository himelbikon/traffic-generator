import json
import os
from datetime import datetime

DB_JSON_PATH = 'db.json'

def load_db():
    if not os.path.exists(DB_JSON_PATH):
        json.dump({}, open(DB_JSON_PATH, 'w'))
        return {}
    
    with open(DB_JSON_PATH, 'r') as f:
        return json.load(f)

def save_db(db):
    with open(DB_JSON_PATH, 'w') as f:
        json.dump(db, f, indent=4)

def get_url_data(url):
    db = load_db()
    urls = db.get('urls', [])

    for index, url_obj in enumerate(urls):
        if url_obj.get('url') and url == url_obj.get('url'):
            return index, url_obj

    url_data = {'url': url}

    urls.append(url_data)

    db['urls'] = urls
    save_db(db)
    
    return len(urls) - 1, url_data

def add_url(url):
    get_url_data(url)


def remove_url(url):
    db = load_db()
    urls = db.get('urls', [])
    index, url_data = get_url_data(url)
    urls.pop(index)
    db['urls'] = urls
    save_db(db)

def add_visit(url):
    # try:
    if True:
        index, url_data = get_url_data(url)

        visits = url_data.get('visits', [])
        visits.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        url_data['visits'] = visits

        db = load_db()
        urls = db.get('urls', [])
        urls[index] = url_data
        db['urls'] = urls

        save_db(db)
        print(f"✓ Added visit to {url}")
    # except Exception as e:
    #     print(f"❌ Error occurred while adding visit: {str(e)}")

def count_visits(url):
    try:
        db = load_db()
        urls = db.get('urls', [])
        index, url_data = get_url_data(url)
        visits = url_data.get('visits', [])
        return len(visits)
    except Exception as e:
        print(f"❌ Error occurred while counting visits: {str(e)}")


if __name__ == '__main__':
    # add_url('https://www.google.com')
    add_visit('https://www.google2.com')
    print(count_visits('https://www.google.com'))