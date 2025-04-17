import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN = os.getenv('TOKEN')
SUPPORT_GUILD_ID = int(os.getenv('SUPPORT_GUILD_ID'))
TICKETS_CATEGORY_ID = int(os.getenv('TICKETS_CATEGORY_ID'))
STATUS_CHANNEL_ID = int(os.getenv('STATUS_CHANNEL_ID'))
TEXT_LOGS_CHANNEL_ID = int(os.getenv('TEXT_LOGS_CHANNEL_ID'))
MEDIA_LOGS_CHANNEL_ID = int(os.getenv('MEDIA_LOGS_CHANNEL_ID'))
RATING_CHANNEL_ID = int(os.getenv('RATING_CHANNEL_ID', 0))
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID'))
SUPPORT_TEAM_ROLE_ID = int(os.getenv('SUPPORT_TEAM_ROLE_ID'))

# Ticket Statuses
TICKET_STATUSES = {
    "open": "🟢 Open",
    "reviewing": "🟡 Under Review",
    "waiting": "🟠 Waiting for User Response",
    "closed": "🔴 Closed"
}

# Ticket Categories
TICKET_CATEGORIES = {
    "general": "General Support",
    "technical": "Technical Support",
    "billing": "Billing Support",
    "other": "Other"
}

# File Paths
TICKETS_FILE = "tickets.json"
TICKET_LOGS_DIR = "ticket_logs" 
