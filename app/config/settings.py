import os

from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATA_PATH: str = os.getenv("DATA_PATH", "data")
    LUX_SOP_FILENAME: str = "lux_sop_updated.xlsx"

    @property
    def lux_sop_filepath(self):
        return os.path.join(self.DATA_PATH, "sops", "luxottica", self.LUX_SOP_FILENAME)

    # Database configurations
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv(
        "DB_HOST"
    )  # 'db' refers to the service name in Docker Compose
    DB_PORT: str = os.getenv("DB_PORT")
    DB_NAME: str = os.getenv("DB_NAME")

    @property
    def DATABASE_URL(self):
        retval = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        # print(f"<<<<<<< DATABASE_URL = {retval}")
        return retval

    # AWS
    OCR_AWS_REGION_NAME: str = os.getenv("OCR_AWS_REGION_NAME")
    OCR_AWS_ACCESS_KEY_ID: str = os.getenv("OCR_AWS_ACCESS_KEY_ID")
    OCR_AWS_SECRET_ACCESS_KEY: str = os.getenv("OCR_AWS_SECRET_ACCESS_KEY")

    # classifier
    @property
    def RECEIPT_CLASSIFIER_PATH(self):
        return os.path.join("app", "models", "receipt_classifier_312.h5")


settings = Settings()
