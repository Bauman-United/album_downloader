import os
import sys
import re
import shutil
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import vk_api
import requests
import datetime
import yadisk

from get_vk_session import get_vk_session

# Load environment variables
load_dotenv()

# Constants
WAITING_FOR_ALBUM_URL = 1
path_to_downloaded_albums = 'vk_downloaded_albums'

# Progress tracking
class ProgressTracker:
    def __init__(self, chat_id, context):
        self.chat_id = chat_id
        self.context = context
        self.last_percent = 0
        
    async def update_progress(self, current, total, stage_name):
        """Send progress update every 10%"""
        if total == 0:
            return
        
        percent = int((current / total) * 100)
        # Send update every 10%
        if percent >= self.last_percent + 10 or percent == 100:
            self.last_percent = percent
            await self.context.bot.send_message(
                chat_id=self.chat_id,
                text=f"📊 {stage_name}: {percent}% ({current}/{total})"
            )


def process_url(url):
    """Extract owner_id and album_id from VK album URL"""
    verification = re.compile(r'^https://vk\.(com|ru)/album(-?[\d]+)_([\d]+)$')
    o = verification.match(url)
    if not o:
        raise ValueError('Invalid album link')
    owner_id = o.group(2)
    album_id = o.group(3)
    return {'owner_id': owner_id, 'album_id': album_id}


def fix_illegal_album_title(title):
    """Replace illegal characters in album title"""
    illegal_character = '\/|:?<>*"'
    for c in illegal_character:
        title = title.replace(c, '_')
    return title


def download_image(url, local_file_name):
    """Download single image from URL"""
    response = requests.get(url, stream=True)
    if not response.ok:
        return False
    with open(local_file_name, 'wb') as file:
        for chunk in response.iter_content(1024):
            file.write(chunk)
    return True


async def download_album(album_url, chat_id, context):
    """Download album from VK"""
    try:
        query = process_url(album_url)
    except ValueError as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {e}")
        return None
    
    vk_session = get_vk_session()
    
    try:
        api = vk_session.get_api()
        api.users.get(user_ids=1)
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ VK authentication failed: {e}")
        return None
    
    o = query['owner_id']
    a = query['album_id']
    
    try:
        album = api.photos.getAlbums(owner_id=o, album_ids=a)['items'][0]
        title = album['title']
        title = fix_illegal_album_title(title)
        images_num = album['size']
        photos = api.photos.get(owner_id=o, album_id=a, photo_sizes=1, count=images_num)['items']
    except vk_api.exceptions.ApiError as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ VK API error: {e}")
        return None
    
    album_path = path_to_downloaded_albums + '/' + title
    if not os.path.exists(album_path):
        os.makedirs(album_path)
    else:
        album_path += '.copy_{:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
        os.makedirs(album_path)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"📥 Downloading album: *{title}*\n📸 Total photos: {images_num}",
        parse_mode='Markdown'
    )
    
    tracker = ProgressTracker(chat_id, context)
    
    for i, p in enumerate(photos, 1):
        largest_image_width = p['sizes'][0]['width']
        largest_image_src = p['sizes'][0]['url']
        
        if largest_image_width == 0:
            largest_image_src = p['sizes'][len(p['sizes']) - 1]['url']
        else:
            for size in p['sizes']:
                if size['width'] > largest_image_width:
                    largest_image_width = size['width']
                    largest_image_src = size['url']
        
        extension = os.path.splitext(largest_image_src)[-1].split('?')[0]
        download_image(largest_image_src, album_path + '/' + str(p['id']) + extension)
        
        await tracker.update_progress(i, images_num, "Downloading")
    
    return {'path': album_path, 'title': title, 'count': images_num}


async def upload_album_to_yandex(album_info, chat_id, context):
    """Upload album to Yandex Disk"""
    token = os.getenv('YANDEX_DISK_TOKEN')
    
    if not token:
        await context.bot.send_message(chat_id=chat_id, text="❌ Yandex Disk token not configured")
        return None
    
    y = yadisk.YaDisk(token=token)
    
    if not y.check_token():
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid Yandex Disk token")
        return None
    
    yandex_disk_path = os.getenv('YANDEX_DISK_PATH', '/VK_Albums')
    album_title = album_info['title']
    local_album_path = album_info['path']
    remote_album_path = f'{yandex_disk_path}/{album_title}'
    
    # Create base directory if needed
    if not y.exists(yandex_disk_path):
        y.mkdir(yandex_disk_path)
    
    # Create album directory
    if not y.exists(remote_album_path):
        y.mkdir(remote_album_path)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"☁️ Uploading to Yandex Disk...\n📁 Path: `{remote_album_path}`",
        parse_mode='Markdown'
    )
    
    photos = [f for f in os.listdir(local_album_path) 
              if os.path.isfile(os.path.join(local_album_path, f))]
    
    tracker = ProgressTracker(chat_id, context)
    uploaded_count = 0
    skipped_count = 0
    
    for i, photo_name in enumerate(photos, 1):
        local_photo_path = os.path.join(local_album_path, photo_name)
        remote_photo_path = f'{remote_album_path}/{photo_name}'
        
        # Check if already exists
        if y.exists(remote_photo_path):
            local_size = os.path.getsize(local_photo_path)
            remote_info = y.get_meta(remote_photo_path)
            
            if remote_info.size == local_size:
                skipped_count += 1
                await tracker.update_progress(i, len(photos), "Uploading")
                continue
        
        try:
            y.upload(local_photo_path, remote_photo_path, overwrite=True)
            uploaded_count += 1
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Error uploading {photo_name}: {e}")
            continue
        
        await tracker.update_progress(i, len(photos), "Uploading")
    
    # Get public link
    try:
        if not y.is_public(remote_album_path):
            y.publish(remote_album_path)
        meta = y.get_meta(remote_album_path)
        public_url = meta.public_url
    except Exception:
        public_url = None
    
    return {
        'uploaded': uploaded_count,
        'skipped': skipped_count,
        'public_url': public_url,
        'remote_path': remote_album_path
    }


def clear_local_album(album_path):
    """Delete local album folder"""
    if os.path.exists(album_path):
        shutil.rmtree(album_path)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = (
        "👋 Welcome to VK Album Downloader Bot!\n\n"
        "Available commands:\n"
        "/download - Download and upload an album\n"
        "/help - Show this help message\n\n"
        "Send /download to get started!"
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📖 *How to use:*\n\n"
        "1️⃣ Send /download command\n"
        "2️⃣ Send VK album URL (format: https://vk.com/album-123456789_987654321)\n"
        "3️⃣ Wait for the bot to:\n"
        "   • Download the album from VK\n"
        "   • Upload it to Yandex Disk\n"
        "   • Clean up local files\n"
        "4️⃣ Get the public link to your album!\n\n"
        "💡 *Progress updates every 10%*"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /download command"""
    await update.message.reply_text(
        "📎 Please send me the VK album URL\n\n"
        "Example: `https://vk.com/album-123456789_987654321`\n\n"
        "Send /cancel to cancel",
        parse_mode='Markdown'
    )
    return WAITING_FOR_ALBUM_URL


async def handle_album_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle album URL and start workflow"""
    album_url = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    # Validate URL
    try:
        process_url(album_url)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid album URL format.\n"
            "Please send a valid VK album URL like:\n"
            "`https://vk.com/album-123456789_987654321`\n\n"
            "Or send /cancel to cancel",
            parse_mode='Markdown'
        )
        return WAITING_FOR_ALBUM_URL
    
    await update.message.reply_text("🚀 Starting workflow...")
    
    # Step 1: Download
    await context.bot.send_message(chat_id=chat_id, text="━━━━━ STEP 1: DOWNLOAD ━━━━━")
    album_info = await download_album(album_url, chat_id, context)
    
    if not album_info:
        await update.message.reply_text("❌ Download failed. Workflow stopped.")
        return ConversationHandler.END
    
    await context.bot.send_message(chat_id=chat_id, text="✅ Download completed!")
    
    # Step 2: Upload
    await context.bot.send_message(chat_id=chat_id, text="\n━━━━━ STEP 2: UPLOAD ━━━━━")
    upload_result = await upload_album_to_yandex(album_info, chat_id, context)
    
    if not upload_result:
        await update.message.reply_text("❌ Upload failed. Local files preserved.")
        return ConversationHandler.END
    
    await context.bot.send_message(chat_id=chat_id, text="✅ Upload completed!")
    
    # Step 3: Cleanup
    await context.bot.send_message(chat_id=chat_id, text="\n━━━━━ STEP 3: CLEANUP ━━━━━")
    clear_local_album(album_info['path'])
    await context.bot.send_message(chat_id=chat_id, text="✅ Local files cleaned up!")
    
    # Final success message
    success_message = (
        "\n🎉 *WORKFLOW COMPLETED SUCCESSFULLY!*\n\n"
        f"📁 Album: *{album_info['title']}*\n"
        f"📸 Photos: {album_info['count']}\n"
        f"📤 Uploaded: {upload_result['uploaded']} new\n"
        f"⊘ Skipped: {upload_result['skipped']} existing\n"
    )
    
    if upload_result['public_url']:
        success_message += f"\n🔗 *Public link:*\n{upload_result['public_url']}"
    else:
        success_message += f"\n📂 *Path:* `{upload_result['remote_path']}`"
    
    await update.message.reply_text(success_message, parse_mode='Markdown')
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END


def main():
    """Start the bot"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print('Error: TELEGRAM_BOT_TOKEN not found in environment variables')
        print('Please add your Telegram bot token to the .env file')
        print('Get your token from: @BotFather on Telegram')
        sys.exit(1)
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('download', download_command)],
        states={
            WAITING_FOR_ALBUM_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_album_url)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(conv_handler)
    
    print('🤖 Bot started! Press Ctrl+C to stop.')
    
    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
