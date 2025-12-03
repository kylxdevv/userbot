# meta developer: @kylxdevvv
# meta pic: https://img.icons8.com/color/96/000000/telegram-app.png
# meta banner: https://img.icons8.com/color/480/000000/telegram-app.png
# scope: hikka_only
# requires: telethon

__version__ = (1, 0, 0)

import asyncio
import random
import string
import logging
from datetime import datetime

from telethon.tl.functions.channels import CreateChannelRequest, UpdateUsernameRequest
from telethon.tl.functions.messages import GetDialogFiltersRequest, UpdateDialogFilterRequest, ExportChatInviteRequest
from telethon.tl.types import DialogFilter, InputPeerChannel, InputChannel
from telethon.errors import (
    UsernameOccupiedError, 
    UsernameInvalidError, 
    FloodWaitError,
    ChannelsTooMuchError
)

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class KylxCreatorMod(loader.Module):
    """Создатель публичных каналов с 4-буквенными ссылками"""
    
    strings = {
        "name": "KylxCreator",
        "started": "🚀 Создание публичных каналов запущено!",
        "stopped": "🛑 Создание каналов остановлено",
        "already_started": "Уже запущено!",
        "already_stopped": "Уже остановлено!",
        "stats": """📊 Статистика:
✅ Создано: {}
❌ Ошибок: {}
📈 Успешность: {}%
⏱️ Время работы: {}
""",
    }
    
    def __init__(self):
        self.is_active = False
        self.task = None
        self.created = 0
        self.errors = 0
        self.start_time = None
        self.channels = []
        self.folder_id = None
        
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.channels = self.db.get(__name__, "channels", [])
        self.created = len(self.channels)
    
    def generate_name(self):
        """Генерирует 4-буквенное имя"""
        return ''.join(random.choices(string.ascii_lowercase, k=4))
    
    async def ensure_folder(self):
        """Создает папку если нет"""
        try:
            folders = await self.client(GetDialogFiltersRequest())
            
            # Ищем папку Kylx
            for f in folders:
                if hasattr(f, 'title') and f.title == "KylxChannels":
                    self.folder_id = f.id
                    return True
            
            # Создаем новую папку
            folder_ids = [f.id for f in folders if hasattr(f, 'id')]
            new_id = max(folder_ids) + 1 if folder_ids else 2
            
            folder = DialogFilter(
                id=new_id,
                title="KylxChannels",
                emoji="📢",
                color=6,
                pinned_peers=[],
                include_peers=[],
                exclude_peers=[],
                contacts=False,
                non_contacts=False,
                groups=False,
                broadcasts=True,
                bots=False,
                exclude_muted=False,
                exclude_read=False,
                exclude_archived=False,
            )
            
            await self.client(UpdateDialogFilterRequest(id=new_id, filter=folder))
            self.folder_id = new_id
            return True
            
        except Exception as e:
            logger.error(f"Folder error: {e}")
            return False
    
    async def add_to_folder(self, channel_id, access_hash):
        """Добавляет канал в папку"""
        try:
            if not self.folder_id:
                await self.ensure_folder()
            
            folders = await self.client(GetDialogFiltersRequest())
            folder = None
            
            for f in folders:
                if f.id == self.folder_id:
                    folder = f
                    break
            
            if not folder:
                return False
            
            # Собираем текущие каналы
            peers = folder.include_peers.copy() if hasattr(folder, 'include_peers') else []
            
            # Проверяем дубликаты
            for p in peers:
                if hasattr(p, 'channel_id') and p.channel_id == channel_id:
                    return True
            
            # Добавляем новый
            peers.append(InputPeerChannel(channel_id, access_hash))
            
            # Обновляем папку
            updated = DialogFilter(
                id=self.folder_id,
                title="KylxChannels",
                emoji="📢",
                color=6,
                pinned_peers=[],
                include_peers=peers,
                exclude_peers=[],
                contacts=False,
                non_contacts=False,
                groups=False,
                broadcasts=True,
                bots=False,
                exclude_muted=False,
                exclude_read=False,
                exclude_archived=False,
            )
            
            await self.client(UpdateDialogFilterRequest(id=self.folder_id, filter=updated))
            return True
            
        except Exception as e:
            logger.error(f"Add to folder error: {e}")
            return False
    
    async def create_channel(self):
        """Создает один канал"""
        attempts = 0
        
        while attempts < 50 and self.is_active:
            name = self.generate_name()
            
            try:
                logger.info(f"Creating: {name}")
                
                # Создаем канал
                result = await self.client(CreateChannelRequest(
                    title=f"Kylx {name}",
                    about="Auto created",
                    megagroup=False,
                    for_import=False
                ))
                
                channel = result.chats[0]
                
                # Делаем публичным
                await self.client(UpdateUsernameRequest(
                    channel=InputChannel(channel.id, channel.access_hash),
                    username=name
                ))
                
                # Создаем ссылку
                try:
                    invite = await self.client(ExportChatInviteRequest(
                        peer=InputPeerChannel(channel.id, channel.access_hash),
                        legacy_revoke_permanent=True
                    ))
                    invite_link = invite.link
                except:
                    invite_link = f"https://t.me/{name}"
                
                # Добавляем в папку
                in_folder = await self.add_to_folder(channel.id, channel.access_hash)
                
                # Сохраняем
                self.channels.append({
                    'name': name,
                    'id': channel.id,
                    'hash': channel.access_hash,
                    'link': f"https://t.me/{name}",
                    'invite': invite_link,
                    'time': datetime.now().isoformat(),
                    'folder': in_folder
                })
                
                self.db.set(__name__, "channels", self.channels)
                self.created += 1
                
                logger.info(f"Created: t.me/{name}")
                return True
                
            except UsernameOccupiedError:
                attempts += 1
                await asyncio.sleep(0.3)
                
            except UsernameInvalidError:
                attempts += 1
                await asyncio.sleep(0.3)
                
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                
            except ChannelsTooMuchError:
                self.is_active = False
                return False
                
            except Exception as e:
                logger.error(f"Error: {e}")
                self.errors += 1
                attempts += 1
                await asyncio.sleep(2)
        
        self.errors += 1
        return False
    
    async def loop(self):
        """Основной цикл"""
        await self.ensure_folder()
        
        while self.is_active:
            success = await self.create_channel()
            
            if not self.is_active:
                break
            
            if success:
                await asyncio.sleep(random.uniform(20, 40))
            else:
                await asyncio.sleep(random.uniform(5, 10))
    
    @loader.command(
        ru_doc="Запустить создание каналов",
        alias="kylxstart"
    )
    async def kylxconcmd(self, message):
        """Запустить создание"""
        if self.is_active:
            await utils.answer(message, self.strings("already_started"))
            return
        
        self.is_active = True
        self.start_time = datetime.now()
        self.task = asyncio.create_task(self.loop())
        
        await utils.answer(message, self.strings("started"))
    
    @loader.command(
        ru_doc="Остановить создание",
        alias="kylxstop"
    )
    async def kylxcoffcmd(self, message):
        """Остановить создание"""
        if not self.is_active:
            await utils.answer(message, self.strings("already_stopped"))
            return
        
        self.is_active = False
        if self.task:
            self.task.cancel()
        
        await utils.answer(message, self.strings("stopped"))
    
    @loader.command(
        ru_doc="Показать статус",
        alias="kylxstat"
    )
    async def kylxstatuscmd(self, message):
        """Показать статус"""
        if self.is_active and self.start_time:
            uptime = datetime.now() - self.start_time
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            seconds = uptime.seconds % 60
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            uptime_str = "00:00:00"
        
        success_rate = 0
        if self.created + self.errors > 0:
            success_rate = round((self.created / (self.created + self.errors)) * 100, 1)
        
        text = self.strings("stats").format(
            self.created,
            self.errors,
            success_rate,
            uptime_str
        )
        
        await utils.answer(message, text)
    
    @loader.command(
        ru_doc="Список каналов",
        alias="kylxls"
    )
    async def kylxlistcmd(self, message):
        """Список каналов"""
        if not self.channels:
            await utils.answer(message, "📭 Каналов нет")
            return
        
        text = "📋 Созданные каналы:\n\n"
        for i, ch in enumerate(self.channels[-10:], 1):
            folder = "✅" if ch.get('folder') else "❌"
            text += f"{i}. {ch['name']} - {ch['link']} {folder}\n"
        
        if len(self.channels) > 10:
            text += f"\n... и еще {len(self.channels) - 10}"
        
        text += f"\n\nВсего: {len(self.channels)}"
        
        await utils.answer(message, text)
    
    @loader.command(
        ru_doc="Создать папку",
        alias="kylxmkfolder"
    )
    async def kylxcreatefoldercmd(self, message):
        """Создать папку"""
        success = await self.ensure_folder()
        if success:
            await utils.answer(message, "📁 Папка 'KylxChannels' создана!")
        else:
            await utils.answer(message, "❌ Ошибка создания папки")
    
    @loader.command(
        ru_doc="Сбросить статистику",
        alias="kylxrst"
    )
    async def kylxresetcmd(self, message):
        """Сбросить статистику"""
        self.created = 0
        self.errors = 0
        self.start_time = None
        await utils.answer(message, "📊 Статистика сброшена")
    
    @loader.command(
        ru_doc="Помощь",
        alias="kylxhelp"
    )
    async def kylxhelpcmd(self, message):
        """Помощь"""
        text = """🤖 <b>Kylx Creator</b>

<b>Команды:</b>
<code>.kylxcon</code> - Запустить создание
<code>.kylxcoff</code> - Остановить
<code>.kylxstatus</code> - Статистика
<code>.kylxlist</code> - Список каналов
<code>.kylxcreatefolder</code> - Создать папку
<code>.kylxreset</code> - Сбросить статистику
<code>.kylxhelp</code> - Помощь

<b>Особенности:</b>
• Создает публичные каналы
• 4-буквенные ссылки
• Автоматически добавляет в папку
"""
        await utils.answer(message, text)
