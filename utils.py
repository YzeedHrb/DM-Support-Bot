import json
import os
from datetime import datetime
import discord
from config import TICKETS_FILE, TICKET_LOGS_DIR

async def save_ticket_data(tickets):
    """Save tickets data to file"""
    tickets_data = {channel_id: ticket.to_dict() for channel_id, ticket in tickets.items()}
    with open(TICKETS_FILE, "w", encoding="utf-8") as f:
        json.dump(tickets_data, f, ensure_ascii=False, indent=4)

async def load_ticket_data():
    """Load tickets data from file"""
    tickets = {}
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, "r", encoding="utf-8") as f:
            tickets_data = json.load(f)
            for channel_id, ticket_data in tickets_data.items():
                ticket = Ticket(
                    ticket_data["user_id"],
                    int(channel_id)
                )
                ticket.status = ticket_data["status"]
                ticket.created_at = datetime.fromisoformat(ticket_data["created_at"])
                ticket.claimed_by = ticket_data["claimed_by"]
                ticket.last_updated = datetime.fromisoformat(ticket_data["last_updated"])
                ticket.messages = ticket_data["messages"]
                ticket.attachments = ticket_data["attachments"]
                ticket.rating = ticket_data["rating"]
                ticket.rating_comment = ticket_data["rating_comment"]
                ticket.category = ticket_data["category"]
                tickets[int(channel_id)] = ticket
    return tickets

async def save_ticket_log(ticket):
    """Save ticket log to file"""
    log_data = ticket.to_dict()
    log_file = f"{TICKET_LOGS_DIR}/ticket_{ticket.channel_id}.json"
    os.makedirs(TICKET_LOGS_DIR, exist_ok=True)
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=4)
    
    return log_file

def format_ticket_embed(ticket, user):
    """Format ticket information into an embed"""
    embed = discord.Embed(
        title="Ticket Information",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Status", value=TICKET_STATUSES[ticket.status])
    embed.add_field(name="Created By", value=f"<@{ticket.user_id}>")
    embed.add_field(name="Created At", value=ticket.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    embed.add_field(name="Last Updated", value=ticket.last_updated.strftime("%Y-%m-%d %H:%M:%S"))
    
    if ticket.claimed_by:
        embed.add_field(name="Claimed By", value=f"<@{ticket.claimed_by}>")
    
    if ticket.category:
        embed.add_field(name="Category", value=TICKET_CATEGORIES[ticket.category])
    
    if ticket.rating:
        embed.add_field(name="Rating", value="⭐" * ticket.rating)
        if ticket.rating_comment:
            embed.add_field(name="Rating Comment", value=ticket.rating_comment)
    
    return embed 
