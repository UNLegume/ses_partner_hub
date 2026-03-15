from dotenv import load_dotenv
import os

load_dotenv()

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SHEET1_GID = os.getenv("SHEET1_GID", "0")
WORK_SHEET_GID = os.getenv("WORK_SHEET_GID", "")
COUNT_SHEET_GID = os.getenv("COUNT_SHEET_GID", "")
SEARCH_DELAY_MIN = int(os.getenv("SEARCH_DELAY_MIN", "3"))
SEARCH_DELAY_MAX = int(os.getenv("SEARCH_DELAY_MAX", "5"))
