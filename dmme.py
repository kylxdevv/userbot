# meta developer: @kylxdevvv
# scope: hikka_only
# scope: hikka_min 1.6.0

from typing import List
import logging
import html

from hikkatl.types import Message
from hikka import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class KeywordNotifierMod(loader.Module):
    """Уведомляет о ключевых словах в чатах"""

    strings = {
        "name": "KeywordNotifier",
        "keywords_empty": "🚫 Список ключевых слов пуст",
        "keywords_list": "📋 <b>Текущие ключевые слова:</b>\n",
        "keyword_added": "✅ Ключевое слово <code>{}</code> добавлено",
        "keyword_removed": "🗑️ Ключевое слово <code>{}</code> удалено",
        "keyword_exists": "⚠️ Ключевое слово <code>{}</code> уже существует",
        "keyword_not_found": "❌ Ключевое слово <code>{}</code> не найдено",
        "chat_set": "✅ Чат для уведомлений установлен",
        "chat_removed": "🗑️ Чат для уведомлений удален",
        "chat_not_set": "❌ Чат для уведомлений не установлен",
        "notify_on": "🔔 Уведомления включены",
        "notify_off": "🔕 Уведомления выключены",
        "notify_already_on": "⚠️ Уведомления уже включены",
        "notify_already_off": "⚠️ Уведомления уже выключены",
        "help_text": """
🤖 <b>KeywordNotifier - помощь по командам</b>

<b>Основные команды:</b>
• <code>.knadd</code> <слово> - добавить ключевое слово
• <code>.knremove</code> <слово> - удалить ключевое слово
• <code>.knlist</code> - список ключевых слов
• <code>.knclear</code> - очистить все ключевые слова

<b>Управление чатом для уведомлений:</b>
• <code>.knchat</code> - установить текущий чат для уведомлений
• <code>.knunchat</code> - удалить чат для уведомлений
• <code>.knstatus</code> - информация о настройках

<b>Настройки:</b>
• <code>.knon</code> - включить уведомления
• <code>.knoff</code> - выключить уведомления

<b>Пример:</b>
<code>.knadd срочно</code> - добавит слово "срочно"
<code>.knadd важн</code> - добавит слово "важно"
        """,
    }

    strings_ru = {
        "keywords_empty": "🚫 Список ключевых слов пуст",
        "keywords_list": "📋 <b>Текущие ключевые слова:</b>\n",
        "keyword_added": "✅ Ключевое слово <code>{}</code> добавлено",
        "keyword_removed": "🗑️ Ключевое слово <code>{}</code> удалено",
        "keyword_exists": "⚠️ Ключевое слово <code>{}</code> уже существует",
        "keyword_not_found": "❌ Ключевое слово <code>{}</code> не найдено",
        "chat_set": "✅ Чат для уведомлений установлен",
        "chat_removed": "🗑️ Чат для уведомлений удален",
        "chat_not_set": "❌ Чат для уведомлений не установлен",
        "notify_on": "🔔 Уведомления включены",
        "notify_off": "🔕 Уведомления выключены",
        "notify_already_on": "⚠️ Уведомления уже включены",
        "notify_already_off": "⚠️ Уведомления уже выключены",
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
                "notify_chat",
                None,
                lambda: "ID чата для уведомлений",
                validator=loader.validators.Union(
                    [loader.validators.Integer(), loader.validators.NoneType()]
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

        # Проверяем, что есть чат для уведомлений
        if not self.config["notify_chat"]:
            return

        # Проверяем, что сообщение из группового чата или канала
        if not message.is_group and not message.is_channel:
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
            chat = message.chat
            chat_title = chat.title if hasattr(chat, 'title') else "Чат"
            
            # Получаем информацию об отправителе
            sender = message.sender
            if sender:
                # Получаем username или first_name
                if sender.username:
                    sender_name = f"@{sender.username}"
                elif sender.first_name:
                    sender_name = sender.first_name
                    if sender.last_name:
                        sender_name += f" {sender.last_name}"
                else:
                    sender_name = "Неизвестно"
            else:
                sender_name = "Неизвестно"
            
            # Формируем ссылку на сообщение
            if hasattr(chat, 'username') and chat.username:
                chat_link = f"https://t.me/{chat.username}/{message.id}"
            else:
                # Для приватных чатов и супергрупп
                chat_id = str(message.chat_id).replace('-100', '')
                chat_link = f"https://t.me/c/{chat_id}/{message.id}"
            
            # Обрезаем текст если он слишком длинный
            text_preview = message.raw_text[:200] + "..." if len(message.raw_text) > 200 else message.raw_text
            
            # Экранируем HTML символы
            safe_text = html.escape(text_preview)
            
            notification_text = (
                f"🔔 <b>Обнаружено ключевое слово!</b>\n\n"
                f"<b>Чат:</b> {html.escape(chat_title)}\n"
                f"<b>Отправитель:</b> {sender_name}\n"
                f"<b>Ключевые слова:</b> <code>{', '.join(keywords)}</code>\n"
                f"<b>Сообщение:</b>\n<code>{safe_text}</code>\n\n"
                f"<a href='{chat_link}'>🔗 Перейти к сообщению</a>"
            )
            
            # Отправляем уведомление в прикрепленный чат
            await self._client.send_message(
                self.config["notify_chat"],
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
                self.strings("keyword_exists").format(html.escape(keyword))
            )
            return

        keywords = self.config["keywords"].copy()
        keywords.append(keyword)
        self.config["keywords"] = keywords
        
        await utils.answer(
            message, 
            self.strings("keyword_added").format(html.escape(keyword))
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
                self.strings("keyword_not_found").format(html.escape(keyword))
            )
            return

        keywords = self.config["keywords"].copy()
        keywords.remove(keyword)
        self.config["keywords"] = keywords
        
        await utils.answer(
            message, 
            self.strings("keyword_removed").format(html.escape(keyword))
        )

    @loader.command(ru_doc="Список ключевых слов")
    async def knlistcmd(self, message: Message):
        """Показать список ключевых слов"""
        if not self.config["keywords"]:
            await utils.answer(message, self.strings("keywords_empty"))
            return

        keywords_list = self.strings("keywords_list")
        for i, keyword in enumerate(self.config["keywords"], 1):
            keywords_list += f"{i}. <code>{html.escape(keyword)}</code>\n"
        
        await utils.answer(message, keywords_list)

    @loader.command(ru_doc="Очистить все ключевые слова")
    async def knclearcmd(self, message: Message):
        """Очистить все ключевые слова"""
        self.config["keywords"] = []
        await utils.answer(message, "✅ Все ключевые слова удалены")

    @loader.command(ru_doc="Установить чат для уведомлений")
    async def knchatcmd(self, message: Message):
        """Установить текущий чат для получения уведомлений"""
        chat_id = message.chat_id
        self.config["notify_chat"] = chat_id
        
        await utils.answer(
            message, 
            self.strings("chat_set")
        )

    @loader.command(ru_doc="Удалить чат для уведомлений")
    async def knunchatcmd(self, message: Message):
        """Удалить чат для уведомлений"""
        self.config["notify_chat"] = None
        await utils.answer(
            message, 
            self.strings("chat_removed")
        )

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
        
        # Получаем информацию о чате для уведомлений
        notify_chat_info = "❌ Не установлен"
        if self.config["notify_chat"]:
            try:
                chat = await self._client.get_entity(self.config["notify_chat"])
                if hasattr(chat, 'title'):
                    notify_chat_info = f"✅ {chat.title}"
                elif hasattr(chat, 'username'):
                    notify_chat_info = f"✅ @{chat.username}"
                else:
                    notify_chat_info = f"✅ ID: {self.config['notify_chat']}"
            except:
                notify_chat_info = f"✅ ID: {self.config['notify_chat']}"

        status_text = (
            f"🔔 <b>KeywordNotifier - Статус</b>\n\n"
            f"<b>Уведомления:</b> {'✅ Включены' if self.config['enabled'] else '❌ Выключены'}\n"
            f"<b>Ключевых слов:</b> {len(self.config['keywords'])}\n"
            f"<b>Чат для уведомлений:</b> {notify_chat_info}\n"
            f"<b>Чувствительность к регистру:</b> {'✅ Да' if self.config['case_sensitive'] else '❌ Нет'}\n"
            f"<b>Точное совпадение:</b> {'✅ Да' if self.config['exact_match'] else '❌ Нет'}\n"
            f"<b>Уведомлять о своих сообщениях:</b> {'✅ Да' if self.config['notify_self'] else '❌ Нет'}\n"
            f"<b>Игнорировать команды:</b> {'✅ Да' if self.config['ignore_commands'] else '❌ Нет'}\n"
        )
        
        if self.config["keywords"]:
            status_text += f"\n<b>Ключевые слова:</b>\n"
            for kw in self.config["keywords"][:5]:  # Показываем первые 5
                status_text += f"• <code>{html.escape(kw)}</code>\n"
            if len(self.config["keywords"]) > 5:
                status_text += f"... и ещё {len(self.config['keywords']) - 5}\n"
        
        await utils.answer(message, status_text)
