import os
import subprocess

_FALLBACK_VERSION = "0.8"
# _DEVELOPMENT_BRANCH = "devel"
_MASTER_BRANCH = "master"


def get_current():
	"""Try to find current version of package using git output"""
	version = _FALLBACK_VERSION
	try:
		cwd_ = os.path.dirname(os.path.abspath(__file__))

		output = subprocess.check_output(["git", "describe", "--tags", "--long"], stderr=subprocess.PIPE, cwd=cwd_)
		describe = str(output, "utf-8").strip()
		output = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.PIPE, cwd=cwd_)
		branch = str(output, "utf-8").strip()

		v, n, commit = describe.split('-')

		if branch == _MASTER_BRANCH or n == "0":
			# TODO: does it possible to proper count commit on master branch?
			version = v
		else:
			# Just assuming we are working on next version
			# if git branch is different from master
			next_version = float(v) + 0.1
			version = "%.1f.dev%s+%s" % (next_version, n, commit)
	except Exception as e:
		# use plain print instead of logger to avoid potential error on setup
		print("Can't read git output:\n%s", e)

	return version
