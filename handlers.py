from aiogram import Router, F 
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, CallbackQuery
import keyboards as kb
import database
from config import ADMINS
from states import Spam, AddTheme, AddShop,EditShop
import asyncio
import os

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    user = await database.pool.fetchrow("SELECT user_id FROM users WHERE user_id=$1", user_id)
    if not user:
        await database.pool.execute(
            "INSERT INTO users (user_id, username) VALUES ($1, $2)",
            user_id, username)
    video = FSInputFile("startvideo.mp4") 
    await message.answer_video(
        video=video,
        caption="Добро пожаловать в СигмаШоп",
        reply_markup=kb.On1)
    

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("🚫 У тебя нет доступа к админке.")
        return
    user_count = await database.count_users()
    text1 = ("👑 Добро пожаловать в админ-панель!\n"
        f"👥 Пользователей в базе: <b>{user_count}</b>")
    await message.answer(text1, reply_markup=kb.admin_menu,parse_mode="HTML")


@router.callback_query(F.data == "spam")
async def start_spam(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer("🚫 Нет доступа!", show_alert=True)
        return
    await callback.message.answer(
        "📨 Отправь сообщение для рассылки.\n"
        "<b>Можно прикрепить:</b> фото, видео или просто текст.\n"
        "Разметка <b>HTML</b> поддерживается.",
        parse_mode="HTML")
    await state.set_state(Spam.waiting_for_message)
@router.message(Spam.waiting_for_message)
async def process_spam_message(message: Message, state: FSMContext):
    await state.clear()
    users = await database.pool.fetch("SELECT user_id FROM users")
    total = len(users)
    success = 0
    await message.answer(f"🚀 Начинаю рассылку {total} пользователям...")
    file_path = None
    media_type = None
    if message.photo:
        media_type = "photo"
        file = await message.bot.get_file(message.photo[-1].file_id)
        file_path = os.path.abspath(f"temp_photo_{message.photo[-1].file_id}.jpg")
        await message.bot.download(file, destination=file_path)
    elif message.video:
        media_type = "video"
        file = await message.bot.get_file(message.video.file_id)
        file_path = os.path.abspath(f"temp_video_{message.video.file_id}.mp4")
        await message.bot.download(file, destination=file_path)
    for user in users:
        user_id = user["user_id"]
        try:
            if media_type == "photo":
                await message.bot.send_photo(
                    user_id,
                    photo=FSInputFile(file_path),
                    caption=message.caption or "",
                    parse_mode="HTML")
            elif media_type == "video":
                await message.bot.send_video(
                    user_id,
                    video=FSInputFile(file_path),
                    caption=message.caption or "",
                    parse_mode="HTML")
            else:
                await message.bot.send_message(
                    user_id,
                    text=message.text or "",
                    parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"❌ Ошибка при отправке пользователю {user_id}: {e}")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    await message.answer(
        f"✅ Рассылка завершена!\n📬 Отправлено: <b>{success}</b> из <b>{total}</b>",
        parse_mode="HTML")


@router.callback_query(F.data == "add_theme")
async def add_theme_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer("🚫 Нет доступа!", show_alert=True)
        return
    await callback.message.answer("📝 Введите название темы:")
    await state.set_state(AddTheme.waiting_for_title)
@router.message(AddTheme.waiting_for_title)
async def add_theme_finish(message: Message, state: FSMContext):
    title = message.text.strip()
    await database.add_theme(title)
    await message.answer(f"✅ Тема <b>{title}</b> успешно добавлена!", parse_mode="HTML")
    await state.clear()
@router.message(F.text == "Магазины")
async def show_themes(message: Message):
    themes = await database.get_themes()
    if not themes:
        await message.answer("😕 Тем пока нет.")
        return
    keyboard = kb.keyboardSortirovka(themes, callback_prefix="theme_")
    await message.answer("📂 Выберите тему:", reply_markup=keyboard)

@router.callback_query(F.data == "delete_theme")
async def delete_theme_start(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        await callback.answer("🚫 Нет доступа!", show_alert=True)
        return
    themes = await database.get_themes()
    if not themes:
        await callback.message.answer("❕ Пока нет тем для удаления.")
        return
    keyboard = kb.keyboardSortirovka(themes, callback_prefix="deltheme_")
    await callback.message.answer("🗑 Выберите тему, которую хотите удалить:",
        reply_markup=keyboard)
@router.callback_query(F.data.startswith("deltheme_"))
async def delete_theme(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return await callback.answer("🚫 Нет доступа!", show_alert=True)
    index = int(callback.data.split("_")[1])
    button_text = None
    for row in callback.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == f"deltheme_{index}":
                button_text = btn.text
                break
    if not button_text:
        return await callback.answer("❌ Ошибка. Темы не найдена.", show_alert=True)
    await database.delete_theme(button_text)
    await callback.message.answer(
        f"🗑 Тема <b>{button_text}</b> успешно удалена!",
        parse_mode="HTML")


@router.callback_query(F.data == "add_shop")
async def add_shop_choose_theme(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return await callback.answer("🚫 Нет доступа!", show_alert=True)
    themes = await database.get_themes()
    if not themes:
        return await callback.message.answer("❗ Нет тем. Создайте тему сначала.")
    keyboard = kb.keyboardSortirovka(themes, callback_prefix="addshop_theme_")
    await callback.message.answer("📂 Выберите тему, куда добавить магазин:", reply_markup=keyboard)
@router.callback_query(F.data.startswith("addshop_theme_"))
async def add_shop_ask_title(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[2])
    theme_title = None
    for row in callback.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == f"addshop_theme_{index}":
                theme_title = btn.text
                break
        if theme_title:
            break
    if not theme_title:
        return await callback.answer("❗ Ошибка выбора темы.", show_alert=True)
    theme_id = await database.pool.fetchval(
        "SELECT id FROM themes WHERE title=$1", theme_title)
    await state.update_data(theme_id=theme_id)
    await state.set_state(AddShop.waiting_for_title)
    await callback.message.answer("📝 Введите название магазина:")
@router.message(AddShop.waiting_for_title)
async def add_shop_save(message: Message, state: FSMContext):
    data = await state.get_data()
    theme_id = data["theme_id"]
    title = message.text.strip()
    await database.add_shop(theme_id, title)
    await state.clear()
    await message.answer(
        f"🏪 Магазин <b>{title}</b> добавлен!",
        parse_mode="HTML")
@router.callback_query(F.data.startswith("theme_"))
async def open_theme(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    theme_title = None
    for row in callback.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == f"theme_{index}":
                theme_title = btn.text
                break
        if theme_title:
            break
    if not theme_title:
        return await callback.answer("❗ Ошибка выбора темы.", show_alert=True)
    theme_id = await database.pool.fetchval(
        "SELECT id FROM themes WHERE title=$1",
        theme_title)
    shops = await database.get_shops(theme_id)
    keyboard = kb.shops_keyboard(shops, callback_prefix="shop_")
    await callback.message.answer(
        f"📂 Тема: <b>{theme_title}</b>\nВыберите магазин:",
        reply_markup=keyboard,
        parse_mode="HTML")
@router.callback_query(F.data.startswith("shop_"))
async def open_shop(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    shop_title = None
    for row in callback.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == f"shop_{index}":
                shop_title = btn.text
                break
    shop = await database.get_shop_by_title(shop_title)
    if not shop:
        return await callback.answer("❗ Магазин не найден.", show_alert=True)
    likes = await database.get_shop_likes(shop["id"])
    keyboard = kb.like_keyboard(shop["id"], likes)
    if shop["photo"]:
        await callback.message.answer_photo(
            photo=FSInputFile(shop["photo"]),
            caption=shop["description"],
            parse_mode="HTML",
            reply_markup=keyboard)
    else:
        await callback.message.answer(
            shop["description"],
            parse_mode="HTML",
            reply_markup=keyboard)

@router.callback_query(F.data == "delete_shop")
async def delete_shop_choose_theme(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return await callback.answer("🚫 Нет доступа!", show_alert=True)
    themes = await database.get_themes()
    if not themes:
        return await callback.message.answer("❗ Нет тем.")
    keyboard = kb.keyboardSortirovka(themes, callback_prefix="delshop_theme_")
    await callback.message.answer(
        "🗑 Выберите тему, из которой хотите удалить магазин:",
        reply_markup=keyboard)
@router.callback_query(F.data.startswith("delshop_theme_"))
async def delete_shop_choose_shop(callback: CallbackQuery):
    index = int(callback.data.split("_")[2])
    theme_title = None
    for row in callback.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == f"delshop_theme_{index}":
                theme_title = btn.text
                break
        if theme_title:
            break
    if not theme_title:
        return await callback.answer("❗ Ошибка выбора темы.", show_alert=True)
    theme_id = await database.pool.fetchval(
        "SELECT id FROM themes WHERE title=$1",
        theme_title)
    shops = await database.get_shops(theme_id)
    if not shops:
        return await callback.message.answer("❗ В этой теме нет магазинов.")
    keyboard = kb.shops_keyboard(shops, callback_prefix="delshop_")
    await callback.message.answer(
        f"🗑 Тема: <b>{theme_title}</b>\nВыберите магазин для удаления:",
        reply_markup=keyboard,
        parse_mode="HTML")
@router.callback_query(F.data.startswith("delshop_"))
async def delete_shop_final(callback: CallbackQuery):
    delete_prefix, index = callback.data.split("_")
    index = int(index)
    shop_title = None
    for row in callback.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == f"delshop_{index}":
                shop_title = btn.text
                break
    if not shop_title:
        return await callback.answer("❗ Ошибка. Магазин не найден.", show_alert=True)
    await database.delete_shop_by_title(shop_title)
    await callback.message.answer(
        f"🗑 Магазин <b>{shop_title}</b> успешно удалён!",
        parse_mode="HTML")
    

@router.callback_query(F.data == "edit_shop")
async def edit_shop_choose_theme(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return await callback.answer("🚫 Нет доступа!", show_alert=True)
    themes = await database.get_themes()
    keyboard = kb.keyboardSortirovka(themes, callback_prefix="editshop_theme_")
    await callback.message.answer("📂 Выберите тему:", reply_markup=keyboard)
@router.callback_query(F.data.startswith("editshop_theme_"))
async def edit_shop_choose_shop(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[2])
    theme_title = None
    for row in callback.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == f"editshop_theme_{index}":
                theme_title = btn.text
                break
        if theme_title:
            break
    theme_id = await database.pool.fetchval(
        "SELECT id FROM themes WHERE title=$1", theme_title)
    shops = await database.get_shops(theme_id)
    keyboard = kb.shops_keyboard(shops, callback_prefix="editshop_")
    await callback.message.answer("🏪 Выберите магазин:", reply_markup=keyboard)
@router.callback_query(F.data.startswith("editshop_"))
async def edit_shop_start(callback: CallbackQuery, state: FSMContext):
    index = int(callback.data.split("_")[1])
    shop_title = None
    for row in callback.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == f"editshop_{index}":
                shop_title = btn.text
                break
    await state.update_data(shop_title=shop_title)
    await callback.message.answer("🖼 Отправь фото магазина или нажми кнопку ниже:",
        reply_markup=kb.skip_keyboard,
        parse_mode="HTML")
    await state.set_state(EditShop.waiting_for_photo)
@router.message(EditShop.waiting_for_photo)
async def edit_shop_get_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    shop_title = data["shop_title"]
    if message.photo:
        file = await message.bot.get_file(message.photo[-1].file_id)
        photo_path = f"shop_{shop_title}.jpg"
        await message.bot.download(file, photo_path)
        await state.update_data(photo=photo_path)
        await message.answer(
            "✏ Теперь отправь описание магазина (HTML разрешён):",
            parse_mode="HTML")
        await state.set_state(EditShop.waiting_for_description)
        return
    return await message.answer("❗ Отправь фото или нажми кнопку «Пропустить».")
@router.callback_query(F.data == "skip_photo")
async def skip_shop_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo=None)
    await callback.message.answer(
        "✏ Теперь отправь описание магазина (HTML разрешён):",
        parse_mode="HTML")
    await state.set_state(EditShop.waiting_for_description)
@router.message(EditShop.waiting_for_description)
async def edit_shop_save(message: Message, state: FSMContext):
    data = await state.get_data()
    shop_title = data["shop_title"]
    photo = data.get("photo")
    description = message.html_text
    await database.update_shop_description(shop_title, description, photo)
    await state.clear()
    await message.answer(
        f"✅ Описание магазина <b>{shop_title}</b> обновлено!",
        parse_mode="HTML")
@router.callback_query(F.data.startswith("shop_"))
async def open_shop(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    shop_title = None
    for row in callback.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == f"shop_{index}":
                shop_title = btn.text
                break
    shop = await database.get_shop_by_title(shop_title)
    if not shop:
        return await callback.answer("❗ Магазин не найден.", show_alert=True)
    if shop["photo"]:
        await callback.message.answer_photo(
            photo=FSInputFile(shop["photo"]),
            caption=shop["description"],
            parse_mode="HTML")
    else:
        await callback.message.answer(
            shop["description"],
            parse_mode="HTML")
        

@router.callback_query(F.data.startswith("like_shop_"))
async def like_shop(callback: CallbackQuery):
    shop_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    if await database.has_liked(user_id, shop_id):
        return await callback.answer("Ты уже лайкнул этот магазин ❤️", show_alert=True)
    await database.add_like(user_id, shop_id)
    likes = await database.get_shop_likes(shop_id)
    await callback.message.edit_reply_markup(
        reply_markup=kb.like_keyboard(shop_id, likes))
    await callback.answer("Спасибо за лайк! ❤️")