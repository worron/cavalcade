# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
from logging import getLogger, StreamHandler, Formatter

# The background is set with 40 plus the number of the color, and the foreground with 30
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
COLORS = {'WARNING': YELLOW, 'INFO': GREEN, 'DEBUG': BLUE, 'CRITICAL': RED, 'ERROR': RED}

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[0;%dm"
BOLD_SEQ = "\033[1m"

MESSAGE_PATTERN = (
	"$COLOR$BOLD%(levelname)s: $RESET$COLOR%(asctime)s %(filename)s:%(funcName)s():L%(lineno)d "
	"$RESET%(message)s"
)


class ColoredFormatter(Formatter):
	"""Colored log output formatter"""
	def format(self, record):
		color = COLOR_SEQ % (30 + COLORS[record.levelname])
		message = super().format(record)
		for rep in (('$RESET', RESET_SEQ), ('$BOLD', BOLD_SEQ), ('$COLOR', color)):
			message = message.replace(*rep)
		return message + RESET_SEQ


logger = getLogger(__name__)

stream_handler = StreamHandler()
color_formatter = ColoredFormatter(MESSAGE_PATTERN)
stream_handler.setFormatter(color_formatter)
logger.addHandler(stream_handler)
