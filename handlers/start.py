from bot import bot
from keyboards.menus import start_menu

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        f"Hello {message.from_user.first_name}",
        reply_markup=start_menu()
    )