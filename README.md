# Discord Support Bot

A powerful Discord bot for managing support tickets with advanced features.

## Features

- 🎫 Automatic ticket creation via DM
- 🔒 Private messaging between support team and users
- 📊 Real-time ticket status tracking
- ⭐ User rating system
- 📝 Detailed ticket logging
- 🎨 Beautiful and intuitive UI
- ⚡ Fast and reliable performance

## Setup

1. Clone the repository:
```bash
git clone https://github.com/YzeedHrb/Discord-Support-Bot.git
cd Discord-Support-Bot
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```env
TOKEN=your_bot_token
SUPPORT_GUILD_ID=your_guild_id
TICKET_CATEGORY_ID=your_category_id
STATUS_CHANNEL_ID=your_status_channel_id
RATING_CHANNEL_ID=your_rating_channel_id
TEXT_LOGS_CHANNEL_ID=your_text_logs_channel_id
MEDIA_LOGS_CHANNEL_ID=your_media_logs_channel_id
```

4. Run the bot:
```bash
python bot.py
```

## Usage

### For Users
1. DM the bot to create a new ticket
2. Select a category for your ticket
3. Describe your issue
4. Wait for a support team member to respond
5. Rate your experience after the ticket is closed

### For Support Team
- Use `/tickets` to view all tickets
- Use `/reply` to respond to tickets
- Use `/close` to close tickets
- Use `/status` to change ticket status
- Use `/claim` to claim a ticket

## File Structure

- `bot.py` - Main bot code
- `config.py` - Configuration settings
- `utils.py` - Utility functions
- `requirements.txt` - Required packages
- `README.md` - Documentation
- `LICENSE` - MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

### Developer
- **Name:** YzeedHrb
- **GitHub:** [YzeedHrb](https://github.com/YzeedHrb)
- **Discord:** YzeedHrb#0000

### Special Thanks
- Discord.py team for the amazing library
- All contributors and supporters

## Support

If you need help with this bot, feel free to:
- Open an issue on GitHub
- Contact me on Discord
- Check out the documentation

## Disclaimer

This bot is developed and maintained by YzeedHrb. Any unauthorized distribution or modification of this code is strictly prohibited. 