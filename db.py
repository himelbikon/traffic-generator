import calendar
import json
import os
from datetime import datetime, timedelta

DB_JSON_PATH = 'db.json'


def load_db():
    if not os.path.exists(DB_JSON_PATH):
        json.dump({}, open(DB_JSON_PATH, 'w', encoding='utf-8'))
        return {}

    with open(DB_JSON_PATH, 'r') as f:
        return json.load(f)


def save_db(db):
    with open(DB_JSON_PATH, 'w', encoding='utf-8') as f:
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
    try:
        index, url_data = get_url_data(url)

        visits = url_data.get('visits', [])
        visits.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        url_data['visits'] = visits

        db = load_db()
        urls = db.get('urls', [])
        urls[index] = url_data
        db['urls'] = urls

        save_db(db)
        print(f"Added visit to {url}")
    except Exception as e:
        print(f"Error occurred while adding visit: {str(e)}")


def count_visits(url):
    try:
        _, url_data = get_url_data(url)
        visits = url_data.get('visits', [])
        return len(visits)
    except Exception as e:
        print(f"Error occurred while counting visits: {str(e)}")


def count_visits_today(url):
    try:
        _, url_data = get_url_data(url)
        visits = url_data.get('visits', [])

        today = datetime.now().date()  # get current date

        # Filter visits that match today's date
        visits_today = [
            v for v in visits
            if datetime.strptime(v, "%Y-%m-%d %H:%M:%S").date() == today
        ]

        return len(visits_today)

    except Exception as e:
        print(f"Error occurred while counting today's visits: {str(e)}")


def import_visits_csv():
    """
    Provides a CSV string with the count of all URLs visited per day for the last month.
    'data' should be a dictionary like your JSON example.
    """
    today = datetime.now()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    last_month = last_day_of_last_month.month
    last_month_year = last_day_of_last_month.year

    # Prepare a dictionary: {url: {day: count}}
    visits_per_url = {}

    data = load_db()

    for entry in data.get('urls', []):
        url = entry['url']
        visits_per_day = {}
        for visit_str in entry.get('visits', []):
            visit_datetime = datetime.strptime(visit_str, '%Y-%m-%d %H:%M:%S')
            if visit_datetime.year == last_month_year and visit_datetime.month == last_month:
                day = visit_datetime.day
                visits_per_day[day] = visits_per_day.get(day, 0) + 1
        visits_per_url[url] = visits_per_day

    # Generate CSV header
    csv_data = "Date," + ",".join(visits_per_url.keys()) + "\n"

    # Number of days in last month
    _, num_days = calendar.monthrange(last_month_year, last_month)

    # Fill CSV rows
    for day in range(1, num_days + 1):
        date_str = f"{last_month_year}-{last_month:02d}-{day:02d}"
        row = [date_str]
        for url in visits_per_url.keys():
            row.append(str(visits_per_url[url].get(day, 0)))
        csv_data += ",".join(row) + "\n"

    return csv_data


if __name__ == '__main__':
    # add_url('https://www.google.com')
    add_visit('http://books.toscrape.com/')
    print(count_visits('http://books.toscrape.com/'))
    csv_data = import_visits_csv()
    print(csv_data)
    open('visits.csv', 'w').write(csv_data)
