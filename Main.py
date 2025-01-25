from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.helpers import escape_markdown
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
import random

# Game data storage
active_games = {}
high_scores = {}

# Menu commands description
COMMANDS = [
    BotCommand("start", "Show welcome message"),
    BotCommand("play", "Start new game"),
    BotCommand("score", "Show current score"),
    BotCommand("top", "View leaderboard"),
    BotCommand("cancel", "Cancel current game")
]


def generate_visual(attempts: int, max_attempts: int, last_guess: int, target: int) -> str:
    """Generate enhanced ASCII art with game state"""
    art = [
        "┌───────────────┐",
        "│               │",
        "│               │",
        "│               │",
        "│               │",
        "└───────────────┘"
    ]

    position = min(9, max(0, last_guess // 10)) if last_guess else 5
    art[2] = f"│ {' ' * position}🎯{' ' * (9 - position)} │"
    art[4] = f"│  Attempts: {attempts}/{max_attempts}  │"

    if last_guess:
        diff = abs(last_guess - target)
        heat = min(4, diff // 10)
        art[1] = "│ " + "🔥" * heat + "🧊" * (4 - heat) + " │"

    return "\n".join(art)


def create_number_pad(last_guess: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("+10", callback_data="+10"),
            InlineKeyboardButton("+5", callback_data="+5"),
            InlineKeyboardButton("+1", callback_data="+1")
        ],
        [
            InlineKeyboardButton(str(last_guess) if last_guess else "---", callback_data="show")
        ],
        [
            InlineKeyboardButton("-1", callback_data="-1"),
            InlineKeyboardButton("-5", callback_data="-5"),
            InlineKeyboardButton("-10", callback_data="-10")
        ],
        [
            InlineKeyboardButton("🎯 Submit Guess", callback_data="submit")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("New Game 🎮", callback_data="menu_play"),
            InlineKeyboardButton("Score 🏆", callback_data="menu_score")
        ],
        [
            InlineKeyboardButton("Leaderboard 🏅", callback_data="menu_top"),
            InlineKeyboardButton("Cancel ❌", callback_data="menu_cancel")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        escape_markdown(
            "🎮 *Number Radar 3000* 🎮\n"
            "Use buttons below to play or type commands!\n"
            "🔥 *Features:*\n"
            "- Interactive number pad\n"
            "- Radar display\n"
            "- Heat indicator\n"
            "- 10 attempts limit",
            version=2
        ),
        parse_mode="MarkdownV2",
        reply_markup=main_menu()
    )


async def set_commands(app: Application) -> None:
    await app.bot.set_my_commands(COMMANDS)


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user

    active_games[chat_id] = {
        "target": random.randint(1, 100),
        "attempts": 0,
        "max_attempts": 10,
        "score": 1000,
        "player": escape_markdown(user.full_name, version=2),
        "last_guess": None
    }

    art = generate_visual(0, 10, None, active_games[chat_id]["target"])
    keyboard = create_number_pad(None)

    await update.message.reply_text(
        escape_markdown(
            f"🆕 *New Game Started!*\n"
            f"```\n{art}\n```\n"
            "_Initial score_: `1000` points \\(-100 per guess\\)",
            version=2
        ),
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id in active_games:
        del active_games[chat_id]
    await update.message.reply_text(
        "🚫 Game canceled. Use /play to start again.",
        reply_markup=main_menu()
    )


async def show_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in active_games:
        await update.message.reply_text(
            "No active game! Use /play to start",
            reply_markup=main_menu()
        )
        return

    game = active_games[chat_id]
    await update.message.reply_text(
        escape_markdown(
            f"🏆 Current Score: {game['score']} points\n"
            f"Attempts: {game['attempts']}/{game['max_attempts']}\n"
            f"Last Guess: {game['last_guess'] or 'None'}",
            version=2
        ),
        parse_mode="MarkdownV2",
        reply_markup=main_menu()
    )


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not high_scores.get(chat_id):
        await update.message.reply_text(
            "No high scores yet! Be the first!",
            reply_markup=main_menu()
        )
        return

    score = high_scores[chat_id]
    await update.message.reply_text(
        escape_markdown(
            "🏆 *Leaderboard* 🏆\n"
            f"Top Score: {score['score']} points\n"
            f"Attempts: {score['attempts']}\n"
            f"Holder: {score['name']}",
            version=2
        ),
        parse_mode="MarkdownV2",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat_id
    message = query.message

    # Handle menu buttons
    if data.startswith("menu_"):
        action = data.split("_")[1]
        try:
            if action == "play":
                # Start new game through menu
                user = update.effective_user
                active_games[chat_id] = {
                    "target": random.randint(1, 100),
                    "attempts": 0,
                    "max_attempts": 10,
                    "score": 1000,
                    "player": escape_markdown(user.full_name, version=2),
                    "last_guess": None
                }

                art = generate_visual(0, 10, None, active_games[chat_id]["target"])
                keyboard = create_number_pad(None)

                await message.edit_text(
                    escape_markdown(
                        f"🆕 *New Game Started!*\n"
                        f"```\n{art}\n```\n"
                        "_Initial score_: `1000` points \\(-100 per guess\\)",
                        version=2
                    ),
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard
                )
                return

            elif action == "score":
                if chat_id not in active_games:
                    await message.edit_text(
                        "No active game! Use /play to start",
                        reply_markup=main_menu()
                    )
                    return

                game = active_games[chat_id]
                await message.edit_text(
                    escape_markdown(
                        f"🏆 Current Score: {game['score']} points\n"
                        f"Attempts: {game['attempts']}/{game['max_attempts']}\n"
                        f"Last Guess: {game['last_guess'] or 'None'}",
                        version=2
                    ),
                    parse_mode="MarkdownV2",
                    reply_markup=main_menu()
                )
                return

            elif action == "top":
                if not high_scores.get(chat_id):
                    await message.edit_text(
                        "No high scores yet! Be the first!",
                        reply_markup=main_menu()
                    )
                    return

                score = high_scores[chat_id]
                await message.edit_text(
                    escape_markdown(
                        "🏆 *Leaderboard* 🏆\n"
                        f"Top Score: {score['score']} points\n"
                        f"Attempts: {score['attempts']}\n"
                        f"Holder: {score['name']}",
                        version=2
                    ),
                    parse_mode="MarkdownV2",
                    reply_markup=main_menu()
                )
                return

            elif action == "cancel":
                if chat_id in active_games:
                    del active_games[chat_id]
                await message.edit_text(
                    "🚫 Game canceled. Use /play to start again.",
                    reply_markup=main_menu()
                )
                return

        except Exception as e:
            print(f"Error handling menu action: {e}")
            return

    # Handle game buttons
    game = active_games.get(chat_id)
    if not game:
        await message.edit_text("Game expired! Use /play to start new", reply_markup=main_menu())
        return

    current = game["last_guess"] or 50  # Default to middle value
    new_guess = current

    try:
        if data.startswith(("+", "-")):
            adjustment = int(data)
            new_guess = max(1, min(100, current + adjustment))
            game["last_guess"] = new_guess

        elif data == "submit":
            if game["last_guess"] is None:
                await query.answer("First adjust your guess using +/- buttons!", show_alert=True)
                return

            await process_guess(chat_id, game["last_guess"], message)
            return

        # Update display for number adjustments
        art = generate_visual(
            game["attempts"],
            game["max_attempts"],
            game["last_guess"],
            game["target"]
        )
        keyboard = create_number_pad(game["last_guess"])

        await message.edit_text(
            escape_markdown(
                f"🎯 Current guess: `{new_guess}`\n"
                f"```\n{art}\n```\n"
                f"Remaining score: `{game['score']}` points",
                version=2
            ),
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"Error handling button press: {e}")
        await message.edit_text("⚠️ Error processing your request. Please start a new game.", reply_markup=main_menu())

async def process_guess(chat_id: int, guess: int, message) -> None:
    game = active_games[chat_id]
    game["attempts"] += 1
    game["score"] = max(0, game["score"] - 100)

    art = generate_visual(
        game["attempts"],
        game["max_attempts"],
        guess,
        game["target"]
    )

    if guess == game["target"]:
        current_high = high_scores.get(chat_id, {"score": 0, "attempts": float('inf')})
        if game["score"] > current_high["score"]:
            high_scores[chat_id] = {
                "score": game["score"],
                "name": game["player"],
                "attempts": game["attempts"]
            }

        await message.reply_text(
            escape_markdown(
                f"🎉 *Correct!* 🎉\n"
                f"```\n{art}\n```\n"
                f"Guessed in {game['attempts']} attempts!\n"
                f"Final Score: `{game['score']}` points",
                version=2
            ),
            parse_mode="MarkdownV2",
            reply_markup=main_menu()
        )
        del active_games[chat_id]
    else:
        hint = "HIGHER ▲" if guess < game["target"] else "LOWER ▼"
        keyboard = create_number_pad(guess)

        if game["attempts"] >= game["max_attempts"]:
            await message.reply_text(
                escape_markdown(
                    f"❌ *Game Over!* ❌\n"
                    f"```\n{art}\n```\n"
                    f"The number was `{game['target']}`",
                    version=2
                ),
                parse_mode="MarkdownV2",
                reply_markup=main_menu()
            )
            del active_games[chat_id]
        else:
            await message.reply_text(
                escape_markdown(
                    f"{hint}\n"
                    f"```\n{art}\n```\n"
                    f"Attempt {game['attempts']}/{game['max_attempts']}\n"
                    f"Remaining score: `{game['score']}` points",
                    version=2
                ),
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )


def main() -> None:
    application = (
        Application.builder()
        .token("7533398063:AAHVuRlg083dONrSWYkrQkMRd2VoayZlUo8")
        .post_init(set_commands)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("score", show_score))
    application.add_handler(CommandHandler("top", show_leaderboard))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: None))

    application.run_polling()


if __name__ == '__main__':
    main()