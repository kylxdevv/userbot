# meta developer: @kylxdevvv
# scope: hikka_only
# scope: hikka_min 1.6.0

from typing import Dict, List, Set
import logging
from datetime import datetime

from hikkatl.types import Message
from hikkatl.tl.types import MessageEntityMention, MessageEntityTextUrl
from hikka import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class KeywordNotifierMod(loader.Module):
    """Уведомляет о ключевых словах в чатах"""

    strings = {
        "name": "KeywordNotifier",
        "config_header": "🔔 <b>Настройки KeywordNotifier</b>\n\n",
        "keywords_empty": "🚫 Список ключевых слов пуст",
        "keywords_list": "📋 <b>Текущие ключевые слова:</b>\n",
        "keyword_added": "✅ Ключевое слово <code>{}</code> добавлено",
        "keyword_removed": "🗑️ Ключевое слово <code>{}</code> удалено",
        "keyword_exists": "⚠️ Ключевое слово <code>{}</code> уже существует",
        "keyword_not_found": "❌ Ключевое слово <code>{}</code> не найдено",
        "chat_added": "✅ Чат <code>{}</code> добавлен в отслеживаемые",
        "chat_removed": "🗑️ Чат <code>{}</code> удален из отслеживаемых",
        "chat_exists": "⚠️ Чат <code>{}</code> уже отслеживается",
        "chat_not_found": "❌ Чат <code>{}</code> не найден в отслеживаемых",
        "chats_empty": "📭 Нет отслеживаемых чатов",
        "chats_list": "👥 <b>Отслеживаемые чаты:</b>\n",
        "notify_on": "🔔 Уведомления включены",
        "notify_off": "🔕 Уведомления выключены",
        "notify_already_on": "⚠️ Уведомления уже включены",
        "notify_already_off": "⚠️ Уведомления уже выключены",
        "help_text": """
🤖 <b>KeywordNotifier - помощь по командам</b>

<b>Основные команды:</b>
• <code>.kn add</code> <слово> - добавить ключевое слово
• <code>.kn remove</code> <слово> - удалить ключевое слово
• <code>.kn list</code> - список ключевых слов
• <code>.kn clear</code> - очистить все ключевые слова

<b>Управление чатами:</b>
• <code>.kn chatadd</code> - добавить текущий чат в отслеживаемые
• <code>.kn chatremove</code> - удалить текущий чат из отслеживаемых
• <code>.kn chatlist</code> - список отслеживаемых чатов
• <code>.kn chatclear</code> - очистить все чаты

<b>Настройки:</b>
• <code>.kn on</code> - включить уведомления
• <code>.kn off</code> - выключить уведомления
• <code>.kn status</code> - текущий статус
• <code>.kn config</code> - настройки модуля

<b>Пример:</b>
<code>.kn add срочно</code> - добавит слово "срочно"
<code>.kn add важн</code> - добавит слово "важно"
        """,
    }

    strings_ru = {
        "config_header": "🔔 <b>Настройки KeywordNotifier</b>\n\n",
        "keywords_empty": "🚫 Список ключевых слов пуст",
        "keywords_list": "📋 <b>Текущие ключевые слова:</b>\n",
        "keyword_added": "✅ Ключевое слово <code>{}</code> добавлено",
        "keyword_removed": "🗑️ Ключевое слово <code>{}</code> удалено",
        "keyword_exists": "⚠️ Ключевое слово <code>{}</code> уже существует",
        "keyword_not_found": "❌ Ключевое слово <code>{}</code> не найдено",
        "chat_added": "✅ Чат <code>{}</code> добавлен в отслеживаемые",
        "chat_removed": "🗑️ Чат <code>{}</code> удален из отслеживаемых",
        "chat_exists": "⚠️ Чат <code>{}</code> уже отслеживается",
        "chat_not_found": "❌ Чат <code>{}</code> не найден в отслеживаемых",
        "chats_empty": "📭 Нет отслеживаемых чатов",
        "chats_list": "👥 <b>Отслеживаемые чаты:</b>\n",
        "notify_on": "🔔 Уведомления включены",
        "notify_off": "🔕 Уведомления выключены",
        "notify_already_on": "⚠️ Уведомления уже включены",
        "notify_already_off": "⚠️ Уведомления уже выключены",
        "help_text": """
🤖 <b>KeywordNotifier - помощь по командам</b>

<b>Основные команды:</b>
• <code>.kn add</code> <слово> - добавить ключевое слово
• <code>.kn remove</code> <слово> - удалить ключевое слово
• <code>.kn list</code> - список ключевых слов
• <code>.kn clear</code> - очистить все ключевые слова

<b>Управление чатами:</b>
• <code>.kn chatadd</code> - добавить текущий чат в отслеживаемые
• <code>.kn chatremove</code> - удалить текущий чат из отслеживаемых
• <code>.kn chatlist</code> - список отслеживаемых чатов
• <code>.kn chatclear</code> - очистить все чаты

<b>Настройки:</b>
• <code>.kn on</code> - включить уведомления
• <code>.kn off</code> - выключить уведомления
• <code>.kn status</code> - текущий статус
• <code>.kn config</code> - настройки модуля

<b>Пример:</b>
<code>.kn add срочно</code> - добавит слово "срочно"
<code>.kn add важн</code> - добавит слово "важно"
        """,
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "keywords",
                [],
                lambda: "Список ключевых слов для отслеживания",
                validator=loader.validators.Series(
                    validator=loader.validators.String()
                ),
            ),
            loader.ConfigValue(
                "chats",
                [],
                lambda: "ID чатов для отслеживания",
                validator=loader.validators.Series(
                    validator=loader.validators.Integer()
                ),
            ),
            loader.ConfigValue(
                "enabled",
                True,
                lambda: "Включены ли уведомления",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "case_sensitive",
                False,
                lambda: "Чувствительность к регистру",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "exact_match",
                False,
                lambda: "Точное совпадение (иначе - частичное)",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "notify_self",
                False,
                lambda: "Уведомлять о своих сообщениях",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "ignore_commands",
                True,
                lambda: "Игнорировать команды",
                validator=loader.validators.Boolean(),
            ),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        logger.info("KeywordNotifier модуль загружен!")

    @loader.watcher(only_messages=True)
    async def watcher(self, message: Message):
        """Отслеживает сообщения на наличие ключевых слов"""
        
        # Проверяем, включены ли уведомления
        if not self.config["enabled"]:
            return

        # Проверяем, что сообщение из чата (не из лс с самим собой)
        if not message.is_group and not message.is_channel:
            return

        # Проверяем, отслеживается ли этот чат
        if message.chat_id not in self.config["chats"]:
            return

        # Игнорируем свои сообщения, если настроено
        if not self.config["notify_self"] and message.out:
            return

        # Игнорируем команды, если настроено
        if self.config["ignore_commands"] and message.raw_text.startswith("."):
            return

        # Проверяем наличие ключевых слов
        text = message.raw_text
        if not text:
            return

        found_keywords = []
        
        for keyword in self.config["keywords"]:
            if not keyword:
                continue

            search_text = text if self.config["case_sensitive"] else text.lower()
            search_keyword = keyword if self.config["case_sensitive"] else keyword.lower()

            if self.config["exact_match"]:
                # Точное совпадение (отдельное слово)
                words = search_text.split()
                if search_keyword in words:
                    found_keywords.append(keyword)
            else:
                # Частичное совпадение
                if search_keyword in search_text:
                    found_keywords.append(keyword)

        if found_keywords:
            await self._send_notification(message, found_keywords)

    async def _send_notification(self, message: Message, keywords: List[str]):
        """Отправляет уведомление о найденных ключевых словах"""
        
        try:
            # Получаем информацию о чате
            chat = await message.get_chat()
            chat_title = utils.get_display_name(chat)
            
            # Получаем информацию об отправителе
            sender = await message.get_sender()
            sender_name = utils.get_display_name(sender) if sender else "Неизвестно"
            
            # Формируем ссылку на сообщение
            msg_link = f"https://t.me/c/{str(message.chat_id).replace('-100', '')}/{message.id}"
            
            # Обрезаем текст если он слишком длинный
            text_preview = message.raw_text[:200] + "..." if len(message.raw_text) > 200 else message.raw_text
            
            notification_text = (
                f"🔔 <b>Обнаружено ключевое слово!</b>\n\n"
                f"<b>Чат:</b> {chat_title}\n"
                f"<b>Отправитель:</b> {sender_name}\n"
                f"<b>Ключевые слова:</b> <code>{', '.join(keywords)}</code>\n"
                f"<b>Сообщение:</b>\n<code>{utils.escape_html(text_preview)}</code>\n\n"
                f"<a href='{msg_link}'>Перейти к сообщению</a>"
            )
            
            # Отправляем уведомление себе
            await self._client.send_message(
                "me",
                notification_text,
                parse_mode="HTML",
                silent=False,
            )
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")

    @loader.command(ru_doc="Показать справку по командам")
    async def kncmd(self, message: Message):
        """Показать справку"""
        await utils.answer(message, self.strings("help_text"))

    @loader.command(ru_doc="Добавить ключевое слово")
    async def knaddcmd(self, message: Message):
        """Добавить ключевое слово для отслеживания"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Укажите ключевое слово")
            return

        keyword = args.strip()
        if keyword in self.config["keywords"]:
            await utils.answer(
                message, 
                self.strings("keyword_exists").format(utils.escape_html(keyword))
            )
            return

        keywords = self.config["keywords"].copy()
        keywords.append(keyword)
        self.config["keywords"] = keywords
        
        await utils.answer(
            message, 
            self.strings("keyword_added").format(utils.escape_html(keyword))
        )

    @loader.command(ru_doc="Удалить ключевое слово")
    async def knremovecmd(self, message: Message):
        """Удалить ключевое слово из отслеживания"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Укажите ключевое слово")
            return

        keyword = args.strip()
        if keyword not in self.config["keywords"]:
            await utils.answer(
                message, 
                self.strings("keyword_not_found").format(utils.escape_html(keyword))
            )
            return

        keywords = self.config["keywords"].copy()
        keywords.remove(keyword)
        self.config["keywords"] = keywords
        
        await utils.answer(
            message, 
            self.strings("keyword_removed").format(utils.escape_html(keyword))
        )

    @loader.command(ru_doc="Список ключевых слов")
    async def knlistcmd(self, message: Message):
        """Показать список ключевых слов"""
        if not self.config["keywords"]:
            await utils.answer(message, self.strings("keywords_empty"))
            return

        keywords_list = self.strings("keywords_list")
        for i, keyword in enumerate(self.config["keywords"], 1):
            keywords_list += f"{i}. <code>{utils.escape_html(keyword)}</code>\n"
        
        await utils.answer(message, keywords_list)

    @loader.command(ru_doc="Очистить все ключевые слова")
    async def knclearcmd(self, message: Message):
        """Очистить все ключевые слова"""
        self.config["keywords"] = []
        await utils.answer(message, "✅ Все ключевые слова удалены")

    @loader.command(ru_doc="Добавить текущий чат в отслеживаемые")
    async def knchataddcmd(self, message: Message):
        """Добавить текущий чат в отслеживаемые"""
        chat_id = message.chat_id
        
        if chat_id in self.config["chats"]:
            await utils.answer(
                message, 
                self.strings("chat_exists").format(chat_id)
            )
            return

        chats = self.config["chats"].copy()
        chats.append(chat_id)
        self.config["chats"] = chats
        
        await utils.answer(
            message, 
            self.strings("chat_added").format(chat_id)
        )

    @loader.command(ru_doc="Удалить текущий чат из отслеживаемых")
    async def knchatremovecmd(self, message: Message):
        """Удалить текущий чат из отслеживаемых"""
        chat_id = message.chat_id
        
        if chat_id not in self.config["chats"]:
            await utils.answer(
                message, 
                self.strings("chat_not_found").format(chat_id)
            )
            return

        chats = self.config["chats"].copy()
        chats.remove(chat_id)
        self.config["chats"] = chats
        
        await utils.answer(
            message, 
            self.strings("chat_removed").format(chat_id)
        )

    @loader.command(ru_doc="Список отслеживаемых чатов")
    async def knchatlistcmd(self, message: Message):
        """Показать список отслеживаемых чатов"""
        if not self.config["chats"]:
            await utils.answer(message, self.strings("chats_empty"))
            return

        try:
            chats_list = self.strings("chats_list")
            
            for i, chat_id in enumerate(self.config["chats"], 1):
                try:
                    chat = await self._client.get_entity(chat_id)
                    chat_name = utils.get_display_name(chat)
                    chats_list += f"{i}. {chat_name} (<code>{chat_id}</code>)\n"
                except:
                    chats_list += f"{i}. Неизвестный чат (<code>{chat_id}</code>)\n"
            
            await utils.answer(message, chats_list)
        except Exception as e:
            await utils.answer(message, f"❌ Ошибка: {str(e)}")

    @loader.command(ru_doc="Очистить все чаты")
    async def knchatclearcmd(self, message: Message):
        """Очистить все чаты из отслеживания"""
        self.config["chats"] = []
        await utils.answer(message, "✅ Все чаты удалены из отслеживания")

    @loader.command(ru_doc="Включить уведомления")
    async def knoncmd(self, message: Message):
        """Включить уведомления"""
        if self.config["enabled"]:
            await utils.answer(message, self.strings("notify_already_on"))
            return

        self.config["enabled"] = True
        await utils.answer(message, self.strings("notify_on"))

    @loader.command(ru_doc="Выключить уведомления")
    async def knoffcmd(self, message: Message):
        """Выключить уведомления"""
        if not self.config["enabled"]:
            await utils.answer(message, self.strings("notify_already_off"))
            return

        self.config["enabled"] = False
        await utils.answer(message, self.strings("notify_off"))

    @loader.command(ru_doc="Текущий статус модуля")
    async def knstatuscmd(self, message: Message):
        """Показать текущий статус модуля"""
        status_text = (
            f"🔔 <b>KeywordNotifier - Статус</b>\n\n"
            f"<b>Уведомления:</b> {'✅ Включены' if self.config['enabled'] else '❌ Выключены'}\n"
            f"<b>Ключевых слов:</b> {len(self.config['keywords'])}\n"
            f"<b>Отслеживаемых чатов:</b> {len(self.config['chats'])}\n"
            f"<b>Чувствительность к регистру:</b> {'✅ Да' if self.config['case_sensitive'] else '❌ Нет'}\n"
            f"<b>Точное совпадение:</b> {'✅ Да' if self.config['exact_match'] else '❌ Нет'}\n"
            f"<b>Уведомлять о своих сообщениях:</b> {'✅ Да' if self.config['notify_self'] else '❌ Нет'}\n"
            f"<b>Игнорировать команды:</b> {'✅ Да' if self.config['ignore_commands'] else '❌ Нет'}\n"
        )
        
        await utils.answer(message, status_text)

    @loader.command(ru_doc="Настройки модуля")
    async def knconfigcmd(self, message: Message):
        """Показать настройки модуля"""
        config_text = self.strings("config_header")
        
        # Ключевые слова
        if self.config["keywords"]:
            config_text += "<b>Ключевые слова:</b>\n"
            for kw in self.config["keywords"][:10]:  # Показываем первые 10
                config_text += f"• <code>{utils.escape_html(kw)}</code>\n"
            if len(self.config["keywords"]) > 10:
                config_text += f"... и ещё {len(self.config['keywords']) - 10}\n"
        else:
            config_text += "<b>Ключевые слова:</b> Нет\n"
        
        config_text += "\n"
        
        # Чаты
        if self.config["chats"]:
            config_text += f"<b>Отслеживаемых чатов:</b> {len(self.config['chats'])}\n"
        else:
            config_text += "<b>Отслеживаемых чатов:</b> Нет\n"
        
        config_text += (
            f"\n<b>Другие настройки:</b>\n"
            f"• Уведомления: {'✅' if self.config['enabled'] else '❌'}\n"
            f"• Регистр: {'✅' if self.config['case_sensitive'] else '❌'}\n"
            f"• Точное совпадение: {'✅' if self.config['exact_match'] else '❌'}\n"
            f"• Свои сообщения: {'✅' if self.config['notify_self'] else '❌'}\n"
            f"• Игнорировать команды: {'✅' if self.config['ignore_commands'] else '❌'}\n"
        )
        
        await utils.answer(message, config_text)
