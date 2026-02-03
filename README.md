# VK Album Downloader Bot

Telegram bot to download VK photo albums and automatically upload them to Yandex Disk.

## Features

✨ **Telegram Bot** - Control remotely from anywhere  
📥 **Auto Download** - Downloads albums from VK  
☁️ **Auto Upload** - Uploads to Yandex Disk  
🔗 **Public Links** - Generates shareable links  
📊 **Progress Tracking** - Updates every 10%  
🐳 **Docker Ready** - One-command deployment  
🔄 **CI/CD Pipeline** - Auto-deploy via GitHub Actions  

## Quick Start

### 1. Get Tokens

| Service | Link |
|---------|------|
| VK API Token | https://oauth.vk.com/authorize?client_id=7624256&display=page&scope=photos,offline&response_type=token&v=5.131 |
| Yandex Disk Token | https://yandex.ru/dev/disk/poligon/ |
| Telegram Bot Token | https://t.me/botfather (send `/newbot`) |

### 2. Choose Deployment Method

#### Option A: Docker (Recommended)

```bash
# Create .env file
cat > .env << EOF
VK_ACCESS_TOKEN=your_vk_token
YANDEX_DISK_TOKEN=your_yandex_token
TELEGRAM_BOT_TOKEN=your_telegram_token
YANDEX_DISK_PATH=/VK_Albums
EOF

# Start bot
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Option B: Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file (same as above)

# Run bot
python telegram_bot.py
```

#### Option C: GitHub Actions (Automated)

1. **Push code to GitHub**

2. **Add GitHub Secrets** (Settings → Secrets → Actions):
   - `VK_ACCESS_TOKEN`
   - `YANDEX_DISK_TOKEN`
   - `TELEGRAM_BOT_TOKEN`
   - `YANDEX_DISK_PATH`

3. **Push to main or click "Run workflow" in Actions tab**

4. **Bot auto-deploys!**

**Optional SSH Deployment Secrets:**
- `SSH_HOST` - Your server IP/hostname
- `SSH_USERNAME` - SSH username
- `SSH_PRIVATE_KEY` - SSH private key
- `SSH_PORT` - SSH port (default: 22)

## Usage

1. **Find your bot on Telegram** (use username from @BotFather)

2. **Send `/start`** to see commands

3. **Send `/download`** and paste VK album URL:
   ```
   https://vk.com/album-123456789_987654321
   ```

4. **Wait for workflow:**
   - 📥 Download from VK (progress every 10%)
   - ☁️ Upload to Yandex Disk (progress every 10%)
   - 🧹 Cleanup local files
   - 🔗 Receive public Yandex Disk link

## Bot Commands

- `/start` - Welcome and help
- `/help` - Detailed instructions
- `/download` - Start downloading album
- `/cancel` - Cancel current operation

## Docker Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild
docker-compose up -d --build
```

## GitHub Actions

### Automatic Deployment
Push to main branch triggers automatic deployment:
```bash
git push origin main
```

### Manual Deployment
1. Go to **Actions** tab on GitHub
2. Select **"Build and Deploy Telegram Bot"**
3. Click **"Run workflow"**
4. Select `main` branch
5. Click **"Run workflow"** button

## Project Structure

```
album_downloader/
├── telegram_bot.py              # Main bot
├── get_vk_session.py            # VK authentication
├── upload_to_yandex_disk.py     # Yandex Disk upload
├── main.py                      # CLI version
├── Dockerfile                   # Docker config
├── docker-compose.yml           # Docker Compose
├── .github/workflows/deploy.yml # CI/CD pipeline
└── requirements.txt             # Dependencies
```

## Environment Variables

Required in `.env` file or GitHub Secrets:

```bash
VK_ACCESS_TOKEN=vk1.a.xxx...
YANDEX_DISK_TOKEN=y0_xxx...
TELEGRAM_BOT_TOKEN=1234567890:ABC...
YANDEX_DISK_PATH=/VK_Albums
```

## Workflow Architecture

```
User → Telegram Bot → Download VK Album → Upload Yandex Disk → Send Link
        ↓                ↓                    ↓                   ↓
    /download        📥 Photos            ☁️ Storage          🔗 Share
                  (10%, 20%...)        (10%, 20%...)      (Cleanup)
```

## Troubleshooting

### Bot not responding
```bash
# Check logs
docker-compose logs -f

# Restart
docker-compose restart
```

### Invalid token errors
- Verify tokens in `.env` file
- Check token format (no extra spaces)
- Regenerate expired tokens

### GitHub Actions failing
- Verify all secrets are set in GitHub
- Check workflow logs in Actions tab
- Ensure secret names match exactly

### SSH deployment not working
- Verify SSH secrets are correct
- Test SSH connection manually
- Check server Docker installation

## Development

Run locally for testing:
```bash
python telegram_bot.py
```

Run specific scripts:
```bash
python main.py                  # CLI download workflow
python get_all_albums.py        # Auto-collect BU albums
python upload_to_yandex_disk.py # Manual upload
```

## Security

✅ Never commit `.env` file (in `.gitignore`)  
✅ Use GitHub Secrets for CI/CD  
✅ Rotate tokens periodically  
✅ Use minimal required permissions  

## Requirements

- Python 3.11+
- Docker & Docker Compose (for Docker deployment)
- VK account with API access
- Yandex Disk account
- Telegram account

## License

Personal and educational use.

---

**Built with ❤️ for easy VK album management**
