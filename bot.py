"""
Discord Support Bot
Developed by YzeedHrb
GitHub: https://github.com/YzeedHrb
Discord: YzeedHrb#0000

This bot is developed and maintained by YzeedHrb.
Any unauthorized distribution or modification of this code is strictly prohibited.
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import datetime
import json
from discord.ui import Button, View
import asyncio
from config import *
from discord.ext import tasks

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد البوت
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.dm_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration IDs
TICKETS_CATEGORY_ID = int(os.getenv('TICKETS_CATEGORY_ID'))
STATUS_CHANNEL_ID = int(os.getenv('STATUS_CHANNEL_ID'))
TEXT_LOGS_CHANNEL_ID = int(os.getenv('TEXT_LOGS_CHANNEL_ID'))
MEDIA_LOGS_CHANNEL_ID = int(os.getenv('MEDIA_LOGS_CHANNEL_ID'))
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID'))
SUPPORT_TEAM_ROLE_ID = int(os.getenv('SUPPORT_TEAM_ROLE_ID'))
RATING_CHANNEL_ID = int(os.getenv('RATING_CHANNEL_ID', 0))

# Ticket Statuses
TICKET_STATUSES = {
    "open": "🟢 Open",
    "reviewing": "🟡 Under Review",
    "waiting": "🟠 Waiting for User Response",
    "closed": "🔴 Closed"
}

class Ticket:
    def __init__(self, user_id, channel_id):
        self.user_id = user_id
        self.channel_id = channel_id
        self.status = "open"
        self.created_at = datetime.now()
        self.claimed_by = None
        self.messages = []
        self.attachments = []
        self.last_updated = datetime.now()
        self.rating = None
        self.rating_comment = None
        self.category = None  # New field for ticket category

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "claimed_by": self.claimed_by,
            "last_updated": self.last_updated.isoformat(),
            "messages": self.messages,
            "attachments": self.attachments,
            "rating": self.rating,
            "rating_comment": self.rating_comment,
            "category": self.category
        }

# Dictionaries for storing data
tickets = {}
ticket_statuses = {}
ticket_logs = {}

# Ticket Categories
TICKET_CATEGORIES = {
    "general": "General Support",
    "technical": "Technical Support",
    "billing": "Billing Support",
    "other": "Other"
}

class CategorySelect(discord.ui.Select):
    def __init__(self, ticket):
        super().__init__(
            placeholder="Select ticket category",
            options=[
                discord.SelectOption(label=label, value=value)
                for value, label in TICKET_CATEGORIES.items()
            ]
        )
        self.ticket = ticket

    async def callback(self, interaction: discord.Interaction):
        self.ticket.category = self.values[0]
        await interaction.response.send_message(
            f"Ticket category set to: {TICKET_CATEGORIES[self.values[0]]}",
            ephemeral=True
        )
        await save_ticket_data()

class CategoryView(discord.ui.View):
    def __init__(self, ticket):
        super().__init__(timeout=None)
        self.add_item(CategorySelect(ticket))

class CloseConfirmView(View):
    def __init__(self, ticket_channel):
        super().__init__(timeout=60)
        self.ticket_channel = ticket_channel
        
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        self.stop()
        
        view = AfterCloseView(self.ticket_channel)
        embed = discord.Embed(
            title="Ticket Closed",
            description="What would you like to do now?",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, view=view)
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        self.stop()
        await interaction.followup.send("Ticket closure cancelled")

class AfterCloseView(View):
    def __init__(self, ticket_channel):
        super().__init__(timeout=60)
        self.ticket_channel = ticket_channel
        self.ticket = tickets[ticket_channel.id]
        
    @discord.ui.button(label="Reopen", style=discord.ButtonStyle.green)
    async def reopen_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        self.stop()
        
        self.ticket.status = "open"
        self.ticket.last_updated = datetime.now()
        
        embed = discord.Embed(
            title="Ticket Reopened",
            description="The ticket has been reopened successfully",
            color=discord.Color.green()
        )
        embed.set_footer(text="Developed by YzeedHrb")
        await interaction.followup.send(embed=embed)
        await update_status_channel(interaction.guild)
        await save_ticket_data()
        
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        self.stop()
        
        # Save ticket log
        await save_ticket_log(self.ticket)
        
        # Send rating request to user
        user = await bot.fetch_user(self.ticket.user_id)
        rating_embed = discord.Embed(
            title="Rate Your Support Experience",
            description="Please rate your experience with our support team",
            color=discord.Color.gold()
        )
        rating_embed.add_field(
            name="Ticket Details",
            value=f"Ticket ID: #{self.ticket.channel_id}\n"
                  f"Category: {TICKET_CATEGORIES.get(self.ticket.category, 'Not set')}\n"
                  f"Support Team: <@{self.ticket.claimed_by}>",
            inline=False
        )
        rating_embed.set_footer(text="Developed by YzeedHrb")
        
        view = RatingButtons(self.ticket)
        await user.send(embed=rating_embed, view=view)
        
        # Delete channel
        await self.ticket_channel.delete()
        
        # Remove ticket from memory
        del tickets[self.ticket_channel.id]
        
        # Save tickets data
        await save_ticket_data()
        
        # Send confirmation message in the original channel
        try:
            embed = discord.Embed(
                title="Ticket Deleted",
                description="The ticket has been deleted successfully",
                color=discord.Color.red()
            )
            embed.set_footer(text="Developed by YzeedHrb")
            await interaction.followup.send(embed=embed)
        except discord.errors.HTTPException:
            # If the channel is already deleted, send to the user's DM
            await user.send("Your ticket has been deleted successfully.")
        
        await update_status_channel(interaction.guild)

async def save_ticket_log(ticket: Ticket):
    log_data = ticket.to_dict()
    
    # Save log to JSON file
    log_file = f"ticket_logs/ticket_{ticket.channel_id}.json"
    os.makedirs("ticket_logs", exist_ok=True)
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=4)
    
    # Send log to log channels
    text_logs = bot.get_channel(TEXT_LOGS_CHANNEL_ID)
    media_logs = bot.get_channel(MEDIA_LOGS_CHANNEL_ID)
    
    if text_logs:
        # Create log embed
        log_embed = discord.Embed(
            title=f"Ticket #{ticket.channel_id} Log",
            description="Complete ticket history and information",
            color=discord.Color.blue()
        )
        
        # Add ticket details
        log_embed.add_field(
            name="Ticket Information",
            value=f"**Status:** {TICKET_STATUSES[ticket.status]}\n"
                  f"**Created by:** <@{ticket.user_id}>\n"
                  f"**Created at:** {ticket.created_at.strftime('%Y-%m-%d %I:%M %p')}\n"
                  f"**Last updated:** {ticket.last_updated.strftime('%Y-%m-%d %I:%M %p')}\n"
                  f"**Category:** {TICKET_CATEGORIES.get(ticket.category, 'Not set')}\n"
                  f"**Claimed by:** {f'<@{ticket.claimed_by}>' if ticket.claimed_by else 'Not claimed'}",
            inline=False
        )
        
        # Add messages in a formatted way
        if ticket.messages:
            messages_text = ""
            for msg in ticket.messages:
                author = msg.get('author', 'Unknown')
                content = msg.get('content', 'No content')
                timestamp = msg.get('timestamp', '')
                if timestamp:
                    try:
                        timestamp = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %I:%M %p')
                    except:
                        pass
                messages_text += f"**{author}** ({timestamp}):\n{content}\n\n"
            
            # Split messages if they're too long
            if len(messages_text) > 1024:
                message_chunks = [messages_text[i:i+1024] for i in range(0, len(messages_text), 1024)]
                for i, chunk in enumerate(message_chunks):
                    log_embed.add_field(
                        name=f"Messages (Part {i+1})",
                        value=chunk,
                        inline=False
                    )
            else:
                log_embed.add_field(
                    name="Messages",
                    value=messages_text,
                    inline=False
                )
        
        # Add rating if exists
        if ticket.rating:
            rating_text = f"Rating: {'⭐' * ticket.rating}"
            if ticket.rating_comment:
                rating_text += f"\nComment: {ticket.rating_comment}"
            log_embed.add_field(
                name="Rating",
                value=rating_text,
                inline=False
            )
        
        log_embed.set_footer(text="Developed by YzeedHrb")
        await text_logs.send(embed=log_embed)
        await text_logs.send(file=discord.File(log_file))
    
    if media_logs and ticket.attachments:
        # Send attachments
        for attachment in ticket.attachments:
            await media_logs.send(f"**Ticket #{ticket.channel_id}** - {attachment}")

# إضافة أزرار تغيير الحالة
class StatusButtons(discord.ui.View):
    def __init__(self, ticket):
        super().__init__(timeout=None)
        self.ticket = ticket
        
        for status, label in TICKET_STATUSES.items():
            button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                custom_id=f"status_{status}"
            )
            button.callback = lambda i, b=button: self.status_callback(i, b)
            self.add_item(button)
    
    async def status_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        status = button.custom_id.split("_")[1]
        self.ticket.status = status
        self.ticket.last_updated = datetime.now()
        
        embed = discord.Embed(
            title="Ticket Status Changed",
            description=f"Ticket status changed to {TICKET_STATUSES[status]}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Developed by YzeedHrb")
        await interaction.channel.send(embed=embed)
        await update_status_channel(interaction.guild)
        await interaction.response.send_message("Ticket status changed successfully!", ephemeral=True)
        
        # Save ticket data
        await save_ticket_data()

# وظيفة حفظ التذاكر
async def save_ticket_data():
    tickets_data = {channel_id: ticket.to_dict() for channel_id, ticket in tickets.items()}
    with open("tickets.json", "w", encoding="utf-8") as f:
        json.dump(tickets_data, f, ensure_ascii=False, indent=4)

# وظيفة تحميل التذاكر
async def load_ticket_data():
    if os.path.exists("tickets.json"):
        with open("tickets.json", "r", encoding="utf-8") as f:
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

async def create_ticket_channel(user: discord.User, guild: discord.Guild):
    # Get or create category
    category = guild.get_channel(TICKETS_CATEGORY_ID)
    if not category:
        category = await guild.create_category("Support Tickets")
    
    # Create ticket channel
    ticket_channel = await guild.create_text_channel(
        f"ticket-{user.name}",
        category=category,
        overwrites={
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.get_role(ADMIN_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(SUPPORT_TEAM_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
    )
    
    # Create ticket
    ticket = Ticket(user.id, ticket_channel.id)
    tickets[ticket_channel.id] = ticket
    
    # Send welcome message
    embed = discord.Embed(
        title="New Support Ticket",
        description=f"A new support ticket has been created by {user.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="Status", value=TICKET_STATUSES["open"])
    embed.add_field(name="Created At", value=ticket.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    
    await ticket_channel.send(embed=embed)
    
    # Mention support team
    support_team = guild.get_role(SUPPORT_TEAM_ROLE_ID)
    if support_team:
        await ticket_channel.send(f"{support_team.mention} New support ticket needs attention!")
    
    # Add status buttons
    view = StatusButtons(ticket)
    await ticket_channel.send(view=view)
    
    # Add category selection
    category_view = CategoryView(ticket)
    await ticket_channel.send("Please select a category for your ticket:", view=category_view)
    
    # Save ticket data
    await save_ticket_data()
    
    return ticket_channel

async def update_status_channel(guild: discord.Guild):
    status_channel = guild.get_channel(STATUS_CHANNEL_ID)
    if not status_channel:
        return
    
    # Create main status embed
    main_embed = discord.Embed(
        title="📊 Ticket Status Overview",
        description="Real-time status of all support tickets",
        color=discord.Color.blue()
    )
    main_embed.set_footer(text="Developed by YzeedHrb")
    
    # Count tickets by status
    open_tickets = []
    reviewing_tickets = []
    waiting_tickets = []
    
    for ticket_id, ticket in tickets.items():
        channel = guild.get_channel(ticket_id)
        if not channel:
            continue
            
        ticket_info = f"Ticket #{ticket_id}\n"
        ticket_info += f"Created by: <@{ticket.user_id}>\n"
        ticket_info += f"Category: {TICKET_CATEGORIES.get(ticket.category, 'Not set')}\n"
        if ticket.claimed_by:
            ticket_info += f"Claimed by: <@{ticket.claimed_by}>\n"
        ticket_info += f"Created: {ticket.created_at.strftime('%Y-%m-%d %I:%M %p')}\n"
        
        if ticket.status == "open":
            open_tickets.append(ticket_info)
        elif ticket.status == "reviewing":
            reviewing_tickets.append(ticket_info)
        elif ticket.status == "waiting":
            waiting_tickets.append(ticket_info)
    
    # Add fields to main embed
    main_embed.add_field(
        name=f"🟢 Open Tickets ({len(open_tickets)})",
        value="\n".join(open_tickets) if open_tickets else "No open tickets",
        inline=False
    )
    main_embed.add_field(
        name=f"🟡 Reviewing Tickets ({len(reviewing_tickets)})",
        value="\n".join(reviewing_tickets) if reviewing_tickets else "No tickets under review",
        inline=False
    )
    main_embed.add_field(
        name=f"🟠 Waiting Tickets ({len(waiting_tickets)})",
        value="\n".join(waiting_tickets) if waiting_tickets else "No waiting tickets",
        inline=False
    )
    
    # Clear channel and send new status
    async for message in status_channel.history():
        await message.delete()
    
    await status_channel.send(embed=main_embed)

# Add webhook for status updates
async def setup_status_webhook(guild: discord.Guild):
    status_channel = guild.get_channel(STATUS_CHANNEL_ID)
    if not status_channel:
        return
    
    # Delete existing webhooks
    webhooks = await status_channel.webhooks()
    for webhook in webhooks:
        await webhook.delete()
    
    # Create new webhook
    webhook = await status_channel.create_webhook(name="Ticket Status")
    return webhook

# Add background task for status updates
@tasks.loop(seconds=30)
async def update_status_task():
    for guild in bot.guilds:
        await update_status_channel(guild)

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user.name}')
    try:
        # Load saved tickets
        await load_ticket_data()
        
        # Setup status webhook
        for guild in bot.guilds:
            await setup_status_webhook(guild)
        
        # Start status update task
        update_status_task.start()
        
        # Sync commands
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Handle bot commands
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    # Handle DMs
    if isinstance(message.channel, discord.DMChannel):
        # Find existing ticket
        ticket_channel = None
        for channel_id, ticket in tickets.items():
            if ticket.user_id == message.author.id:
                ticket_channel = bot.get_channel(channel_id)
                break
        
        # Create new ticket if none exists
        if not ticket_channel:
            support_guild = bot.get_guild(int(os.getenv('SUPPORT_GUILD_ID')))
            if not support_guild:
                await message.author.send("Sorry, there was an error connecting to the support server.")
                return
                
            ticket_channel = await create_ticket_channel(message.author, support_guild)
            await message.author.send("Your ticket has been created! You can now send your message.")
        
        # Send message to ticket channel
        content = f"**{message.author.name}:** {message.content}"
        await ticket_channel.send(content)
        
        # Update ticket messages
        ticket = tickets[ticket_channel.id]
        ticket.messages.append({
            "author": message.author.name,
            "content": message.content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Handle attachments
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith(('image/', 'video/')):
                    await ticket_channel.send(attachment.url)
                    ticket.attachments.append(attachment.url)
        
        # Save ticket data
        await save_ticket_data()

@bot.tree.command(name="reply", description="Reply to user message")
async def reply(interaction: discord.Interaction, message: str):
    if interaction.channel.id not in tickets:
        await interaction.response.send_message("This command can only be used in ticket channels!", ephemeral=True)
        return
    
    ticket = tickets[interaction.channel.id]
    user = await bot.fetch_user(ticket.user_id)
    
    try:
        await user.send(f"**Support ({interaction.user.name}):** {message}")
        await interaction.response.send_message("Reply sent successfully!", ephemeral=True)
        
        # Update ticket messages
        ticket.messages.append({
            "author": f"Support ({interaction.user.name})",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save ticket data
        await save_ticket_data()
    except Exception as e:
        await interaction.response.send_message(f"Error sending reply: {str(e)}", ephemeral=True)

@bot.tree.command(name="close", description="Close the ticket")
async def close(interaction: discord.Interaction):
    if interaction.channel.id not in tickets:
        await interaction.response.send_message("This command can only be used in ticket channels!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="Confirm Closure",
        description="Are you sure you want to close this ticket?",
        color=discord.Color.yellow()
    )
    
    view = CloseConfirmView(interaction.channel)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="claim", description="Claim the ticket")
async def claim(interaction: discord.Interaction):
    if interaction.channel.id not in tickets:
        await interaction.response.send_message("This command can only be used in ticket channels!", ephemeral=True)
        return
    
    ticket = tickets[interaction.channel.id]
    if ticket.claimed_by:
        await interaction.response.send_message("This ticket is already claimed!", ephemeral=True)
        return
    
    ticket.claimed_by = interaction.user.id
    ticket.status = "reviewing"
    ticket.last_updated = datetime.now()
    
    embed = discord.Embed(
        title="Ticket Claimed",
        description=f"Ticket claimed by {interaction.user.mention}",
        color=discord.Color.yellow()
    )
    await interaction.channel.send(embed=embed)
    
    await update_status_channel(interaction.guild)
    await interaction.response.send_message("Ticket claimed successfully!", ephemeral=True)

@bot.tree.command(name="status", description="Change ticket status")
async def status(interaction: discord.Interaction, status: str):
    if interaction.channel.id not in tickets:
        await interaction.response.send_message("This command can only be used in ticket channels!", ephemeral=True)
        return
    
    if status not in TICKET_STATUSES:
        await interaction.response.send_message(
            f"Invalid status! Must be one of: {', '.join(TICKET_STATUSES.keys())}",
            ephemeral=True
        )
        return
    
    ticket = tickets[interaction.channel.id]
    ticket.status = status
    ticket.last_updated = datetime.now()
    
    embed = discord.Embed(
        title="Ticket Status Changed",
        description=f"Ticket status changed to {TICKET_STATUSES[status]}",
        color=discord.Color.blue()
    )
    await interaction.channel.send(embed=embed)
    await update_status_channel(interaction.guild)
    await interaction.response.send_message("Ticket status changed successfully!", ephemeral=True)

# إضافة أزرار التقييم
class RatingButtons(discord.ui.View):
    def __init__(self, ticket):
        super().__init__(timeout=None)
        self.ticket = ticket
        
        for i in range(1, 6):
            button = discord.ui.Button(
                label=str(i) + " ⭐",
                style=discord.ButtonStyle.primary,
                custom_id=f"rating_{i}"
            )
            button.callback = lambda i, b=button: self.rating_callback(i, b)
            self.add_item(button)
    
    async def rating_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the user is the ticket creator
        if interaction.user.id != self.ticket.user_id:
            await interaction.response.send_message(
                "Only the ticket creator can rate the support service!",
                ephemeral=True
            )
            return
        
        rating = int(button.custom_id.split("_")[1])
        self.ticket.rating = rating
        
        # Request rating comment
        await interaction.response.send_message(
            "Thank you for your rating! Would you like to add a comment about our service? (Type 'no' if you don't want to add a comment)",
            ephemeral=True
        )
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        
        try:
            comment_msg = await bot.wait_for('message', check=check, timeout=300)
            if comment_msg.content.lower() != 'no':
                self.ticket.rating_comment = comment_msg.content
        except asyncio.TimeoutError:
            pass
        
        # Send thank you message
        thank_embed = discord.Embed(
            title="Thank You!",
            description="Thank you for your feedback! Your ticket has been closed and your rating has been recorded.",
            color=discord.Color.green()
        )
        thank_embed.add_field(
            name="Your Rating",
            value="⭐" * rating,
            inline=True
        )
        if self.ticket.rating_comment:
            thank_embed.add_field(
                name="Your Comment",
                value=self.ticket.rating_comment,
                inline=True
            )
        thank_embed.set_footer(text="Developed by YzeedHrb")
        await interaction.channel.send(embed=thank_embed)
        
        # Save ticket data
        await save_ticket_data()
        
        # Send rating to rating channel
        if RATING_CHANNEL_ID:
            rating_channel = bot.get_channel(RATING_CHANNEL_ID)
            if rating_channel:
                rating_embed = discord.Embed(
                    title="New Ticket Rating",
                    description=f"Ticket #{self.ticket.channel_id} has been rated",
                    color=discord.Color.gold()
                )
                rating_embed.add_field(
                    name="Ticket Details",
                    value=f"Category: {TICKET_CATEGORIES.get(self.ticket.category, 'Not set')}\n"
                          f"Created by: <@{self.ticket.user_id}>\n"
                          f"Handled by: <@{self.ticket.claimed_by}>",
                    inline=False
                )
                rating_embed.add_field(
                    name="Rating",
                    value="⭐" * rating,
                    inline=True
                )
                if self.ticket.rating_comment:
                    rating_embed.add_field(
                        name="Comment",
                        value=self.ticket.rating_comment,
                        inline=True
                    )
                rating_embed.add_field(
                    name="Timeline",
                    value=f"Created: {self.ticket.created_at.strftime('%Y-%m-%d %I:%M %p')}\n"
                          f"Closed: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}",
                    inline=False
                )
                rating_embed.set_footer(text="Developed by YzeedHrb")
                await rating_channel.send(embed=rating_embed)

# تشغيل البوت
bot.run(os.getenv('TOKEN')) 