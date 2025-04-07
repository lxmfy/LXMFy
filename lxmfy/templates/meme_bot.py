import requests

from lxmfy import Attachment, AttachmentType, LXMFBot, command
from lxmfy.events import Event, EventPriority

MEME_API_URL = "https://memeapi.zachl.tech/pic/json"

class MemeBot:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode

        self.bot = LXMFBot(
            name="Meme Bot",
            command_prefix="/",
            storage_type="json",
            storage_path="data/meme_bot",
            announce=600,
            announce_immediately=False,
            first_message_enabled=False
        )
        self.bot.command(name="meme", description="Sends a random meme picture")(self.send_meme)

    def fetch_random_meme(self) -> tuple[str | None, str | None, str | None]:
        """Fetches a random meme picture URL from the zachl.tech API."""

        try:
            response = requests.get(MEME_API_URL, timeout=15)
            response.raise_for_status()
            data = response.json()

            meme_url = data.get("MemeURL")
            meme_title = "Here's your meme!"

            if not meme_url:
                if self.debug_mode:
                    print(f"[DEBUG] No meme URL found in API response: {data}")
                return None, "API did not return a meme URL.", None

            # Extract file extension from URL, ignoring query parameters
            url_path = meme_url.split('?')[0]
            file_extension = url_path.split('.')[-1].lower() if '.' in url_path else None

            # Validate common image types
            if file_extension not in ["jpg", "jpeg", "png", "gif"]:
                if self.debug_mode:
                    print(f"[DEBUG] Unsupported meme format or invalid URL path: {file_extension} from {url_path}")
                return None, f"Unsupported format ({file_extension}) or invalid URL.", None

            if self.debug_mode:
                print(f"[DEBUG] Fetched meme URL: {meme_url} (extension: {file_extension})")
            return meme_url, meme_title, file_extension

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error fetching meme from API: {http_err}")
            return None, f"HTTP error: {response.status_code}", None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching meme from API: {e}")
            return None, f"Network error: {e}", None
        except Exception as e:
            print(f"Error processing meme API response: {e}")
            return None, f"Processing error: {e}", None

    def fetch_image_data(self, url: str) -> bytes | None:
        """Fetches image data from a URL."""
        try:
            headers = {'User-Agent': 'LXMFy-MemeBot/1.0'}
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '').lower()
            if 'image' in content_type:
                if self.debug_mode:
                    print(f"[DEBUG] Successfully downloaded image from {url}")
                return response.content
            else:
                if self.debug_mode:
                    print(f"[DEBUG] Content downloaded from {url} might not be an image. Content-Type: {content_type}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching image data from {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching image data: {e}")
            return None

    def send_meme(self, ctx):
        """Callback function for the /meme command."""
        sender = ctx.sender

        try:
            meme_url, result_message, meme_format = self.fetch_random_meme()

            if meme_url and meme_format:
                image_data = self.fetch_image_data(meme_url)

                if image_data:
                    if self.debug_mode:
                         print(f"[DEBUG] Meme image data fetched successfully ({len(image_data)} bytes). Preparing attachment...")
                    try:
                        attachment = Attachment(
                            type=AttachmentType.IMAGE,
                            name=f"meme.{meme_format}",
                            data=image_data,
                            format=meme_format
                        )
                        if self.debug_mode:
                             print("[DEBUG] Attachment object prepared. Sending...")

                        self.bot.send_with_attachment(
                            destination=sender,
                            message=result_message,
                            attachment=attachment,
                            title="Your Meme Delivery!"
                        )
                        if self.debug_mode:
                            print("[DEBUG] Meme sent successfully with attachment.")

                    except Exception as e:
                        if self.debug_mode:
                            print(f"[DEBUG] Error creating/sending Attachment: {e}")
                        ctx.reply(f"Sorry, I couldn't prepare the meme image. Error: {e}")
                else:
                    if self.debug_mode:
                        print("[DEBUG] Failed to fetch meme image data.")
                    ctx.reply(f"Sorry, I found a meme URL but couldn't download the image from {meme_url}.")
            else:
                error_msg = result_message or "Sorry, I couldn't fetch a meme right now."
                if self.debug_mode:
                    print(f"[DEBUG] Failed to fetch meme URL or determine format. Reason: {error_msg}")
                ctx.reply(error_msg)

        except Exception as e:
            print(f"Error in send_meme command: {e}")
            ctx.reply("An unexpected error occurred while fetching a meme.")

    def run(self):
        print("Starting Meme Bot...")
        self.bot.run()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run the LXMF Meme Bot.')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable detailed logging.'
    )
    args = parser.parse_args()

    meme_bot = MemeBot(debug_mode=args.debug)
    meme_bot.run()