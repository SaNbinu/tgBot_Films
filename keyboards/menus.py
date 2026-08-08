from telebot import types

def start_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Films")
    return kb


def films_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Watched", "Wanted", "Recommendation")
    kb.add("Back")
    return kb


def watched_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Add", "Delete movie")
    kb.add("Back")
    return kb


def wanted_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Add", "Delete movie")
    kb.add("Back")
    return kb
