import telebot
import requests
import sys

BOT_TOKEN = "8924492918:AAEiJafRy_Xi0Hz4XyCFOSZ-Or70AY_0jdI"  # <-- Put your BotFather token here
SEARXNG_URL = "https://global-scraping-production.up.railway.app"


def test_searxng_connection():
    """Test if SearXNG is working before starting the bot"""
    print("Testing SearXNG connection...")
    try:
        r = requests.get(
            f"{SEARXNG_URL}/search",
            params={"q": "test", "format": "json"},
            timeout=15
        )
        print(f"Status Code: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                result_count = len(data.get("results", []))
                print(f"SearXNG working! Got {result_count} results for test query.")
                return True
            except ValueError:
                print("SearXNG responded but NOT in JSON format.")
                print("   Fix: check that settings.yml has 'formats: [html, json]',")
                print("   then redeploy on Railway.")
                print(f"   Raw response (first 300 chars): {r.text[:300]}")
                return False
        else:
            print(f"SearXNG returned status {r.status_code}")
            print(f"   Response: {r.text[:300]}")
            return False

    except requests.exceptions.ConnectionError:
        print("Connection failed - SearXNG URL is wrong or server is down.")
        return False
    except requests.exceptions.Timeout:
        print("Request timed out - server slow or not responding.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def check_bot_token():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN.strip():
        print("BOT_TOKEN is not set! Put your real token at the top of this script.")
        print("   Get a token from BotFather: t.me/BotFather -> /newbot")
        return False
    return True


# ---------- Pre-flight checks ----------
print("=" * 50)
print("SHUVO AI Global Search Bot - Starting checks")
print("=" * 50)

if not check_bot_token():
    sys.exit(1)

searxng_ok = test_searxng_connection()
if not searxng_ok:
    print("\nWarning: SearXNG has an issue, but the bot will still start.")
    print("   Search command may not work until SearXNG is fixed.\n")

print("=" * 50)

# ---------- Bot setup ----------
bot = telebot.TeleBot(BOT_TOKEN)


def global_search(query, num_results=8):
    try:
        params = {
            "q": query,
            "format": "json",
            "language": "en",
        }
        response = requests.get(f"{SEARXNG_URL}/search", params=params, timeout=15)
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            return {"error": "SearXNG did not return JSON. Check settings.yml formats config."}

        results = []
        for item in data.get("results", [])[:num_results]:
            results.append({
                "title": item.get("title", "No title"),
                "url": item.get("url", ""),
                "content": (item.get("content") or "No description")[:150],
            })
        return results

    except requests.exceptions.RequestException as e:
        return {"error": f"Search server error: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


def format_results(query, results):
    if isinstance(results, dict) and "error" in results:
        return f"Search failed: {results['error']}"

    if not results:
        return f"No results found for '{query}'."

    text = f"*Global Search Results for:* `{query}`\n\n"
    for i, r in enumerate(results, 1):
        text += f"*{i}. {r['title']}*\n"
        text += f"{r['url']}\n"
        text += f"{r['content']}...\n\n"

    return text


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Welcome to SHUVO AI Global Search!\n\n"
        "Use: `/search <your query>`\n"
        "Example: `/search SHUVO5600`",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["search"])
def handle_search(message):
    query = message.text.replace("/search", "").strip()

    if not query:
        bot.reply_to(message, "Please provide a query. Example: `/search SHUVO5600`", parse_mode="Markdown")
        return

    waiting_msg = bot.reply_to(message, f"Searching for `{query}`...", parse_mode="Markdown")

    results = global_search(query)
    formatted = format_results(query, results)

    try:
        bot.edit_message_text(
            formatted,
            chat_id=message.chat.id,
            message_id=waiting_msg.message_id,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception:
        # If Markdown parsing fails, send as plain text
        bot.edit_message_text(
            formatted,
            chat_id=message.chat.id,
            message_id=waiting_msg.message_id,
            disable_web_page_preview=True
        )


if __name__ == "__main__":
    print("Bot is running... (Ctrl+C to stop)")
    bot.infinity_polling()
