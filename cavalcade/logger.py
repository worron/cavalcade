import sys
import types
from itertools import chain
import logging

# The background is set with 40 plus the number of the color, and the foreground with 30
CI = dict(zip(("BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE"), range(8)))
COLORS = {'WARNING': CI["YELLOW"], 'INFO': CI["GREEN"], 'DEBUG': CI["BLUE"], 'CRITICAL': CI["RED"], 'ERROR': CI["RED"]}

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[0;%dm"
BOLD_SEQ = "\033[1m"

COLOR_PACK = list(('$' + color, COLOR_SEQ % (30 + CI[color])) for color in CI.keys())

MESSAGE_PATTERN = (
	"$COLOR$BOLD%(levelname)s: $RESET$COLOR%(asctime)s %(filename)s:%(funcName)s():L%(lineno)d "
	"$RESET%(message)s"
)

FUNCTION_PATTERN = "$COLOR$BOLD%(levelname)s: $RESET$COLOR%(asctime)s $RESET%(message)s"

_tabbing = 0
_tab = ">>"


class ColoredFormatter(logging.Formatter):
	"""Colored log output formatter"""
	def format(self, record):
		level_color = COLOR_SEQ % (30 + COLORS[record.levelname])
		message = super().format(record)
		for rep in [('$RESET', RESET_SEQ), ('$BOLD', BOLD_SEQ), ('$COLOR', level_color)] + COLOR_PACK:
			message = message.replace(*rep)
		return message + RESET_SEQ


logger = logging.getLogger(__name__)
color_formatter = ColoredFormatter(MESSAGE_PATTERN)
function_formatter = ColoredFormatter(FUNCTION_PATTERN)

stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(color_formatter)
logger.addHandler(stream_handler)


def is_debug(inst):
	return inst.getEffectiveLevel() == logging.DEBUG

# noinspection PyArgumentList
logger.is_debug = types.MethodType(is_debug, logger)


def debuginfo(input_log=True, output_log=True):
	"""Decorator to log function details.
	:param input_log: show function arguments
	:param output_log: show function result
	:return: function wrapped for logging
	"""
	def real_decorator(fn):
		if logger.getEffectiveLevel() > logging.DEBUG:
			return fn

		def wrapped(*args, **kwargs):
			global _tabbing
			name = fn.__qualname__.split('.')[-1]
			filename = fn.__code__.co_filename.split('/')[-1]
			lineno = fn.__code__.co_firstlineno
			params = ", ".join(map(repr, chain(args, kwargs.values())))

			# print function name
			stream_handler.setFormatter(function_formatter)
			logger.debug(
				"$BOLD$CYAN%s%s %s:$MAGENTA%s$CYAN:L%s",
				_tab * _tabbing, "FUNCTION", filename, name, lineno
			)

			# print function arguments
			if input_log:
				logger.debug(
					"$BOLD$CYAN%s%s $MAGENTA%s$CYAN: $RESET%s",
					_tab * _tabbing, "INPUT", name, params
				)
			stream_handler.setFormatter(color_formatter)

			# run original function
			_tabbing += 1
			returned_value = fn(*args, **kwargs)
			_tabbing -= 1

			# print function result
			stream_handler.setFormatter(function_formatter)
			if output_log:
				logger.debug(
					"$BOLD$CYAN%s%s $MAGENTA%s$CYAN: $RESET%s",
					_tab * _tabbing, "OUTPUT", name, repr(returned_value)
				)
			logger.debug("$BOLD$CYAN%s%s $MAGENTA%s", _tab * _tabbing, "FINISHED", name)
			stream_handler.setFormatter(color_formatter)

			return returned_value

		return wrapped
	return real_decorator
