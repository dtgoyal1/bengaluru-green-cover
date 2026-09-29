"""Serve `site/` locally, with the HTTP range requests PMTiles needs.

Python's own `http.server` ignores the Range header, and a PMTiles file read
without it downloads whole on every tile. Usage, from the repo root:

	python site/serve.py            # http://localhost:8765
"""

import os
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = Path(__file__).resolve().parent
RANGE = re.compile(r"bytes=(\d*)-(\d*)")


class RangeHandler(SimpleHTTPRequestHandler):
	def end_headers(self):
		self.send_header("Cache-Control", "no-store")
		super().end_headers()

	def send_head(self):
		match = RANGE.fullmatch(self.headers.get("Range", ""))
		path = Path(self.translate_path(self.path))
		if not match or not path.is_file():
			return super().send_head()
		size = path.stat().st_size
		start = int(match[1]) if match[1] else max(0, size - int(match[2]))
		end = min(int(match[2]), size - 1) if match[1] and match[2] else size - 1
		if start > end:
			self.send_error(416)
			return None
		f = path.open("rb")
		f.seek(start)
		self.send_response(206)
		self.send_header("Content-Type", self.guess_type(str(path)))
		self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
		self.send_header("Content-Length", str(end - start + 1))
		self.send_header("Accept-Ranges", "bytes")
		self.end_headers()
		self.remaining = end - start + 1
		return f

	def copyfile(self, source, outputfile):
		remaining = getattr(self, "remaining", None)
		if remaining is None:
			return super().copyfile(source, outputfile)
		while remaining > 0:
			chunk = source.read(min(65536, remaining))
			if not chunk:
				break
			outputfile.write(chunk)
			remaining -= len(chunk)
		self.remaining = None


if __name__ == "__main__":
	os.chdir(ROOT)
	print(f"serving {ROOT} at http://localhost:{PORT}")
	ThreadingHTTPServer(("", PORT), partial(RangeHandler, directory=str(ROOT))).serve_forever()
