from lxmfy import LXMFBot, command
import sqlite3
import feedparser
import trafilatura
import pytz
from datetime import datetime, timedelta
import threading
import time

class NewsBot:
    def __init__(self):
        self.bot = LXMFBot(
            name="LXMFy News Bot",
            announce=600,
            admins=[],  # Add your admin hash
            command_prefix="",
            hot_reloading=True,
        )
        
        self.db = sqlite3.connect('feed.db' 
        self.setup_database()
        self.setup_commands()
        
        # Start feed checker thread
        self.checker_thread = threading.Thread(target=self.check_feeds, daemon=True)
        self.checker_thread.start()

    def setup_database(self):
        cursor = self.db.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                last_check TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS users (
                hash TEXT PRIMARY KEY,
                timezone TEXT DEFAULT 'UTC',
                update_time TEXT DEFAULT '09:00',
                active BOOLEAN DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_hash TEXT,
                feed_id INTEGER,
                FOREIGN KEY(user_hash) REFERENCES users(hash),
                FOREIGN KEY(feed_id) REFERENCES feeds(id),
                PRIMARY KEY(user_hash, feed_id)
            );
            
            CREATE TABLE IF NOT EXISTS sent_items (
                id INTEGER PRIMARY KEY,
                feed_id INTEGER,
                item_id TEXT,
                sent_date TIMESTAMP,
                FOREIGN KEY(feed_id) REFERENCES feeds(id)
            );
        ''')
        self.db.commit()

    def setup_commands(self):
        @self.bot.command(
            name="subscribe",
            description="Subscribe to a feed",
            usage="subscribe <feed_url> [name]"
        )
        def subscribe(ctx):
            if len(ctx.args) < 1:
                ctx.reply("Usage: /subscribe <feed_url> [name]")
                return
                
            url = ctx.args[0]
            name = " ".join(ctx.args[1:]) if len(ctx.args) > 1 else url
            
            cursor = self.db.cursor()
            try:
                # Validate feed
                feed = feedparser.parse(url)
                if feed.bozo:
                    ctx.reply("Invalid feed URL")
                    return
                    
                # Add feed if not exists
                cursor.execute('''
                    INSERT OR IGNORE INTO feeds (url, name, last_check)
                    VALUES (?, ?, ?)
                ''', (url, name, datetime.utcnow()))
                
                feed_id = cursor.lastrowid or cursor.execute(
                    'SELECT id FROM feeds WHERE url = ?', (url,)
                ).fetchone()[0]
                
                # Subscribe user
                cursor.execute('''
                    INSERT OR IGNORE INTO users (hash) VALUES (?)
                ''', (ctx.sender,))
                
                cursor.execute('''
                    INSERT OR IGNORE INTO subscriptions (user_hash, feed_id)
                    VALUES (?, ?)
                ''', (ctx.sender, feed_id))
                
                self.db.commit()
                ctx.reply(f"Subscribed to: {name}")
                
            except Exception as e:
                self.db.rollback()
                ctx.reply(f"Error: {str(e)}")

        @self.bot.command(
            name="unsubscribe",
            description="Unsubscribe from a feed",
            usage="unsubscribe <feed_name>"
        )
        def unsubscribe(ctx):
            if not ctx.args:
                ctx.reply("Usage: /unsubscribe <feed_name>")
                return
                
            name = " ".join(ctx.args)
            cursor = self.db.cursor()
            
            cursor.execute('''
                DELETE FROM subscriptions 
                WHERE user_hash = ? AND feed_id IN 
                    (SELECT id FROM feeds WHERE name = ?)
            ''', (ctx.sender, name))
            
            if cursor.rowcount > 0:
                self.db.commit()
                ctx.reply(f"Unsubscribed from: {name}")
            else:
                ctx.reply(f"You're not subscribed to: {name}")

        @self.bot.command(
            name="list",
            description="List your subscribed feeds"
        )
        def list_feeds(ctx):
            cursor = self.db.cursor()
            cursor.execute('''
                SELECT f.name, f.url 
                FROM feeds f
                JOIN subscriptions s ON f.id = s.feed_id
                WHERE s.user_hash = ?
            ''', (ctx.sender,))
            
            feeds = cursor.fetchall()
            if feeds:
                response = "Your subscriptions:\n"
                for name, url in feeds:
                    response += f"- {name}: {url}\n"
            else:
                response = "You have no subscriptions"
            
            ctx.reply(response)

        @self.bot.command(
            name="timezone",
            description="Set your timezone",
            usage="timezone <timezone>",
            examples=["timezone UTC", "timezone America/New_York"]
        )
        def set_timezone(ctx):
            if not ctx.args:
                ctx.reply("Usage: /timezone <timezone>")
                return
                
            tz = " ".join(ctx.args)
            try:
                pytz.timezone(tz)
                cursor = self.db.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (hash, timezone)
                    VALUES (?, ?)
                ''', (ctx.sender, tz))
                self.db.commit()
                ctx.reply(f"Timezone set to: {tz}")
            except Exception:
                ctx.reply("Invalid timezone. Use format like 'UTC' or 'America/New_York'")

        @self.bot.command(
            name="time",
            description="Set daily update time",
            usage="time <HH:MM>",
            examples=["time 09:00"]
        )
        def set_time(ctx):
            if not ctx.args or not ctx.args[0]:
                ctx.reply("Usage: /time HH:MM")
                return
                
            try:
                time = datetime.strptime(ctx.args[0], "%H:%M").strftime("%H:%M")
                cursor = self.db.cursor()
                cursor.execute('''
                    UPDATE users SET update_time = ? WHERE hash = ?
                ''', (time, ctx.sender))
                self.db.commit()
                ctx.reply(f"Update time set to: {time}")
            except ValueError:
                ctx.reply("Invalid time format. Use HH:MM (24-hour format)")

    def check_feeds(self):
        while True:
            try:
                cursor = self.db.cursor()
                
                # Get all active users and their preferences
                cursor.execute('''
                    SELECT u.hash, u.timezone, u.update_time, f.id, f.url, f.name
                    FROM users u
                    JOIN subscriptions s ON u.hash = s.user_hash
                    JOIN feeds f ON s.feed_id = f.id
                    WHERE u.active = 1
                ''')
                
                for user_hash, tz, update_time, feed_id, feed_url, feed_name in cursor.fetchall():
                    # Check if it's time to send updates for this user
                    user_tz = pytz.timezone(tz or 'UTC')
                    user_now = datetime.now(user_tz)
                    update_hour, update_minute = map(int, (update_time or '09:00').split(':'))
                    
                    if user_now.hour == update_hour and user_now.minute == update_minute:
                        self.send_feed_updates(user_hash, feed_id, feed_url, feed_name)
                
            except Exception as e:
                print(f"Feed checker error: {str(e)}")
            
            time.sleep(60)  # Check every minute

    def send_feed_updates(self, user_hash, feed_id, feed_url, feed_name):
        try:
            feed = feedparser.parse(feed_url)
            cursor = self.db.cursor()
            
            for entry in feed.entries[:5]:  # Send top 5 newest entries
                item_id = entry.get('id', entry.get('link', ''))
                
                # Check if already sent
                cursor.execute('''
                    SELECT 1 FROM sent_items 
                    WHERE feed_id = ? AND item_id = ?
                ''', (feed_id, item_id))
                
                if not cursor.fetchone():
                    # Get full text if available
                    full_text = ""
                    if entry.get('link'):
                        downloaded = trafilatura.fetch_url(entry.link)
                        if downloaded:
                            full_text = trafilatura.extract(downloaded)
                    
                    message = f"""
{feed_name}

{entry.get('title', 'No title')}

{entry.get('description', full_text or 'No description')}

Link: {entry.get('link', 'No link')}
"""
                    self.bot.send(user_hash, message, title=f"News: {feed_name}")
                    
                    cursor.execute('''
                        INSERT INTO sent_items (feed_id, item_id, sent_date)
                        VALUES (?, ?, ?)
                    ''', (feed_id, item_id, datetime.utcnow()))
                    self.db.commit()
                    
        except Exception as e:
            print(f"Error sending feed updates: {str(e)}")

    def run(self):
        self.bot.run()

if __name__ == "__main__":
    bot = NewsBot()
    bot.run()