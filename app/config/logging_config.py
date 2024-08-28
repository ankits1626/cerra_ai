import logging
import os
from logging.handlers import TimedRotatingFileHandler

from pythonjsonlogger import jsonlogger

from app.config.settings import settings


def setup_logging():
    # Create logs directory if not exists
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Define the log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(funcName)s:%(lineno)d]"

    # Determine log level based on environment
    if settings.ENVIRONMENT == "development":
        log_level = logging.DEBUG
        console_level = logging.DEBUG
    else:
        log_level = logging.ERROR
        console_level = logging.ERROR

    # Create handlers
    file_handler = TimedRotatingFileHandler(
        "logs/app.log", when="midnight", backupCount=7
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(log_level)

    json_handler = TimedRotatingFileHandler(
        "logs/app_json.log", when="midnight", backupCount=7
    )
    json_handler.setFormatter(jsonlogger.JsonFormatter())
    json_handler.setLevel(log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format))
    stream_handler.setLevel(console_level)

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(json_handler)
    logger.addHandler(stream_handler)

    # Add a placeholder for CloudWatch integration
    if settings.ENVIRONMENT == "production" and settings.OCR_AWS_REGION_NAME:
        try:
            import watchtower

            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group="your-log-group"
            )
            cloudwatch_handler.setLevel(log_level)
            logger.addHandler(cloudwatch_handler)
        except ImportError:
            logger.warning(
                "Watchtower is not installed. CloudWatch logging is not configured."
            )

    return logger
