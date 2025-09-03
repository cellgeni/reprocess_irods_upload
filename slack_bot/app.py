import os
import argparse
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load env variables
load_dotenv("/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/slack_bot/.env")

# parser
parser = argparse.ArgumentParser(description="Process arguments.")
parser.add_argument("--file", required=True, help="Path to status file.")


# Slack Bot Token
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = os.getenv(
    "CHANNEL_ID"
)  # Replace with the channel ID where you want to send the message


def reformat_status(status: str, total_number: int, used: str, quote: str) -> str:
    if status == "No datasets found in the list":
        formated_status = f"✅*PASS:* 0\n❌*FAIL:* 0\n:among_us_hammer:*PROCESSED:* 0\n:bird_run:*LEFT:* {total_number - 1}"
    else:
        status = status.split(",")
        status = {
            x.split(":")[0].strip(" "): x.split(":")[1].strip(" ") for x in status
        }
        left = total_number - int(status["ALL"]) - 1
        formated_status = f"✅*PASS:* {status['PASS']}\n❌*FAIL:* {status['FAIL']}\n:among_us_hammer:*PROCESSED:* {status['ALL']}\n:bird_run:*LEFT:* {left}\n:writing_hand:*MEM:* {used}/{quote}"
    return formated_status


def read_results(file: str) -> str:
    with open(file, "r") as file:
        status = file.readline().rstrip()
        total_number = int(file.readline().split(" ")[0])
        used, quote = file.readline().rstrip().split(" ")
    return reformat_status(status, total_number, used, quote)


def send_daily_message(status_file: str):
    client = WebClient(token=SLACK_BOT_TOKEN)
    status = read_results(status_file)
    try:
        response = client.chat_postMessage(
            channel=CHANNEL_ID, text=f"Hello! Current Reprocessing Status 🚀\n{status}"
        )
        print(f"Message sent: {response['message']['text']}")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")


if __name__ == "__main__":
    args = parser.parse_args()
    send_daily_message(args.file)
