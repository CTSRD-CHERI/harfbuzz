#!/usr/bin/env python3

import sys, os, subprocess, tempfile, shutil


def cmd (command):
	# https://stackoverflow.com/a/4408409 as we might have huge output sometimes
	with tempfile.TemporaryFile () as tempf:
		p = subprocess.Popen (command, stderr=tempf)

		try:
			p.wait (timeout=int (os.environ.get ("HB_TEST_SHAPE_FUZZER_TIMEOUT", "2")))
			tempf.seek (0)
			text = tempf.read ()

			#TODO: Detect debug mode with a better way
			is_debug_mode = b"SANITIZE" in text

			return ("" if is_debug_mode else text.decode ("utf-8").strip ()), p.returncode
		except subprocess.TimeoutExpired:
			return 'error: timeout, ' + ' '.join (command), 1


srcdir = os.environ.get ("srcdir", ".")
EXEEXT = os.environ.get ("EXEEXT", "")
top_builddir = os.environ.get ("top_builddir", ".")
hb_shape_fuzzer = os.path.join (top_builddir, "hb-shape-fuzzer" + EXEEXT)

if not os.path.exists (hb_shape_fuzzer):
	if len (sys.argv) == 1 or not os.path.exists (sys.argv[1]):
		print ("""Failed to find hb-shape-fuzzer binary automatically,
please provide it as the first argument to the tool""")
		sys.exit (1)

	hb_shape_fuzzer = sys.argv[1]

print ('hb_shape_fuzzer:', hb_shape_fuzzer)
fails = 0

libtool = os.environ.get ('LIBTOOL')
valgrind = None
if os.environ.get ('RUN_VALGRIND', ''):
	valgrind = shutil.which ('valgrind')
	if valgrind is None:
		print ("""Valgrind requested but not found.""")
		sys.exit (1)
	if libtool is None:
		print ("""Valgrind support is currently autotools only and needs libtool but not found.""")


parent_path = os.path.join (srcdir, "fonts")
for file in os.listdir (parent_path):
	path = os.path.join (parent_path, file)

	if valgrind:
		text, returncode = cmd (libtool.split(' ') + ['--mode=execute', valgrind + ' --leak-check=full --error-exitcode=1', '--', hb_shape_fuzzer, path])
	else:
		text, returncode = cmd ([hb_shape_fuzzer, path])
		if 'error' in text:
			returncode = 1

	if (not valgrind or returncode) and text.strip ():
		print (text)

	if returncode != 0:
		print ('failure on %s' % file)
		fails = fails + 1


if fails:
	print ("%i shape fuzzer related tests failed." % fails)
	sys.exit (1)
