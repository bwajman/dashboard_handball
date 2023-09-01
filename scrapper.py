import sqlite3
import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
import re
import pandas as pd

# Find every country
def get_country(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    country = [country.get_text() for country in soup.find(class_="box-aside__section__in").find_all('a') if country != None]
    for row in country:
        cursor.execute("INSERT INTO COUNTRY_SL (COUNTRY) SELECT ? WHERE NOT EXISTS (SELECT 1 FROM COUNTRY_SL WHERE COUNTRY = ?)",(row,row))
        connection.commit()

# Find links for any country
def links_country(url):
    cursor.execute("SELECT ID, COUNTRY FROM COUNTRY_SL")
    countries = cursor.fetchall()
    for id, country in countries:
        cursor.execute("SELECT MAX(ID_COUNTRY)-1 FROM LINKS")
        max = cursor.fetchone()
        print(max)
        if id > int(max[0]):
            response = requests.get(f"{url}{country.lower().replace('& ','').replace(' ','-')}")
            soup = BeautifulSoup(response.content, 'html.parser')
            for link in soup.find(class_="box-overflow").find_all('a'):
                cursor.execute("INSERT INTO LINKS (ID_COUNTRY, HREF) SELECT ?, ? WHERE NOT EXISTS (SELECT 1 FROM LINKS WHERE HREF = ?)", (country[0], link['href'], link['href']))
                connection.commit()

# Links for main_stage etc. if it exist in each season
def new_links(url):
    cursor.execute("SELECT ID, ID_COUNTRY, HREF FROM LINKS WHERE FLAG = 0")
    links = cursor.fetchall()
    for id, id_country, link in links:
        link = f"https://www.betexplorer.com{link.lower()}results"
        response = requests.get(link)
        print(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            page = soup.find_all("div", class_ = 'box-overflow__in')[1].find_all('a')
            for href in page:
                new_link = f"{link}/{str(href['href'])}"
                if 'stage' in new_link:
                    cursor.execute("INSERT INTO SUB_LINKS (ID_COUNTRY,ID_LINK, HREF) SELECT ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM SUB_LINKS WHERE HREF = ?)",(id_country, id, new_link, new_link))
                    cursor.execute("UPDATE LINKS SET FLAG = 1 WHERE ID = ?",(id,))
                    connection.commit()
                else:
                    cursor.execute("UPDATE LINKS SET FLAG = 2 WHERE ID = ?", (id,))
                    connection.commit()
        except:
            cursor.execute("UPDATE LINKS SET FLAG = 2 WHERE ID = ?",(id,))
            connection.commit()
            continue

# Go to every link
def seasons_scrap():
        cursor.execute("SELECT ID, ID_COUNTRY, NULL, HREF, 1 AS SOURCE FROM LINKS WHERE FLAG = 2 UNION SELECT ID, ID_COUNTRY, ID_LINK, HREF, 2 AS SOURCE FROM SUB_LINKS WHERE FLAG = 0")
        rows = cursor.fetchall()
        for id, id_country, id_link, href, source in rows:
            if source == 1:
                href = 'https://www.betexplorer.com'+href+'results'
            response = requests.get(href)
            print(href)
            soup = BeautifulSoup(response.content, 'html.parser')
            league = href.split('/')[5]
            matches = soup.find_all('tr')
            if not matches:
                if source == 1:
                    cursor.execute("UPDATE LINKS SET FLAG = 4 WHERE ID = ?", (id,))
                elif source == 2:
                    cursor.execute("UPDATE SUB_LINKS SET FLAG = 4 WHERE ID = ?", (id,))
            connection.commit()
            for match in matches:
                if match.find('td', class_ = 'h-text-left'):
                    teams = match.find('td',class_='h-text-left').get_text()
                    score = match.find('td',class_='h-text-center').get_text()
                    numbers = re.findall('\d{1,2}\.\d{1,2}(?:\.\d{4})?\.?',str(match))
                    home, draw, away = ['NaN']*3
                    try:
                        home, draw, away, date = numbers
                    except:
                        date = numbers[0]
                    if date.endswith("."):
                        date += '2023'
                    if source == 1:
                        cursor.execute("UPDATE LINKS SET FLAG = 3 WHERE ID = ?",(id,))
                    elif source == 2:
                        cursor.execute("UPDATE SUB_LINKS SET FLAG = 3 WHERE ID = ?", (id,))
                    cursor.execute("INSERT INTO MATCHES (ID_COUNTRY,ID_SOURCE,ID_LINK, COMPETITION, TEAMS, RESULT, HOME, DRAW, AWAY, DATE) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ",
                    (id_country, source, id, league, teams, score, home, draw, away, date))
                    print(f'{id};{source}\n')
                    connection.commit()

# Update counts matches
def update_info():
    cursor.execute("UPDATE LINKS SET COUNT =(SELECT COUNT(b.ID_LINK) FROM MATCHES b WHERE LINKS.ID = b.ID_LINK and b.ID_SOURCE = 1 GROUP BY b.ID_LINK)")
    cursor.execute("UPDATE SUB_LINKS SET COUNT =(SELECT COUNT(b.ID_LINK) FROM MATCHES b WHERE SUB_LINKS.ID = b.ID_LINK and b.ID_SOURCE = 2 GROUP BY b.ID_LINK)")
    cursor.execute("UPDATE LINKS SET COUNT = 0 WHERE COUNT IS NULL")
    cursor.execute("UPDATE SUB_LINKS SET COUNT = 0 WHERE COUNT IS NULL")


try:
    connection = sqlite3.connect('/Users/admin/database/handball.db')
    cursor = connection.cursor()
    url = 'https://www.betexplorer.com/handball/'
    get_country(url)
    links_country(url)
    new_links(url)
    seasons_scrap()
    update_info()
    connection.commit()
    query = 'SELECT c.COUNTRY, CASE WHEN ID_SOURCE = 1 THEN l.HREF WHEN ID_SOURCE = 2 THEN sl.HREF END as LINK, ' \
            'm.COMPETITION, m.TEAMS, m.RESULT, m.HOME, m.DRAW, m.AWAY, m.DATE ' \
            'FROM MATCHES m INNER JOIN COUNTRY_SL c ON m.ID_COUNTRY = c.ID ' \
            'LEFT JOIN LINKS l ON m.ID_LINK = l.ID ' \
            'LEFT JOIN SUB_LINKS sl ON m.ID_LINK = sl.ID'
    df=pd.read_sql_query(query,connection)
    df.to_csv('/Users/admin/database/data.csv')
    connection.close()

except ConnectionError:
    print('Error with connection')
