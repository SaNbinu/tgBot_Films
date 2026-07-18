from telebot import types

def start_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("films")
    return kb


def films_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Смотрел", "Желание", "Рекомендация")
    kb.add("back")
    return kb


def watched_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("add")
    kb.add("back")
    return kb


def wanted_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("add")
    kb.add("back")
    return kb