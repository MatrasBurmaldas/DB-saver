import sqlite3
import requests
from bs4 import BeautifulSoup
import os

class Database:
    # об'єкт для роботи з базою даних

    def __init__(self, path="sites.db"):
        # шлях до бази поруч з файлом main.py
        folder = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(folder, path)
        # підключення до файлу бази
        self.conn = sqlite3.connect(full_path)
        # виведення шляху щоб знати де файл
        print("база даних:", full_path)

    def add_site(self, url):
        # додавання посилання без дублікатів
        self.conn.execute("INSERT OR IGNORE INTO sites (url) VALUES (?)", (url,))
        self.conn.commit()

    def get_sites(self):
        # отримання всіх посилань списком
        rows = self.conn.execute("SELECT url FROM sites").fetchall()
        return [row[0] for row in rows]

    def clear(self):
        # видалення всіх записів
        self.conn.execute("DELETE FROM sites")
        self.conn.commit()


class Parser:
    # об'єкт що завантажує сторінки і рахує збіги

    def count_phrase(self, url, phrase):
        try:
            # завантаження сторінки з обмеженням часу
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.RequestException:
            # якщо сайт недоступний вважаємо що збігів нема
            return 0
        # розбір html коду сторінки
        soup = BeautifulSoup(response.text, "html.parser")
        # видалення службових тегів з кодом і стилями
        for tag in soup(["script", "style"]):
            tag.decompose()
        # отримання видимого тексту
        text = soup.get_text().lower()
        # підрахунок скільки разів зустрілась фраза
        return text.count(phrase.lower())


class ConsoleUI:
    # об'єкт інтерфейсу користувача в консолі

    def show_menu(self):
        print("\n1 додати сайт")
        print("2 показати список сайтів")
        print("3 пошук")
        print("4 очистити базу")
        print("0 вихід")
        return input("оберіть дію: ").strip()

    def ask(self, text):
        # запит рядка від користувача
        return input(text).strip()

    def show_message(self, text):
        print(text)

    def show_results(self, results):
        # виведення результатів від більшої кількості до меншої
        if not results:
            print("нічого не знайдено")
            return
        for url, count in results:
            print(f"{count} збігів  {url}")


def run():
    # створення об'єктів і зв'язок між ними
    db = Database()
    parser = Parser()
    ui = ConsoleUI()

    # головний цикл програми
    while True:
        choice = ui.show_menu()

        if choice == "1":
            url = ui.ask("введіть посилання: ")
            db.add_site(url)
            ui.show_message("сайт додано")

        elif choice == "2":
            for site in db.get_sites():
                ui.show_message(site)

        elif choice == "3":
            phrase = ui.ask("що шукати: ")
            results = []
            for site in db.get_sites():
                count = parser.count_phrase(site, phrase)
                # у результат беремо лише сайти зі збігами
                if count > 0:
                    results.append((site, count))
            # сортування за кількістю збігів спадання
            results.sort(key=lambda item: item[1], reverse=True)
            ui.show_results(results)

        elif choice == "4":
            db.clear()
            ui.show_message("базу очищено")

        elif choice == "0":
            break


# запуск програми лише при прямому старті файлу
if __name__ == "__main__":
    run()