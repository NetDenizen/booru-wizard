from urllib.request import Request

DEFAULT_USER_AGENT = "curl/7.72.0"

class HeadRequest(Request):
	def get_method(self):
		return "HEAD"
	def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None):
		super().__init__(url, data, headers, origin_req_host, unverifiable, method)
		self.add_header("User-Agent", DEFAULT_USER_AGENT)
