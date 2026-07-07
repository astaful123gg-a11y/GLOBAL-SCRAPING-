import telebot
import requests
from telebot import types

BOT_TOKEN = "8924492918:AAGaKEZwAAHbzsIPp1ZY6Z6394yDkXXDmVQ"
SEARXNG_URL = "global-scraping-production.up.railway.app"  # <-- tomar Railway URL boshao

bot = telebot.TeleBot(BOT_TOKEN)


def global_search(query, num_results=8):
    """
    Nijer self-hosted SearXNG theke search kore.
    Kono API key lagbe na, kono daily limit nai.
    """
    try:
        params = {
            "q": query,
            "format": "json",
            "language": "en",
        }
        response = requests.get(f"{SEARXNG_URL}/search", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", [])[:num_results]:
            results.append({
                "title": item.get("title", "No title"),
                "url": item.get("url", ""),
                "content": item.get("content", "No description")[:150],
            })
        return results

    except requests.exceptions.RequestException as e:
        return {"error": f"Search server error: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


def format_results(query, results):
    if isinstance(results, dict) and "error" in results:
        return f"❌ Search failed: {results['error']}"

    if not results:
        return f"😕 Kono result pawa jayni '{query}' er jonno."

    text = f"🔍 **Global Search Results for:** `{query}`\n\n"
    for i, r in enumerate(results, 1):
        text += f"**{i}. {r['title']}**\n"
        text += f"🔗 {r['url']}\n"
        text += f"📝 {r['content']}...\n\n"

    return text


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "👋 Welcome to SHUVO AI Global Search!\n\n"
        "Use: `/search <your query>`\n"
        "Example: `/search SHUVO5600`",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["search"])
def handle_search(message):
    query = message.text.replace("/search", "").strip()

    if not query:
        bot.reply_to(message, "⚠️ Query dao. Example: `/search SHUVO5600`", parse_mode="Markdown")
        return

    waiting_msg = bot.reply_to(message, f"🔎 Searching for `{query}`...", parse_mode="Markdown")

    results = global_search(query)
    formatted = format_results(query, results)

    bot.edit_message_text(
        formatted,
        chat_id=message.chat.id,
        message_id=waiting_msg.message_id,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
