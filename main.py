import telebot
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = "bot_token"
CHAT_ID = - # Важно. Иначе будет не будет писать еп
URL = "https://servers-monitoring.ru/server/37.230.228.211:27020" # Ссылку на мониторинг. лучше юзать который используется здесь 
PLAYER_LINES_START = 83
PLAYER_LINES_COUNT = 5
TIME_FORMAT_INDICATORS = [":"]
WEBSITE_PHRASES = ["(1)www.svarog-game.com", "www.svarog-game.com"] # Суда никнейм бота с сервера ( спектатор с вк сайтом или просто сайтом , пофик )
# Фразы, которые нужно игнорировать типо сайты (не добавлять в player_lines, но проверять на них флаг)
EXCLUDE_FROM_PLAYERS = ["Комментарии к серверу", "Контакты"]
DETECTED_WEBSITE_PHRASE = False

def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.body.get_text(separator='\n', strip=True)
        lines = text_content.splitlines()
        data = {}
        for i, line in enumerate(lines):
            data[i + 1] = line
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Юзай /getdata, для вывода инфы с сервера")


@bot.message_handler(commands=['getdata'])
def get_data(message):
    bot.send_chat_action(message.chat.id, 'typing')

    data = scrape_website(URL)

    if "error" in data:
        bot.send_message(message.chat.id, f"Error: {data['error']}")
    else:
        line_60 = data.get(60, "N/A")
        line_66 = data.get(66, "N/A")
        line_72 = data.get(72, "N/A")

        player_lines = []
        global DETECTED_WEBSITE_PHRASE
        DETECTED_WEBSITE_PHRASE = False

        for i in range(PLAYER_LINES_COUNT):
            line_number = PLAYER_LINES_START + (i * 3)
            line_content = data.get(line_number, "N/A")

            is_time_format = any(indicator in line_content for indicator in TIME_FORMAT_INDICATORS)

            # Проверка на фразы, которые нужно исключить из списка игроков
            is_excluded = any(phrase in line_content for phrase in EXCLUDE_FROM_PLAYERS)

            # Проверка на веб-сайт
            is_website_phrase = any(phrase in line_content for phrase in WEBSITE_PHRASES)
            if is_website_phrase:
                DETECTED_WEBSITE_PHRASE = True

            if not is_time_format and not is_excluded:
                player_lines.append(line_content)

        player_lines_str = ", ".join(player_lines)

        output_parts = [
            f"Сервер: {line_60}\n",
            f"Игроки: {line_66}",
            player_lines_str,
        ]

        if DETECTED_WEBSITE_PHRASE:
            output_parts.append("\n1 из них бот")

        output_parts.append(f"\nКарта: {line_72}")

        output = "\n".join(output_parts)
        bot.send_message(message.chat.id, output)

if __name__ == '__main__':
    print("Бот запущен.")
    bot.infinity_polling()