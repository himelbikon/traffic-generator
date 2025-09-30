from visit_automation import visit_website
import pandas as pd
import db


VISIT_PER_DAY = 20


def had_enough_visits(url):
    visits = db.count_visits_today(url)
    if visits >= VISIT_PER_DAY:
        print(f"Already had enough visits ({visits}) for {url}")
        return True
    return False


def visit_all_sites():
    df = pd.read_csv("demo_scraping_sites.csv")

    all_site_visited = True

    for index, row in df.iterrows():
        if had_enough_visits(row['URL']):
            continue

        all_site_visited = False

        for _ in range(3):
            try:
                visit_website(row['URL'])
                break
            except Exception as e:
                print(f"Error occurred while visiting {row['URL']}: {str(e)}")

    return all_site_visited


while True:
    all_site_visited = visit_all_sites()
    if all_site_visited:
        print("All sites are visited")
        break
        

    sleep_time = 10 * 3600 / max(VISIT_PER_DAY-2, 2)

    doped_sleep_time = sleep_time + random.randint(-int(sleep_time * 0.2), int(sleep_time * 0.2))

    hour = doped_sleep_time // 3600
    minute = (doped_sleep_time % 3600) // 60

    print(f"Sleeping for {hour} hours and {minute} minutes")
    time.sleep(doped_sleep_time)

