# meta developer: @kylxdevvv
# meta pic: https://img.icons8.com/color/96/000000/telegram-app.png
# meta banner: https://img.icons8.com/color/480/000000/telegram-app.png
# requires: telethon>=1.24.0

__version__ = (1, 2, 0)
__author__ = "kylxdevv"

import asyncio
import random
import string
import logging
from datetime import datetime
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    UpdateUsernameRequest,
    ExportMessageLinkRequest,
    ToggleInvitesRequest,
    EditPhotoRequest
)
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest, 
    UpdateDialogFilterRequest,
    ExportChatInviteRequest
)
from telethon.tl.types import (
    DialogFilter,
    InputPeerChannel,
    InputChannel,
    InputChatPhotoEmpty
)
from telethon.errors import (
    UsernameOccupiedError, 
    UsernameInvalidError, 
    FloodWaitError,
    ChannelsTooMuchError,
    ChatAdminRequiredError
)

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class KylxCreatorMod(loader.Module):
    """Модуль для автоматического создания публичных каналов с 4-буквенными ссылками"""
    
    strings = {
        "name": "KylxCreator",
        "already_started": "🛑 Уже запущено",
        "started": "🚀 Создание публичных каналов запущено",
        "already_stopped": "🛑 Уже остановлено",
        "stopped": "🛑 Создание каналов остановлено",
        "stats_reset": "📊 Статистика сброшена",
        "folder_created": "📁 Папка 'KylxChannels' создана успешно!",
        "folder_exists": "📁 Папка 'KylxChannels' уже существует",
        "folder_error": "❌ Ошибка при создании папки: {}",
        "folder_list": "📋 Список папок:\n{}",
        "help_text": """
🤖 <b>Kylx Channel Creator</b> 🤖

<b>Команды:</b>
<code>.kylxcon</code> - Запустить создание публичных каналов
<code>.kylxcoff</code> - Остановить создание каналов
<code>.kylxstatus</code> - Показать статус
<code>.kylxreset</code> - Сбросить статистику
<code>.kylxfolders</code> - Показать список папок
<code>.kylxlist</code> - Показать список созданных каналов
<code>.kylxhelp</code> - Показать эту справку

<b>Особенности:</b>
• Создает публичные каналы с 4-буквенными ссылками
• Автоматически создает папку 'KylxChannels'
• Все каналы автоматически добавляются в папку
• Автоматически проверяет доступность имен
• Обрабатывает флуд-контроль
• Ведет статистику

<b>Внимание:</b> Используйте осторожно, соблюдая правила Telegram!
""",
        "status_template": """
<b>🚀 Статус Kylx Creator</b>

<b>Состояние:</b> {status}
{uptime}
<b>📁 Папка:</b> KylxChannels
<b>✅ Создано:</b> {created}
<b>❌ Ошибок:</b> {failed}
<b>📊 Успешность:</b> {success_rate}%
<b>🔄 В папке:</b> {in_folder}/{total} каналов
"""
    }
    
    strings_ru = {
        "name": "KylxCreator",
        "already_started": "🛑 Уже запущено",
        "started": "🚀 Создание публичных каналов запущено",
        "already_stopped": "🛑 Уже остановлено",
        "stopped": "🛑 Создание каналов остановлено",
        "stats_reset": "📊 Статистика сброшена",
        "folder_created": "📁 Папка 'KylxChannels' создана успешно!",
        "folder_exists": "📁 Папка 'KylxChannels' уже существует",
        "folder_error": "❌ Ошибка при создании папки: {}",
        "folder_list": "📋 Список папок:\n{}",
        "help_text": """
🤖 <b>Kylx Channel Creator</b> 🤖

<b>Команды:</b>
<code>.kylxcon</code> - Запустить создание публичных каналов
<code>.kylxcoff</code> - Остановить создание каналов
<code>.kylxstatus</code> - Показать статус
<code>.kylxreset</code> - Сбросить статистику
<code>.kylxfolders</code> - Показать список папок
<code>.kylxlist</code> - Показать список созданных каналов
<code>.kylxhelp</code> - Показать эту справку

<b>Особенности:</b>
• Создает публичные каналы с 4-буквенными ссылками
• Автоматически создает папку 'KylxChannels'
• Все каналы автоматически добавляются в папку
• Автоматически проверяет доступность имен
• Обрабатывает флуд-контроль
• Ведет статистику

<b>Внимание:</b> Используйте осторожно, соблюдая правила Telegram!
""",
        "status_template": """
<b>🚀 Статус Kylx Creator</b>

<b>Состояние:</b> {status}
{uptime}
<b>📁 Папка:</b> KylxChannels
<b>✅ Создано:</b> {created}
<b>❌ Ошибок:</b> {failed}
<b>📊 Успешность:</b> {success_rate}%
<b>🔄 В папке:</b> {in_folder}/{total} каналов
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
                15,
                "Минимальная задержка между созданиями",
                validator=loader.validators.Integer(minimum=10)
            ),
            loader.ConfigValue(
                "max_delay",
                45,
                "Максимальная задержка между созданиями",
                validator=loader.validators.Integer(minimum=20)
            ),
            loader.ConfigValue(
                "max_attempts",
                200,
                "Максимум попыток на один канал",
                validator=loader.validators.Integer(minimum=50, maximum=1000)
            ),
            loader.ConfigValue(
                "auto_create_folder",
                True,
                "Автоматически создавать папку KylxChannels",
                validator=loader.validators.Boolean()
            ),
        )
    
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self._db = db
        
        # Находим или создаем папку при запуске модуля
        await self._ensure_folder_exists()
    
    async def _ensure_folder_exists(self):
        """Убеждается, что папка KylxChannels существует"""
        try:
            folders = await self.client(GetDialogFiltersRequest())
            
            # Ищем папку KylxChannels
            for folder in folders:
                if hasattr(folder, 'title') and folder.title == "KylxChannels":
                    self.folder_id = getattr(folder, 'id', 0)
                    logger.info(f"Найдена папка 'KylxChannels' (ID: {self.folder_id})")
                    return True
            
            # Если папка не найдена и включено автосоздание, создаем ее
            if self.config["auto_create_folder"]:
                return await self._create_kylx_folder()
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при проверке папки: {e}")
            return False
    
    async def _create_kylx_folder(self):
        """Создает папку KylxChannels"""
        try:
            folders = await self.client(GetDialogFiltersRequest())
            
            # Ищем свободный ID
            folder_ids = [f.id for f in folders if hasattr(f, 'id')]
            new_id = max(folder_ids) + 1 if folder_ids else 2
            
            # Создаем новую папку
            new_folder = DialogFilter(
                id=new_id,
                title="KylxChannels",
                emoji="📢",
                color=6,  # Синий цвет
                pinned_peers=[],
                include_peers=[],
                exclude_peers=[],
                contacts=False,
                non_contacts=False,
                groups=False,
                broadcasts=True,  # Только каналы
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
            logger.info(f"Создана папка 'KylxChannels' (ID: {new_id})")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при создании папки: {e}")
            return False
    
    async def _add_channel_to_kylx_folder(self, channel_id, access_hash=None):
        """Добавляет канал в папку KylxChannels"""
        try:
            # Получаем текущие папки
            folders = await self.client(GetDialogFiltersRequest())
            
            # Ищем папку KylxChannels
            kylx_folder = None
            for folder in folders:
                if hasattr(folder, 'title') and folder.title == "KylxChannels":
                    kylx_folder = folder
                    break
            
            if not kylx_folder:
                # Если папки нет, создаем ее
                if not await self._create_kylx_folder():
                    return False
                # Получаем обновленный список папок
                folders = await self.client(GetDialogFiltersRequest())
                for folder in folders:
                    if hasattr(folder, 'title') and folder.title == "KylxChannels":
                        kylx_folder = folder
                        break
            
            # Получаем объект канала
            try:
                if access_hash:
                    channel_peer = InputPeerChannel(channel_id, access_hash)
                else:
                    # Пытаемся получить канал через get_entity
                    channel = await self.client.get_entity(channel_id)
                    channel_peer = InputPeerChannel(channel.id, channel.access_hash)
            except Exception as e:
                logger.error(f"Не удалось получить канал {channel_id}: {e}")
                return False
            
            # Получаем текущие каналы в папке
            current_peers = []
            if hasattr(kylx_folder, 'include_peers'):
                current_peers = kylx_folder.include_peers.copy()
            
            # Проверяем, нет ли уже этого канала в папке
            for peer in current_peers:
                if hasattr(peer, 'channel_id') and peer.channel_id == channel_id:
                    logger.debug(f"Канал {channel_id} уже в папке")
                    return True
            
            # Добавляем новый канал
            current_peers.append(channel_peer)
            
            # Обновляем папку
            updated_folder = DialogFilter(
                id=kylx_folder.id,
                title="KylxChannels",
                emoji="📢",
                color=6,
                pinned_peers=[],
                include_peers=current_peers,
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
                id=kylx_folder.id,
                filter=updated_folder
            ))
            
            logger.info(f"Канал {channel_id} добавлен в папку 'KylxChannels'")
            return True
            
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
        """Пытается создать один публичный канал"""
        attempts = 0
        max_attempts = self.config["max_attempts"]
        
        while attempts < max_attempts and self.is_active:
            username = self.generate_username()
            
            try:
                logger.info(f"Попытка создать публичный канал: t.me/{username}")
                
                # 1. Создаем канал (публичный по умолчанию)
                result = await self.client(CreateChannelRequest(
                    title=f"Kylx {username}",
                    about="Создано автоматически | Public channel",
                    megagroup=False,
                    for_import=False,
                    broadcast=True
                ))
                
                channel = result.chats[0]
                logger.info(f"Канал создан, ID: {channel.id}")
                
                # 2. Устанавливаем публичное имя пользователя
                try:
                    await self.client(UpdateUsernameRequest(
                        channel=InputChannel(channel.id, channel.access_hash),
                        username=username
                    ))
                    logger.info(f"Установлен username: {username}")
                except Exception as e:
                    logger.error(f"Не удалось установить username: {e}")
                    self.failed_count += 1
                    await asyncio.sleep(5)
                    attempts += 1
                    continue
                
                # 3. Включаем возможность приглашений (на всякий случай)
                try:
                    await self.client(ToggleInvitesRequest(
                        channel=InputChannel(channel.id, channel.access_hash),
                        enabled=True
                    ))
                except Exception as e:
                    logger.warning(f"Не удалось включить приглашения: {e}")
                
                # 4. Создаем публичную ссылку-приглашение
                try:
                    invite = await self.client(ExportChatInviteRequest(
                        peer=InputPeerChannel(channel.id, channel.access_hash),
                        legacy_revoke_permanent=True,
                        request_needed=False
                    ))
                    invite_link = invite.link
                    logger.info(f"Создана публичная ссылка: {invite_link}")
                except Exception as e:
                    logger.warning(f"Не удалось создать ссылку-приглашение: {e}")
                    invite_link = f"https://t.me/{username}"
                
                # 5. Добавляем канал в папку KylxChannels
                try:
                    success = await self._add_channel_to_kylx_folder(channel.id, channel.access_hash)
                    in_folder = success
                except Exception as e:
                    logger.error(f"Не удалось добавить канал в папку: {e}")
                    in_folder = False
                
                self.created_count += 1
                logger.info(f"✅ Успешно создан публичный канал: t.me/{username}")
                
                # 6. Сохраняем в базе данных
                created_channels = self.db.get(__name__, "created_channels", [])
                created_channels.append({
                    'username': username,
                    'channel_id': channel.id,
                    'access_hash': channel.access_hash,
                    'public_link': f"https://t.me/{username}",
                    'invite_link': invite_link,
                    'created_at': datetime.now().isoformat(),
                    'in_folder': in_folder
                })
                self.db.set(__name__, "created_channels", created_channels)
                
                return {
                    'success': True,
                    'username': username,
                    'channel_id': channel.id,
                    'public_link': f"https://t.me/{username}",
                    'invite_link': invite_link,
                    'added_to_folder': in_folder
                }
                
            except UsernameOccupiedError:
                logger.debug(f"Имя {username} занято")
                attempts += 1
                await asyncio.sleep(0.5)
                
            except UsernameInvalidError:
                logger.debug(f"Некорректное имя: {username}")
                attempts += 1
                await asyncio.sleep(0.5)
                
            except ChannelsTooMuchError:
                logger.error("❌ Достигнут лимит каналов на аккаунте!")
                self.is_active = False
                return {'success': False, 'error': 'channels_limit'}
                
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"⏳ Флуд-контроль: ожидание {wait_time} секунд")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Ошибка при создании канала: {str(e)}")
                self.failed_count += 1
                await asyncio.sleep(5)
                attempts += 1
        
        self.failed_count += 1
        return {'success': False, 'error': 'max_attempts'}
    
    async def creation_loop(self):
        """Основной цикл создания каналов"""
        logger.info("Запуск цикла создания публичных каналов")
        
        # Убеждаемся, что папка существует перед началом создания
        if self.config["auto_create_folder"]:
            await self._ensure_folder_exists()
        
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
                logger.info(f"Успешно создан канал. Следующий через {delay:.1f} секунд")
                await asyncio.sleep(delay)
            else:
                if result.get('error') == 'channels_limit':
                    logger.error("Достигнут лимит каналов. Остановка.")
                    break
                # Задержка после неудачи
                wait_time = random.uniform(8, 15)
                logger.info(f"Неудача. Следующая попытка через {wait_time:.1f} секунд")
                await asyncio.sleep(wait_time)
    
    @loader.command(ru_doc="Запустить создание публичных каналов")
    async def kylxconcmd(self, message):
        """Запустить создание публичных каналов"""
        if self.is_active:
            await utils.answer(message, self.strings("already_started"))
            return
        
        # Создаем папку перед запуском
        if self.config["auto_create_folder"]:
            try:
                await self._ensure_folder_exists()
                await utils.answer(message, "📁 Создаю папку 'KylxChannels'...")
            except Exception as e:
                logger.error(f"Ошибка при создании папки: {e}")
                await utils.answer(message, f"⚠️ Не удалось создать папку: {e}\nПродолжаю без папки...")
        
        self.is_active = True
        self.start_time = datetime.now()
        self.creation_task = asyncio.create_task(self.creation_loop())
        logger.info("Создание публичных каналов запущено")
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
        
        uptime = ""
        if self.start_time and self.is_active:
            uptime_seconds = (datetime.now() - self.start_time).seconds
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            seconds = uptime_seconds % 60
            uptime = f"<b>⏱️ Время работы:</b> {hours:02d}:{minutes:02d}:{seconds:02d}\n"
        
        # Получаем статистику по папке
        created_channels = self.db.get(__name__, "created_channels", [])
        in_folder_count = sum(1 for ch in created_channels if ch.get('in_folder', False))
        total_count = len(created_channels)
        
        text = self.strings("status_template").format(
            status=status,
            uptime=uptime,
            created=self.created_count,
            failed=self.failed_count,
            success_rate=self.get_success_rate(),
            in_folder=in_folder_count,
            total=total_count
        )
        
        await utils.answer(message, text)
    
    @loader.command(ru_doc="Сбросить статистику")
    async def kylxresetcmd(self, message):
        """Сбросить статистику"""
        self.created_count = 0
        self.failed_count = 0
        self.start_time = None
        await utils.answer(message, self.strings("stats_reset"))
    
    @loader.command(ru_doc="Создать папку KylxChannels")
    async def kylxcreatefoldercmd(self, message):
        """Создать папку KylxChannels"""
        try:
            success = await self._create_kylx_folder()
            if success:
                await utils.answer(message, self.strings("folder_created"))
            else:
                await utils.answer(message, self.strings("folder_exists"))
        except Exception as e:
            logger.error(f"Ошибка при создании папки: {e}")
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
                    is_kylx = folder_name == "KylxChannels"
                    prefix = "📍 " if is_kylx else "📁 "
                    
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
        
        text = "📋 <b>Созданные публичные каналы:</b>\n\n"
        for i, channel in enumerate(created_channels[-15:], 1):  # Последние 15
            in_folder = "✅" if channel.get('in_folder', False) else "❌"
            text += f"{i}. <code>{channel['username']}</code>\n"
            text += f"   🔗 {channel['public_link']}\n"
            if channel.get('invite_link') and channel['invite_link'] != channel['public_link']:
                text += f"   📨 {channel['invite_link']}\n"
            text += f"   📁 {in_folder}\n\n"
        
        if len(created_channels) > 15:
            text += f"\n📊 И еще {len(created_channels) - 15} каналов..."
        
        text += f"\n📈 Всего каналов: {len(created_channels)}"
        text += f"\n✅ В папке: {sum(1 for ch in created_channels if ch.get('in_folder', False))}"
        
        await utils.answer(message, text)
    
    @loader.command(ru_doc="Добавить все каналы в папку")
    async def kylxaddalltofoldercmd(self, message):
        """Добавить все созданные каналы в папку KylxChannels"""
        created_channels = self.db.get(__name__, "created_channels", [])
        
        if not created_channels:
            await utils.answer(message, "📭 Нет созданных каналов для добавления")
            return
        
        await utils.answer(message, f"🔄 Добавляю {len(created_channels)} каналов в папку...")
        
        success_count = 0
        fail_count = 0
        
        for channel in created_channels:
            if not channel.get('in_folder', False):
                try:
                    success = await self._add_channel_to_kylx_folder(
                        channel['channel_id'],
                        channel.get('access_hash')
                    )
                    if success:
                        channel['in_folder'] = True
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    logger.error(f"Ошибка при добавлении канала {channel['username']}: {e}")
                    fail_count += 1
                
                # Задержка между добавлениями
                await asyncio.sleep(1)
        
        # Обновляем БД
        self.db.set(__name__, "created_channels", created_channels)
        
        await utils.answer(message, f"✅ Готово!\nУспешно: {success_count}\nНе удалось: {fail_count}")
    
    @loader.command(ru_doc="Очистить список каналов")
    async def kylxclearcmd(self, message):
        """Очистить список созданных каналов"""
        self.db.set(__name__, "created_channels", [])
        await utils.answer(message, "🗑️ Список каналов очищен")
