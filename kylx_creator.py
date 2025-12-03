# meta developer: @yourusername
# meta pic: https://img.icons8.com/color/96/000000/telegram-app.png
# meta banner: https://img.icons8.com/color/480/000000/telegram-app.png
# requires: telethon>=1.24.0

__version__ = (1, 1, 0)
__author__ = "YourName"

import asyncio
import random
import string
import logging
from datetime import datetime
from telethon.tl.functions.channels import CreateChannelRequest
from telethon.tl.functions.messages import GetDialogFiltersRequest, UpdateDialogFilterRequest
from telethon.tl.types import (
    DialogFilter,
    InputChannel,
    InputPeerChannel
)
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
    """Модуль для автоматического создания каналов с 4-буквенными ссылками"""
    
    strings = {
        "name": "KylxCreator",
        "already_started": "🛑 Уже запущено",
        "started": "🚀 Создание каналов запущено",
        "already_stopped": "🛑 Уже остановлено",
        "stopped": "🛑 Создание каналов остановлено",
        "stats_reset": "📊 Статистика сброшена",
        "folder_created": "📁 Папка создана: {}",
        "folder_exists": "📁 Папка уже существует: {}",
        "folder_error": "❌ Ошибка при создании/обновлении папки: {}",
        "no_folder": "❌ Папка не найдена. Создайте папку командой .kylxfolder",
        "folder_list": "📋 Список папок:\n{}",
        "help_text": """
🤖 <b>Kylx Channel Creator</b> 🤖

<b>Команды:</b>
<code>.kylxcon</code> - Запустить создание каналов
<code>.kylxcoff</code> - Остановить создание каналов
<code>.kylxstatus</code> - Показать статус
<code>.kylxreset</code> - Сбросить статистику
<code>.kylxfolder</code> - Создать/обновить папку для каналов
<code>.kylxfolders</code> - Показать список папок
<code>.kylxlist</code> - Показать список созданных каналов
<code>.kylxhelp</code> - Показать эту справку

<b>Особенности:</b>
• Создает каналы с 4-буквенными ссылками
• Автоматически добавляет каналы в папку
• Автоматически проверяет доступность имен
• Обрабатывает флуд-контроль
• Ведет статистику

<b>Внимание:</b> Используйте осторожно, соблюдая правила Telegram!
""",
        "status_template": """
<b>🚀 Статус Kylx Creator</b>

<b>Состояние:</b> {status}
{uptime}
<b>Папка:</b> {folder_name}
<b>✅ Создано:</b> {created}
<b>❌ Ошибок:</b> {failed}
<b>📊 Успешность:</b> {success_rate}%
"""
    }
    
    strings_ru = {
        "name": "KylxCreator",
        "already_started": "🛑 Уже запущено",
        "started": "🚀 Создание каналов запущено",
        "already_stopped": "🛑 Уже остановлено",
        "stopped": "🛑 Создание каналов остановлено",
        "stats_reset": "📊 Статистика сброшена",
        "folder_created": "📁 Папка создана: {}",
        "folder_exists": "📁 Папка уже существует: {}",
        "folder_error": "❌ Ошибка при создании/обновлении папки: {}",
        "no_folder": "❌ Папка не найдена. Создайте папку командой .kylxfolder",
        "folder_list": "📋 Список папок:\n{}",
        "help_text": """
🤖 <b>Kylx Channel Creator</b> 🤖

<b>Команды:</b>
<code>.kylxcon</code> - Запустить создание каналов
<code>.kylxcoff</code> - Остановить создание каналов
<code>.kylxstatus</code> - Показать статус
<code>.kylxreset</code> - Сбросить статистику
<code>.kylxfolder</code> - Создать/обновить папку для каналов
<code>.kylxfolders</code> - Показать список папок
<code>.kylxlist</code> - Показать список созданных каналов
<code>.kylxhelp</code> - Показать эту справку

<b>Особенности:</b>
• Создает каналы с 4-буквенными ссылками
• Автоматически добавляет каналы в папку
• Автоматически проверяет доступность имен
• Обрабатывает флуд-контроль
• Ведет статистику

<b>Внимание:</b> Используйте осторожно, соблюдая правила Telegram!
""",
        "status_template": """
<b>🚀 Статус Kylx Creator</b>

<b>Состояние:</b> {status}
{uptime}
<b>Папка:</b> {folder_name}
<b>✅ Создано:</b> {created}
<b>❌ Ошибок:</b> {failed}
<b>📊 Успешность:</b> {success_rate}%
"""
    }
    
    def __init__(self):
        self.is_active = False
        self.creation_task = None
        self.created_count = 0
        self.failed_count = 0
        self.start_time = None
        self.folder_id = None
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "min_delay",
                10,
                "Минимальная задержка между созданиями",
                validator=loader.validators.Integer(minimum=5)
            ),
            loader.ConfigValue(
                "max_delay",
                30,
                "Максимальная задержка между созданиями",
                validator=loader.validators.Integer(minimum=10)
            ),
            loader.ConfigValue(
                "max_attempts",
                100,
                "Максимум попыток на один канал",
                validator=loader.validators.Integer(minimum=10, maximum=1000)
            ),
            loader.ConfigValue(
                "folder_name",
                "Kylx Channels",
                "Название папки для каналов",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "folder_color",
                6,  # Blue color
                "Цвет папки (0-13)",
                validator=loader.validators.Integer(minimum=0, maximum=13)
            ),
            loader.ConfigValue(
                "auto_add_to_folder",
                True,
                "Автоматически добавлять каналы в папку",
                validator=loader.validators.Boolean()
            ),
        )
    
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self._db = db
        
        # Пытаемся найти существующую папку
        await self._find_or_create_folder()
    
    async def _find_or_create_folder(self):
        """Находит существующую папку или создает новую"""
        try:
            # Получаем список всех папок
            folders = await self.client(GetDialogFiltersRequest())
            
            # Ищем папку с нашим названием
            target_folder_name = self.config["folder_name"]
            for folder in folders:
                if hasattr(folder, 'title') and folder.title == target_folder_name:
                    self.folder_id = getattr(folder, 'id', 0)
                    logger.info(f"Найдена существующая папка: {target_folder_name} (ID: {self.folder_id})")
                    return True
            
            # Если папка не найдена, создадим ее позже при первом создании канала
            self.folder_id = None
            logger.info(f"Папка '{target_folder_name}' не найдена, будет создана при первом канале")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при поиске папки: {e}")
            self.folder_id = None
            return False
    
    async def _create_or_update_folder(self, channel_ids=None):
        """Создает новую папку или обновляет существующую"""
        try:
            target_folder_name = self.config["folder_name"]
            folder_color = self.config["folder_color"]
            
            # Получаем текущий список папок
            folders = await self.client(GetDialogFiltersRequest())
            
            # Если channel_ids не передан, используем пустой список
            if channel_ids is None:
                channel_ids = []
            
            # Ищем существующую папку
            existing_folder = None
            for folder in folders:
                if hasattr(folder, 'title') and folder.title == target_folder_name:
                    existing_folder = folder
                    break
            
            # Собираем InputPeerChannel для каждого канала
            include_peers = []
            for channel_id in channel_ids:
                try:
                    # Получаем информацию о канале
                    channel = await self.client.get_entity(channel_id)
                    if hasattr(channel, 'access_hash'):
                        input_channel = InputPeerChannel(channel.id, channel.access_hash)
                        include_peers.append(input_channel)
                except Exception as e:
                    logger.error(f"Ошибка при получении канала {channel_id}: {e}")
                    continue
            
            if existing_folder:
                # Обновляем существующую папку
                folder_id = existing_folder.id
                
                # Получаем существующие пиры из папки
                existing_peers = []
                if hasattr(existing_folder, 'include_peers'):
                    existing_peers = existing_folder.include_peers
                
                # Объединяем существующие пиры с новыми, избегая дубликатов
                all_peers = existing_peers.copy()
                for new_peer in include_peers:
                    if not any(hasattr(p, 'channel_id') and p.channel_id == new_peer.channel_id 
                              for p in all_peers if hasattr(p, 'channel_id')):
                        all_peers.append(new_peer)
                
                # Обновляем папку
                updated_folder = DialogFilter(
                    id=folder_id,
                    title=target_folder_name,
                    emoji="📢",
                    color=folder_color,
                    pinned_peers=[],
                    include_peers=all_peers,
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
                
                await self.client(UpdateDialogFilterRequest(
                    id=folder_id,
                    filter=updated_folder
                ))
                
                self.folder_id = folder_id
                logger.info(f"Обновлена папка '{target_folder_name}' с {len(all_peers)} каналами")
                return True
                
            else:
                # Создаем новую папку
                # Ищем свободный ID для папки
                folder_ids = [f.id for f in folders if hasattr(f, 'id')]
                new_id = max(folder_ids) + 1 if folder_ids else 2
                
                # Создаем новую папку
                new_folder = DialogFilter(
                    id=new_id,
                    title=target_folder_name,
                    emoji="📢",
                    color=folder_color,
                    pinned_peers=[],
                    include_peers=include_peers,
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
                
                await self.client(UpdateDialogFilterRequest(
                    id=new_id,
                    filter=new_folder
                ))
                
                self.folder_id = new_id
                logger.info(f"Создана новая папка '{target_folder_name}' с {len(include_peers)} каналами")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при создании/обновлении папки: {e}")
            return False
    
    async def _add_channel_to_folder(self, channel_id):
        """Добавляет канал в папку"""
        if not self.config["auto_add_to_folder"]:
            return False
        
        try:
            # Получаем все созданные каналы из БД
            created_channels = self.db.get(__name__, "created_channels", [])
            all_channel_ids = [ch['channel_id'] for ch in created_channels if 'channel_id' in ch]
            
            # Добавляем новый канал в список
            if channel_id not in all_channel_ids:
                all_channel_ids.append(channel_id)
            
            # Создаем или обновляем папку
            success = await self._create_or_update_folder(all_channel_ids)
            
            if success:
                logger.info(f"Канал {channel_id} добавлен в папку '{self.config['folder_name']}'")
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении канала в папку: {e}")
            return False
    
    def generate_username(self):
        """Генерирует 4-буквенное имя пользователя"""
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(4))
    
    def get_success_rate(self):
        """Рассчитывает процент успешных созданий"""
        total = self.created_count + self.failed_count
        if total == 0:
            return 0
        return round((self.created_count / total) * 100, 1)
    
    async def create_single_channel(self):
        """Пытается создать один канал"""
        attempts = 0
        max_attempts = self.config["max_attempts"]
        
        while attempts < max_attempts and self.is_active:
            username = self.generate_username()
            
            try:
                logger.info(f"Попытка создать канал: t.me/{username}")
                
                # Создаем канал
                result = await self.client(CreateChannelRequest(
                    title=f"Kylx {username}",
                    about="Создано автоматически",
                    megagroup=False,
                    for_import=False
                ))
                
                channel = result.chats[0]
                
                # Пытаемся установить username
                try:
                    await self.client.edit_channel(
                        channel.id,
                        username=username
                    )
                except Exception as e:
                    logger.error(f"Не удалось установить username: {e}")
                    self.failed_count += 1
                    await asyncio.sleep(5)
                    attempts += 1
                    continue
                
                self.created_count += 1
                logger.info(f"✅ Успешно создан: t.me/{username} (ID: {channel.id})")
                
                # Добавляем канал в папку
                if self.config["auto_add_to_folder"]:
                    try:
                        await self._add_channel_to_folder(channel.id)
                    except Exception as e:
                        logger.error(f"Не удалось добавить канал в папку: {e}")
                
                # Сохраняем в базе данных
                created_channels = self.db.get(__name__, "created_channels", [])
                created_channels.append({
                    'username': username,
                    'channel_id': channel.id,
                    'link': f"https://t.me/{username}",
                    'created_at': datetime.now().isoformat(),
                    'in_folder': self.config["auto_add_to_folder"]
                })
                self.db.set(__name__, "created_channels", created_channels)
                
                return {
                    'success': True,
                    'username': username,
                    'channel_id': channel.id,
                    'link': f"https://t.me/{username}",
                    'added_to_folder': self.config["auto_add_to_folder"]
                }
                
            except UsernameOccupiedError:
                logger.debug(f"Имя {username} занято")
                attempts += 1
                await asyncio.sleep(0.3)
                
            except UsernameInvalidError:
                logger.debug(f"Некорректное имя: {username}")
                attempts += 1
                await asyncio.sleep(0.3)
                
            except ChannelsTooMuchError:
                logger.error("❌ Достигнут лимит каналов на аккаунте!")
                self.is_active = False
                return {'success': False, 'error': 'channels_limit'}
                
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"⏳ Флуд-контроль: ожидание {wait_time} секунд")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Ошибка при создании канала: {e}")
                self.failed_count += 1
                await asyncio.sleep(5)
                attempts += 1
        
        self.failed_count += 1
        return {'success': False, 'error': 'max_attempts'}
    
    async def creation_loop(self):
        """Основной цикл создания каналов"""
        logger.info("Запуск цикла создания каналов")
        
        while self.is_active:
            result = await self.create_single_channel()
            
            if not self.is_active:
                break
                
            if result['success']:
                # Задержка после успешного создания
                delay = random.uniform(
                    self.config["min_delay"],
                    self.config["max_delay"]
                )
                await asyncio.sleep(delay)
            else:
                if result.get('error') == 'channels_limit':
                    logger.error("Достигнут лимит каналов. Остановка.")
                    break
                # Задержка после неудачи
                await asyncio.sleep(random.uniform(5, 10))
    
    @loader.command(ru_doc="Запустить создание каналов")
    async def kylxconcmd(self, message):
        """Запустить создание каналов"""
        if self.is_active:
            await utils.answer(message, self.strings("already_started"))
            return
        
        self.is_active = True
        self.start_time = datetime.now()
        self.creation_task = asyncio.create_task(self.creation_loop())
        logger.info("Создание каналов запущено")
        await utils.answer(message, self.strings("started"))
    
    @loader.command(ru_doc="Остановить создание каналов")
    async def kylxcoffcmd(self, message):
        """Остановить создание каналов"""
        if not self.is_active:
            await utils.answer(message, self.strings("already_stopped"))
            return
        
        self.is_active = False
        if self.creation_task:
            self.creation_task.cancel()
            try:
                await self.creation_task
            except asyncio.CancelledError:
                pass
        logger.info("Создание каналов остановлено")
        await utils.answer(message, self.strings("stopped"))
    
    @loader.command(ru_doc="Показать статус создания")
    async def kylxstatuscmd(self, message):
        """Показать статус создания"""
        status = "🟢 Активен" if self.is_active else "🔴 Остановлен"
        folder_name = self.config["folder_name"] if self.config["auto_add_to_folder"] else "Не используется"
        
        uptime = ""
        if self.start_time and self.is_active:
            uptime_seconds = (datetime.now() - self.start_time).seconds
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            seconds = uptime_seconds % 60
            uptime = f"<b>⏱️ Время работы:</b> {hours:02d}:{minutes:02d}:{seconds:02d}\n"
        
        text = self.strings("status_template").format(
            status=status,
            uptime=uptime,
            folder_name=folder_name,
            created=self.created_count,
            failed=self.failed_count,
            success_rate=self.get_success_rate()
        )
        
        await utils.answer(message, text)
    
    @loader.command(ru_doc="Сбросить статистику")
    async def kylxresetcmd(self, message):
        """Сбросить статистику"""
        self.created_count = 0
        self.failed_count = 0
        self.start_time = None
        await utils.answer(message, self.strings("stats_reset"))
    
    @loader.command(ru_doc="Создать/обновить папку для каналов")
    async def kylxfoldercmd(self, message):
        """Создать или обновить папку для каналов"""
        try:
            # Получаем все созданные каналы из БД
            created_channels = self.db.get(__name__, "created_channels", [])
            channel_ids = [ch['channel_id'] for ch in created_channels if 'channel_id' in ch]
            
            # Создаем или обновляем папку
            success = await self._create_or_update_folder(channel_ids)
            
            if success:
                await utils.answer(message, self.strings("folder_created").format(self.config["folder_name"]))
            else:
                await utils.answer(message, self.strings("folder_exists").format(self.config["folder_name"]))
                
        except Exception as e:
            logger.error(f"Ошибка при работе с папкой: {e}")
            await utils.answer(message, self.strings("folder_error").format(str(e)))
    
    @loader.command(ru_doc="Показать список папок")
    async def kylxfolderscmd(self, message):
        """Показать список папок"""
        try:
            folders = await self.client(GetDialogFiltersRequest())
            
            if not folders:
                await utils.answer(message, "📭 Нет созданных папок")
                return
            
            text_lines = []
            for i, folder in enumerate(folders, 1):
                if hasattr(folder, 'title'):
                    folder_name = folder.title
                    folder_id = getattr(folder, 'id', 'N/A')
                    
                    # Подсчитываем количество каналов в папке
                    channel_count = 0
                    if hasattr(folder, 'include_peers'):
                        channel_count = sum(1 for peer in folder.include_peers 
                                          if hasattr(peer, 'channel_id'))
                    
                    # Проверяем, наша ли это папка
                    is_target = folder_name == self.config["folder_name"]
                    prefix = "📍 " if is_target else "📁 "
                    
                    text_lines.append(f"{prefix}<b>{folder_name}</b> (ID: {folder_id}) - {channel_count} каналов")
            
            text = self.strings("folder_list").format("\n".join(text_lines))
            await utils.answer(message, text)
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка папок: {e}")
            await utils.answer(message, f"❌ Ошибка: {e}")
    
    @loader.command(ru_doc="Показать справку")
    async def kylxhelpcmd(self, message):
        """Показать справку"""
        await utils.answer(message, self.strings("help_text"))
    
    @loader.command(ru_doc="Показать список созданных каналов")
    async def kylxlistcmd(self, message):
        """Показать список созданных каналов"""
        created_channels = self.db.get(__name__, "created_channels", [])
        
        if not created_channels:
            await utils.answer(message, "📭 Нет созданных каналов")
            return
        
        text = "📋 <b>Созданные каналы:</b>\n\n"
        for i, channel in enumerate(created_channels[-20:], 1):  # Последние 20
            in_folder = "✅" if channel.get('in_folder', False) else "❌"
            text += f"{i}. <code>{channel['username']}</code> - {channel['link']} {in_folder}\n"
        
        if len(created_channels) > 20:
            text += f"\n📊 И еще {len(created_channels) - 20} каналов..."
        
        text += f"\n📁 Всего каналов: {len(created_channels)}"
        await utils.answer(message, text)
    
    @loader.command(ru_doc="Очистить список каналов")
    async def kylxclearcmd(self, message):
        """Очистить список созданных каналов"""
        self.db.set(__name__, "created_channels", [])
        await utils.answer(message, "🗑️ Список каналов очищен")
    
    @loader.command(ru_doc="Тест добавления текущего чата в папку")
    async def kylxtestfolder(self, message):
        """Тест добавления текущего чата в папку"""
        try:
            chat = await message.get_chat()
            if hasattr(chat, 'id'):
                success = await self._add_channel_to_folder(chat.id)
                if success:
                    await utils.answer(message, f"✅ Чат добавлен в папку '{self.config['folder_name']}'")
                else:
                    await utils.answer(message, f"❌ Не удалось добавить чат в папку")
            else:
                await utils.answer(message, "❌ Это не канал")
        except Exception as e:
            await utils.answer(message, f"❌ Ошибка: {e}")
