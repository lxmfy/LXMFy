"""Wake-up call bot template with timezone support.

This bot allows users to schedule wake-up calls at specific times
in their local timezone. The bot will call users at the scheduled time
and play an alarm sound or message.
"""

import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, available_timezones

from lxmfy import LXMFBot
from lxmfy.voice import VoiceCallManager


class WakeupCallBot:
    """A bot that makes wake-up calls to users at scheduled times.
    
    Users can set their timezone and schedule wake-up calls using text commands.
    The bot will initiate a voice call at the specified time.
    """
    
    def __init__(self, test_mode=False, alarm_audio_path=None, use_tts=True):
        """Initialize the WakeupCallBot.
        
        Args:
            test_mode: Whether to run in test mode
            alarm_audio_path: Path to audio file to play during wake-up calls
            use_tts: Whether to use text-to-speech for wake-up messages (default: True)
        """
        self.bot = LXMFBot(
            name="Wake-Up Call Bot",
            announce=600,
            command_prefix="",
            storage_type="sqlite",
            storage_path="data/wakeup_calls.db",
            test_mode=test_mode,
        )
        
        self.alarm_audio_path = alarm_audio_path or self._get_default_alarm_path()
        self.voice_manager = None
        self.use_tts = use_tts
        self.tts_available = self._check_tts_available()
        
        if use_tts and not self.tts_available:
            self.bot.logger.warning(
                "TTS requested but espeak-ng or ffmpeg not available. "
                "Install with: sudo apt install espeak-ng ffmpeg"
            )
        
        self._init_voice_manager()
        self.setup_commands()
        
        self.bot.scheduler.add_task(
            "check_wakeup_calls",
            self._check_wakeup_calls,
            "*/1 * * * *",
        )
    
    def _check_tts_available(self):
        """Check if TTS tools (espeak-ng and ffmpeg) are available.
        
        Returns:
            bool: True if both espeak-ng and ffmpeg are available
        """
        espeak_available = shutil.which("espeak-ng") is not None
        ffmpeg_available = shutil.which("ffmpeg") is not None
        
        if espeak_available and ffmpeg_available:
            return True
        
        if not espeak_available:
            self.bot.logger.debug("espeak-ng not found in PATH")
        if not ffmpeg_available:
            self.bot.logger.debug("ffmpeg not found in PATH")
        
        return False
    
    def _get_default_alarm_path(self):
        """Get the default alarm audio path.
        
        Returns:
            str: Path to default alarm audio file, or None if not found
        """
        try:
            import LXST
            lxst_path = os.path.dirname(LXST.__file__)
            default_alarm = os.path.join(lxst_path, "Sounds", "ringer.opus")
            if os.path.isfile(default_alarm):
                return default_alarm
        except (ImportError, AttributeError):
            pass
        return None
    
    def _generate_tts_audio(self, text, output_path):
        """Generate speech audio from text using espeak-ng and ffmpeg.
        
        Args:
            text: Text to speak
            output_path: Path to save the opus audio file
            
        Returns:
            bool: True if generation was successful
        """
        if not self.tts_available:
            return False
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
            
            espeak_cmd = [
                "espeak-ng",
                "-v", "en",
                "-s", "150",
                "-a", "200",
                "-w", temp_wav_path,
                text
            ]
            
            result = subprocess.run(
                espeak_cmd,
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.bot.logger.error(f"espeak-ng failed: {result.stderr.decode()}")
                os.unlink(temp_wav_path)
                return False
            
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", temp_wav_path,
                "-c:a", "libopus",
                "-b:a", "24k",
                "-vbr", "on",
                "-y",
                output_path
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                timeout=30
            )
            
            os.unlink(temp_wav_path)
            
            if result.returncode != 0:
                self.bot.logger.error(f"ffmpeg failed: {result.stderr.decode()}")
                return False
            
            return os.path.isfile(output_path)
            
        except subprocess.TimeoutExpired:
            self.bot.logger.error("TTS generation timed out")
            return False
        except Exception as e:
            self.bot.logger.error(f"TTS generation failed: {e}")
            return False
    
    def _init_voice_manager(self):
        """Initialize the voice call manager."""
        try:
            self.voice_manager = VoiceCallManager(
                self.bot.identity,
                ring_time=60,
                wait_time=90
            )
            self.voice_manager.announce()
        except RuntimeError as e:
            self.bot.logger.error(f"Failed to initialize voice manager: {e}")
            self.bot.logger.error("Voice calling features will be disabled")
    
    def setup_commands(self):
        """Set up the bot's commands for managing wake-up calls."""
        
        @self.bot.command(name="identity", description="Set your identity address for voice calls")
        def set_identity(ctx):
            """Set the user's identity address for receiving voice calls.
            
            Args:
                ctx: Command context containing sender and arguments
            """
            if not self.voice_manager:
                ctx.reply("Voice calling is not available on this bot")
                return
            
            if not ctx.args:
                user_settings = self._get_user_settings(ctx.sender)
                current_identity = user_settings.get("identity_address")
                if current_identity:
                    ctx.reply(
                        f"Your identity address: {current_identity}\n\n"
                        "Usage: identity <address>\n"
                        "Example: identity 63711db779086bc3e45656e25a125a07\n\n"
                        "Your identity address is your RNS identity hash (not your LXMF address).\n"
                        "Find it by running 'rnstatus' or checking your RNS identity file."
                    )
                else:
                    ctx.reply(
                        "No identity address set.\n\n"
                        "Usage: identity <address>\n"
                        "Example: identity 63711db779086bc3e45656e25a125a07\n\n"
                        "Your identity address is your RNS identity hash (not your LXMF address).\n"
                        "This is required for receiving voice calls.\n"
                        "Find it by running 'rnstatus' or checking your RNS identity file."
                    )
                return
            
            identity_address = ctx.args[0].lower().replace(":", "").replace(" ", "")
            
            try:
                bytes.fromhex(identity_address)
            except ValueError:
                ctx.reply(
                    "Invalid identity address format.\n"
                    "Must be a hex string (e.g., 63711db779086bc3e45656e25a125a07)"
                )
                return
            
            if len(identity_address) != 32:
                ctx.reply(
                    f"Invalid identity address length: {len(identity_address)} characters.\n"
                    "Expected 32 hex characters (16 bytes)."
                )
                return
            
            user_settings = self._get_user_settings(ctx.sender)
            user_settings["identity_address"] = identity_address
            self._save_user_settings(ctx.sender, user_settings)
            
            ctx.reply(
                f"Identity address set to: {identity_address}\n"
                "You can now receive wake-up calls!"
            )
        
        @self.bot.command(name="timezone", description="Set your timezone")
        def set_timezone(ctx):
            """Set the user's timezone for wake-up calls.
            
            Args:
                ctx: Command context containing sender and arguments
            """
            if not ctx.args:
                current_tz = self._get_user_timezone(ctx.sender)
                ctx.reply(
                    f"Your current timezone: {current_tz}\n\n"
                    "Usage: timezone <timezone>\n"
                    "Example: timezone America/New_York\n"
                    "Example: timezone Europe/London\n"
                    "Example: timezone Asia/Tokyo"
                )
                return
            
            timezone_str = ctx.args[0]
            
            if timezone_str not in available_timezones():
                ctx.reply(
                    f"Invalid timezone: {timezone_str}\n"
                    "Use standard IANA timezone names like:\n"
                    "America/New_York, Europe/London, Asia/Tokyo"
                )
                return
            
            user_settings = self._get_user_settings(ctx.sender)
            user_settings["timezone"] = timezone_str
            self._save_user_settings(ctx.sender, user_settings)
            
            ctx.reply(f"Timezone set to: {timezone_str}")
        
        @self.bot.command(name="wakeup", description="Schedule a wake-up call")
        def schedule_wakeup(ctx):
            """Schedule a wake-up call.
            
            Args:
                ctx: Command context containing sender and arguments
            """
            if not self.voice_manager:
                ctx.reply("Voice calling is not available on this bot")
                return
            
            user_settings = self._get_user_settings(ctx.sender)
            if not user_settings.get("identity_address"):
                ctx.reply(
                    "You must set your identity address first!\n"
                    "Use: identity <your_identity_address>\n\n"
                    "Your identity address is your RNS identity hash.\n"
                    "Find it by running 'rnstatus' or checking your RNS identity file."
                )
                return
            
            if not ctx.args:
                tts_info = ""
                if self.use_tts and self.tts_available:
                    tts_info = "\n\nYour label will be spoken as the wake-up message!"
                
                ctx.reply(
                    "Usage: wakeup <time> [label]\n"
                    "Examples:\n"
                    "  wakeup 07:00 Morning alarm\n"
                    "  wakeup 14:30 Afternoon meeting\n"
                    "  wakeup tomorrow 06:00 Early start\n\n"
                    "Time format: HH:MM (24-hour format)\n"
                    f"You can also use: today, tomorrow, or +Nd (N days from now){tts_info}"
                )
                return
            
            time_str = ctx.args[0]
            label = " ".join(ctx.args[1:]) if len(ctx.args) > 1 else "Wake up!"
            
            user_tz = self._get_user_timezone(ctx.sender)
            
            try:
                wakeup_time = self._parse_wakeup_time(time_str, ctx.args[1:2], user_tz)
            except ValueError as e:
                ctx.reply(f"Invalid time format: {e}")
                return
            
            if wakeup_time <= datetime.now(ZoneInfo(user_tz)):
                ctx.reply("Wake-up time must be in the future")
                return
            
            wakeup_call = {
                "user": ctx.sender,
                "time": wakeup_time.timestamp(),
                "label": label,
                "timezone": user_tz,
                "created": time.time(),
            }
            
            wakeup_calls = self.bot.storage.get("wakeup_calls", [])
            wakeup_calls.append(wakeup_call)
            self.bot.storage.set("wakeup_calls", wakeup_calls)
            
            time_str = wakeup_time.strftime("%Y-%m-%d %H:%M %Z")
            
            tts_note = ""
            if self.use_tts and self.tts_available:
                tts_note = "\n\nYour wake-up call will say: '{}'".format(
                    self._format_tts_message(label, user_tz, wakeup_time)
                )
            
            ctx.reply(
                f"Wake-up call scheduled!\n"
                f"Time: {time_str}\n"
                f"Label: {label}{tts_note}"
            )
        
        @self.bot.command(name="list", description="List your wake-up calls")
        def list_wakeups(ctx):
            """List the user's scheduled wake-up calls.
            
            Args:
                ctx: Command context
            """
            wakeup_calls = self.bot.storage.get("wakeup_calls", [])
            user_calls = [c for c in wakeup_calls if c["user"] == ctx.sender]
            
            if not user_calls:
                ctx.reply("You have no scheduled wake-up calls")
                return
            
            user_tz = self._get_user_timezone(ctx.sender)
            tz = ZoneInfo(user_tz)
            
            response = f"Your wake-up calls (timezone: {user_tz}):\n\n"
            for i, call in enumerate(sorted(user_calls, key=lambda x: x["time"]), 1):
                wakeup_time = datetime.fromtimestamp(call["time"], tz)
                response += (
                    f"{i}. {call['label']}\n"
                    f"   {wakeup_time.strftime('%Y-%m-%d %H:%M %Z')}\n\n"
                )
            
            ctx.reply(response.rstrip())
        
        @self.bot.command(name="cancel", description="Cancel a wake-up call")
        def cancel_wakeup(ctx):
            """Cancel a scheduled wake-up call.
            
            Args:
                ctx: Command context
            """
            if not ctx.args:
                ctx.reply("Usage: cancel <number>\nUse 'list' to see your wake-up calls")
                return
            
            try:
                index = int(ctx.args[0]) - 1
            except ValueError:
                ctx.reply("Invalid number. Use 'list' to see your wake-up calls")
                return
            
            wakeup_calls = self.bot.storage.get("wakeup_calls", [])
            user_calls = [c for c in wakeup_calls if c["user"] == ctx.sender]
            
            if index < 0 or index >= len(user_calls):
                ctx.reply("Invalid wake-up call number")
                return
            
            call_to_cancel = user_calls[index]
            wakeup_calls = [c for c in wakeup_calls if c != call_to_cancel]
            self.bot.storage.set("wakeup_calls", wakeup_calls)
            
            ctx.reply(f"Cancelled wake-up call: {call_to_cancel['label']}")
        
        @self.bot.command(name="help", description="Show available commands")
        def show_help(ctx):
            """Show help information for all commands.
            
            Args:
                ctx: Command context
            """
            tts_status = ""
            if self.use_tts:
                if self.tts_available:
                    tts_status = "\n\nText-to-Speech: ENABLED\nYour wake-up labels will be spoken!"
                else:
                    tts_status = "\n\nText-to-Speech: UNAVAILABLE\nInstall espeak-ng and ffmpeg to enable spoken wake-up messages."
            
            ctx.reply(
                "Wake-Up Call Bot Commands:\n\n"
                "identity <address>\n"
                "  Set your RNS identity address for receiving voice calls\n"
                "  Example: identity 63711db779086bc3e45656e25a125a07\n\n"
                "timezone <timezone>\n"
                "  Set your timezone\n"
                "  Example: timezone America/New_York\n\n"
                "wakeup <time> [label]\n"
                "  Schedule a wake-up call\n"
                "  Example: wakeup 07:00 Morning alarm\n"
                "  Example: wakeup tomorrow 06:30 Meeting\n\n"
                "list\n"
                "  List your scheduled wake-up calls\n\n"
                "cancel <number>\n"
                "  Cancel a wake-up call\n"
                "  Example: cancel 1\n\n"
                f"Note: You must set your identity address before scheduling calls!{tts_status}"
            )
    
    def _get_user_settings(self, user_hash):
        """Get user settings from storage.
        
        Args:
            user_hash: User's identity hash
            
        Returns:
            dict: User settings
        """
        all_settings = self.bot.storage.get("user_settings", {})
        return all_settings.get(user_hash, {"timezone": "UTC"})
    
    def _save_user_settings(self, user_hash, settings):
        """Save user settings to storage.
        
        Args:
            user_hash: User's identity hash
            settings: Settings dictionary to save
        """
        all_settings = self.bot.storage.get("user_settings", {})
        all_settings[user_hash] = settings
        self.bot.storage.set("user_settings", all_settings)
    
    def _get_user_timezone(self, user_hash):
        """Get user's configured timezone.
        
        Args:
            user_hash: User's identity hash
            
        Returns:
            str: Timezone string
        """
        settings = self._get_user_settings(user_hash)
        return settings.get("timezone", "UTC")
    
    def _parse_wakeup_time(self, time_str, prefix_args, timezone):
        """Parse wake-up time string into datetime.
        
        Args:
            time_str: Time string to parse
            prefix_args: Additional arguments that might contain day specifiers
            timezone: User's timezone
            
        Returns:
            datetime: Parsed datetime in user's timezone
            
        Raises:
            ValueError: If time format is invalid
        """
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        
        day_offset = 0
        actual_time_str = time_str
        
        if time_str.lower() == "tomorrow":
            day_offset = 1
            if prefix_args:
                actual_time_str = prefix_args[0]
            else:
                raise ValueError("Time required after 'tomorrow'")
        elif time_str.lower() == "today":
            day_offset = 0
            if prefix_args:
                actual_time_str = prefix_args[0]
            else:
                raise ValueError("Time required after 'today'")
        elif re.match(r'\+(\d+)d', time_str.lower()):
            match = re.match(r'\+(\d+)d', time_str.lower())
            day_offset = int(match.group(1))
            if prefix_args:
                actual_time_str = prefix_args[0]
            else:
                raise ValueError("Time required after day offset")
        
        time_match = re.match(r'(\d{1,2}):(\d{2})', actual_time_str)
        if not time_match:
            raise ValueError("Use HH:MM format (24-hour)")
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        
        if hour < 0 or hour > 23:
            raise ValueError("Hour must be 0-23")
        if minute < 0 or minute > 59:
            raise ValueError("Minute must be 0-59")
        
        target_date = now.date() + timedelta(days=day_offset)
        wakeup_time = datetime.combine(
            target_date,
            datetime.min.time().replace(hour=hour, minute=minute)
        ).replace(tzinfo=tz)
        
        return wakeup_time
    
    def _format_tts_message(self, label, timezone, wakeup_time):
        """Format a TTS message for wake-up calls.
        
        Args:
            label: User's label for the wake-up call
            timezone: User's timezone string
            wakeup_time: The datetime of the wake-up call
            
        Returns:
            str: Formatted message for TTS
        """
        time_str = wakeup_time.strftime("%I:%M %p")
        
        message = f"Good morning! This is your wake-up call. {label}. "
        message += f"The time is {time_str}. "
        message += "Have a great day!"
        
        return message
    
    def _check_wakeup_calls(self):
        """Check for due wake-up calls and initiate them."""
        if not self.voice_manager:
            return
        
        wakeup_calls = self.bot.storage.get("wakeup_calls", [])
        current_time = time.time()
        
        due_calls = [c for c in wakeup_calls if c["time"] <= current_time]
        remaining = [c for c in wakeup_calls if c["time"] > current_time]
        
        for call in due_calls:
            self._make_wakeup_call(call)
        
        if due_calls:
            self.bot.storage.set("wakeup_calls", remaining)
    
    def _make_wakeup_call(self, call_info):
        """Initiate a wake-up call.
        
        Args:
            call_info: Dictionary containing call information
        """
        user_lxmf_hash = call_info["user"]
        label = call_info["label"]
        timezone = call_info.get("timezone", "UTC")
        
        user_settings = self._get_user_settings(user_lxmf_hash)
        identity_address = user_settings.get("identity_address")
        
        if not identity_address:
            self.bot.logger.error(f"No identity address for user {user_lxmf_hash}")
            self.bot.send(
                user_lxmf_hash,
                f"Wake-up call failed: {label}\n"
                "No identity address on file. Please set it with: identity <address>",
                "Wake-Up Call"
            )
            return
        
        self.bot.logger.info(f"Making wake-up call to {identity_address}: {label}")
        
        self.bot.send(
            user_lxmf_hash,
            f"Wake-up call: {label}\nInitiating voice call to {identity_address}...",
            "Wake-Up Call"
        )
        
        audio_file = None
        temp_tts_file = None
        
        try:
            if self.use_tts and self.tts_available:
                wakeup_time = datetime.fromtimestamp(
                    call_info["time"],
                    ZoneInfo(timezone)
                )
                tts_message = self._format_tts_message(label, timezone, wakeup_time)
                
                temp_tts_file = tempfile.NamedTemporaryFile(
                    suffix=".opus",
                    delete=False
                )
                temp_tts_file.close()
                
                if self._generate_tts_audio(tts_message, temp_tts_file.name):
                    audio_file = temp_tts_file.name
                    self.bot.logger.info(f"Generated TTS audio: {tts_message}")
                else:
                    self.bot.logger.warning("TTS generation failed, using alarm audio")
                    audio_file = self.alarm_audio_path
            else:
                audio_file = self.alarm_audio_path
            
            success = self.voice_manager.call(identity_address, timeout=30)
            
            if success:
                if self.voice_manager.wait_for_call_established(timeout=60):
                    self.bot.logger.info(f"Wake-up call established with {identity_address}")
                    
                    time.sleep(2)
                    
                    if audio_file and os.path.isfile(audio_file):
                        loop_audio = not (self.use_tts and self.tts_available)
                        self.voice_manager.play_audio_file(
                            audio_file,
                            loop=loop_audio
                        )
                        
                        if self.use_tts and self.tts_available:
                            time.sleep(15)
                        else:
                            time.sleep(30)
                    else:
                        time.sleep(30)
                    
                    self.voice_manager.hangup()
                    
                    self.bot.send(
                        user_lxmf_hash,
                        f"Wake-up call completed: {label}",
                        "Wake-Up Call"
                    )
                else:
                    self.bot.logger.warning(f"Wake-up call to {identity_address} was not answered")
                    self.bot.send(
                        user_lxmf_hash,
                        f"Wake-up call not answered: {label}\n"
                        f"Attempted to call {identity_address} but no response.\n"
                        "Please check your device was online and LXST is running.",
                        "Wake-Up Call Failed"
                    )
            else:
                self.bot.logger.error(f"Failed to initiate wake-up call to {identity_address}")
                self.bot.send(
                    user_lxmf_hash,
                    f"Failed to place wake-up call: {label}\n"
                    f"Could not establish connection to {identity_address}.\n"
                    "This may happen if:\n"
                    "- Your device is offline\n"
                    "- LXST telephony service is not running\n"
                    "- Identity address is incorrect\n"
                    "- No network path available",
                    "Wake-Up Call Failed"
                )
        except Exception as e:
            self.bot.logger.error(f"Error during wake-up call: {e}")
            import traceback
            self.bot.logger.error(traceback.format_exc())
            self.bot.send(
                user_lxmf_hash,
                f"Error during wake-up call: {label}\n"
                f"Technical error: {str(e)}\n"
                "Please contact the bot administrator if this persists.",
                "Wake-Up Call Error"
            )
        finally:
            if temp_tts_file and os.path.isfile(temp_tts_file.name):
                try:
                    os.unlink(temp_tts_file.name)
                except Exception as e:
                    self.bot.logger.warning(f"Failed to clean up temp TTS file: {e}")
    
    def run(self):
        """Run the bot."""
        try:
            self.bot.run()
        finally:
            if self.voice_manager:
                self.voice_manager.teardown()


if __name__ == "__main__":
    bot = WakeupCallBot()
    bot.run()

