import os

from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


class Settings:
    DATA_PATH: str = os.getenv("DATA_PATH", "data")
    LUX_SOP_FILENAME: str = "lux_sop_updated.xlsx"

    @property
    def lux_sop_filepath(self):
        return os.path.join(self.DATA_PATH, "sops", "luxottica", self.LUX_SOP_FILENAME)


settings = Settings()
