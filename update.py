import io
import requests
from bs4 import BeautifulSoup

max_post_count = 5
prefix = 'https://t.me/world_in_red/'
telegram_url = 'https://t.me/s/world_in_red'
personal_file = 'personal.html'
personal_file_offset = 5
index_file = "index.html"
index_file_offset = 38
id_stub = 'stub'
template = '  <script async src="https://telegram.org/js/telegram-widget.js" data-telegram-post="world_in_red/stub" data-width="100%" data-color="343638" data-dark-color="FFFFFF"></script>\n'

# read latest posts
html_text = requests.get(telegram_url).text
soup = BeautifulSoup(html_text, 'html.parser')
links = soup.findAll("a", {"class": "tgme_widget_message_date"}, href=True)

ids = []
for link in links:
    ids.append(int(link['href'].replace(prefix, '')))

ids.reverse()
ids = ids[:max_post_count]

# update 'personal' file
file = []
with io.open(personal_file, 'r', encoding='utf8') as f:
    file = f.readlines()

with io.open(personal_file, 'w', encoding='utf8') as f:
    for line in file[:personal_file_offset]:
        if not line.startswith(template[:10]):
            f.write(line)
    for id in ids:
        f.write(template.replace(id_stub, str(id)))
    f.write(file[-1])

# update 'index' file
file = []
with io.open(index_file, 'r', encoding='utf8') as f:
    file = f.readlines()

with io.open(index_file, 'w', encoding='utf8') as f:
    for line in file[:index_file_offset]:
        if not line.startswith(template[:10]):
            f.write(line)
    f.write(template.replace(id_stub, str(ids[0])))
    f.write(file[-1])
