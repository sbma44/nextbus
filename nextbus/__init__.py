import scrapelib
import time
import re
import json

class Nextbus(object):
	"""Tracks Nextbus arrival times"""
	def __init__(self, routes):
		super(Nextbus, self).__init__()
		self.scraper = scrapelib.Scraper(requests_per_minute=10)

		self.api_key = self.get_api_key()

		self.routes = routes
		self.predictions = {}
		self.last_refresh = {}		
		for r in self.routes:
			self.predictions[r] = None
			self.last_refresh[r] = 0
			self.refresh(r)		
	
	def _clean_prediction_html(self, html):
		return re.sub(r'&nbsp;','', re.sub(r'<[^>]*>','',(str(html)), flags=re.MULTILINE|re.DOTALL)).strip()

	def get_api_key(self):
		re_api = re.compile(r'<p id=\'api_key\' class=\'hide\'>\?key=([abcdef0123456789]+)')
		html = self.scraper.urlopen('http://www.nextbus.com')
		matches = re_api.search(html)
		if matches is None:
			raise Exception("Could not find Nextbus key")
		return matches.group(1)

	def _extract_predictions(self, data):
		predictions = []
		for p in data[0]['values']:
			predictions.append(p['minutes'])
		return predictions

	def refresh(self, route):
		"""Force a refresh of a specific route"""
		route = str(route)

		url = self.routes.get(route, False)
		if not url:
			return
		if callable(url):
			url = url()
		url = "%s&key=%s&timestamp=%d" % (url, self.api_key, int(time.time() * 1000))

		attempts = 0
		json_response = '[]'
		while attempts < 3 and json_response == '[]':
			try:
				self.scraper.headers['Referer'] = 'http://www.nextbus.com/'
				json_response = self.scraper.urlopen(url)
			except scrapelib.HTTPError, e:
				print 'got http error: %s' % str(e)
				if e.response.code == 401:
					self.api_key = self.get_api_key()
				attempts += 1
			except Exception, e:
				raise e

		data = json.loads(json_response)
		self.predictions[route] = self._extract_predictions(data)
		self.last_refresh[route] = time.time()

	def _get_query_frequency(self, last_prediction_in_minutes):
		if last_prediction_in_minutes>20:
			return (last_prediction_in_minutes / 2) * 60
		elif last_prediction_in_minutes>10:
			return 3 * 60
		elif last_prediction_in_minutes>5:
			return 2 * 60
		else:
			return 60

	def refresh_all(self):
		for r in self.routes:
			self.refresh(r)

	def refresh_if_necessary(self):
		"""Only refresh prediction times intermittently -- don't hammer"""
		for r in self.routes:
			if self.predictions[r] is None:
				if (time.time() - self.last_refresh[r]) > TIMEOUT:
					self.refresh(r)
			else:
				# if we have a prediction, refresh if we're halfway or more to
				# the expected arrival time
				if (time.time() - self.last_refresh[r]) > self._get_query_frequency(self.predictions[r][0]):
					self.refresh(r)
	
	def _adjust_prediction_for_elapsed_time(self, prediction, r):
		return round(prediction - round((time.time() - self.last_refresh[r]) / 60.0))

	def get_closest_arrival(self):
		return self.get_nth_closest_arrival(0)

	def get_nth_closest_arrival(self, n=0, route=None):
		"""Return the (route, arrival) pair that's happening soonest"""
		arrivals = []
		for r in self.routes:			
			if self.predictions.get(r) is not None:			
				for p in self.predictions.get(r, []):
					valid_route = route is None
					valid_route = valid_route or ((type(route) in (tuple, list)) and (r in route))
					valid_route = valid_route or route==r
					if valid_route:
						arrivals.append( (p, r) )

		if n>=len(arrivals):
			return None

		matching_arrival = sorted(arrivals, key=lambda x: x[0])[n]
		return (matching_arrival[1], self._adjust_prediction_for_elapsed_time(matching_arrival[0], matching_arrival[1]))


if __name__ == '__main__':
	main()
