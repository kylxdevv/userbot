# meta developer: @kylxdevvv
# scope: hikka_only

from typing import List
import html

from hikkatl.types import Message
from hikka import loader, utils


@loader.tds
class KeywordNotifierMod(loader.Module):
    """Уведомляет о ключевых словах в чатах"""
    
    strings = {
        "name": "KeywordNotifier",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "keywords",
                [],
                lambda: "Ключевые слова",
                validator=loader.validators.Series(validator=loader.validators.String()),
            ),
            loader.ConfigValue(
                "notify_chat",
                None,
                lambda: "Чат для уведомлений",
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "enabled",
                True,
                lambda: "Включено",
                validator=loader.validators.Boolean(),
            ),
        )
        self._notify_chat = None

    async def client_ready(self, client, db):
        self._client = client
        if self.config["notify_chat"]:
            self._notify_chat = self.config["notify_chat"]

    @loader.watcher()
    async def watcher(self, message: Message):
        if not self.config["enabled"] or not self._notify_chat:
            return
            
        if not message.text:
            return
            
        text = message.text.lower()
        
        for keyword in self.config["keywords"]:
            if not keyword:
                continue
                
            if keyword.lower() in text:
                await self._send_notification(message, keyword)
                break

    async def _send_notification(self, message: Message, keyword: str):
        try:
            # Получаем имя отправителя
            sender = message.sender
            sender_name = "Неизвестно"
            if sender:
                if sender.username:
                    sender_name = f"@{sender.username}"
                elif sender.first_name:
                    sender_name = sender.first_name
                    if sender.last_name:
                        sender_name += f" {sender.last_name}"
            
            # Ссылка на сообщение
            chat = message.chat
            if hasattr(chat, 'username') and chat.username:
                link = f"https://t.me/{chat.username}/{message.id}"
            else:
                chat_id = str(message.chat_id).replace('-100', '')
                link = f"https://t.me/c/{chat_id}/{message.id}"
            
            # Текст сообщения
            text_preview = message.text[:100] + "..." if len(message.text) > 100 else message.text
            safe_text = html.escape(text_preview)
            
            # Отправляем уведомление
            await self._client.send_message(
                self._notify_chat,
                f"🔔 <b>Найдено слово:</b> <code>{keyword}</code>\n"
                f"<b>От:</b> {sender_name}\n"
                f"<b>Текст:</b> {safe_text}\n"
                f"<a href='{link}'>Перейти</a>",
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Ошибка: {e}")

    @loader.command()
    async def knadd(self, message: Message):
        """Добавить ключевое слово"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Укажите слово")
            return
            
        keyword = args.strip()
        keywords = self.config["keywords"].copy()
        
        if keyword in keywords:
            await utils.answer(message, "⚠️ Уже есть")
            return
            
        keywords.append(keyword)
        self.config["keywords"] = keywords
        await utils.answer(message, f"✅ Добавлено: <code>{html.escape(keyword)}</code>")

    @loader.command()
    async def knremove(self, message: Message):
        """Удалить ключевое слово"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Укажите слово")
            return
            
        keyword = args.strip()
        keywords = self.config["keywords"].copy()
        
        if keyword not in keywords:
            await utils.answer(message, "❌ Не найдено")
            return
            
        keywords.remove(keyword)
        self.config["keywords"] = keywords
        await utils.answer(message, f"🗑️ Удалено: <code>{html.escape(keyword)}</code>")

    @loader.command()
    async def knlist(self, message: Message):
        """Список ключевых слов"""
        if not self.config["keywords"]:
            await utils.answer(message, "📭 Список пуст")
            return
            
        text = "📋 <b>Ключевые слова:</b>\n"
        for i, kw in enumerate(self.config["keywords"], 1):
            text += f"{i}. <code>{html.escape(kw)}</code>\n"
            
        await utils.answer(message, text)

    @loader.command()
    async def knchat(self, message: Message):
        """Установить чат для уведомлений"""
        self.config["notify_chat"] = message.chat_id
        self._notify_chat = message.chat_id
        await utils.answer(message, "✅ Чат установлен")

    @loader.command()
    async def knon(self, message: Message):
        """Включить уведомления"""
        self.config["enabled"] = True
        await utils.answer(message, "🔔 Включено")

    @loader.command()
    async def knoff(self, message: Message):
        """Выключить уведомления"""
        self.config["enabled"] = False
        await utils.answer(message, "🔕 Выключено")

    @loader.command()
    async def knstatus(self, message: Message):
        """Статус модуля"""
        status = "🟢 Включено" if self.config["enabled"] else "🔴 Выключено"
        chat_info = f"ID: {self._notify_chat}" if self._notify_chat else "❌ Не установлен"
        
        text = (
            f"🔔 <b>KeywordNotifier</b>\n\n"
            f"<b>Статус:</b> {status}\n"
            f"<b>Чат уведомлений:</b> {chat_info}\n"
            f"<b>Ключевых слов:</b> {len(self.config['keywords'])}"
        )
        
        await utils.answer(message, text)
