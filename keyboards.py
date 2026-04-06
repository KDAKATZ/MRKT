from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from math import ceil

On1 = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Магазины")],
                                    [KeyboardButton(text="Информация FAQ"),KeyboardButton(text="Поддержка")]],
                                    resize_keyboard=True)

admin_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Рассылка", callback_data="spam")],
                                                   [InlineKeyboardButton(text="Добавить Шоп", callback_data="add_shop")],
                                                   [InlineKeyboardButton(text="Удалить Шоп", callback_data="delete_shop")],
                                                   [InlineKeyboardButton(text="Редактировать Шоп", callback_data="edit_shop")],
                                                   [InlineKeyboardButton(text="Добавить Тему", callback_data="add_theme")],
                                                   [InlineKeyboardButton(text="Удалить Тему", callback_data="delete_theme")]])

skip_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_photo")]])


def like_keyboard(shop_id: int, likes: int):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                    text=f"👍 Лайки ({likes})",
                    callback_data=f"like_shop_{shop_id}")]])


def paginate_buttons(buttons: list, page: int = 0, page_size: int = 5, prefix: str = "page_"):
    total_pages = ceil(len(buttons) / page_size)
    start = page * page_size
    end = start + page_size
    page_buttons = buttons[start:end]
    inline_keyboard = [[btn] for btn in page_buttons]
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"{prefix}{page-1}"
            ))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="➡️ Вперед", 
                callback_data=f"{prefix}{page+1}"
            ))
        inline_keyboard.append(nav_buttons)
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def keyboardSortirovka(buttons: list[str], callback_prefix: str = "btn_"):
    buttons_copy = buttons.copy()
    total = len(buttons_copy)
    num_long_positions = total // 3
    long_buttons = []
    temp_buttons = buttons_copy.copy()
    for _ in range(num_long_positions):
        longest_index = max(range(len(temp_buttons)), key=lambda x: len(temp_buttons[x]))
        long_buttons.append(temp_buttons.pop(longest_index))
    short_buttons = [b for b in buttons_copy if b not in long_buttons]
    keyboard = []
    i = 0
    short_index = 0
    long_index = 0
    while short_index < len(short_buttons) or long_index < len(long_buttons):
        group = []
        for _ in range(2):
            if short_index < len(short_buttons):
                group.append(short_buttons[short_index])
                short_index += 1
        if long_index < len(long_buttons):
            group.append(long_buttons[long_index])
            long_index += 1
        j = 0
        while j < len(group):
            row = [InlineKeyboardButton(text=group[j], callback_data=f"{callback_prefix}{i}")]
            i += 1
            j += 1
            if j < len(group):
                row.append(InlineKeyboardButton(text=group[j], callback_data=f"{callback_prefix}{i}"))
                i += 1
                j += 1
            keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def shops_keyboard(shops: list, callback_prefix="shop_"):
    semicolon = [s for s in shops if ";" in s["title"]]
    colon = [s for s in shops if ":" in s["title"] and s not in semicolon]
    regular = [s for s in shops if s not in semicolon and s not in colon]
    semicolon_titles = [s["title"] for s in semicolon]  
    colon_titles = [s["title"] for s in colon]          
    regular_titles = [s["title"] for s in regular]       
    keyboard = []
    index = 0
    while regular_titles or semicolon_titles or colon_titles:
        if regular_titles:
            row = []
            for _ in range(2):
                if regular_titles:
                    title = regular_titles.pop(0)
                    row.append(InlineKeyboardButton(
                        text=title,
                        callback_data=f"{callback_prefix}{index}"
                    ))
                    index += 1
            keyboard.append(row)
        if semicolon_titles or colon_titles:
            row = []
            if semicolon_titles:
                title = semicolon_titles.pop(0)
            else:
                title = colon_titles.pop(0)
            row.append(InlineKeyboardButton(
                text=title,
                callback_data=f"{callback_prefix}{index}"))
            index += 1
            keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)