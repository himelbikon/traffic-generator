from visit_automation import visit_website
import pandas as pd


VISIT_PER_DAY = 10


df = pd.read_csv("demo_scraping_sites.csv")

for index, row in df.iterrows():
    visit_website(row['URL'])
