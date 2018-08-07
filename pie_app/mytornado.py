import mytornadosettings
import time
import tornado.web
import tornado.httpserver

from treadmill import treadmill

treadmill = treadmill()

class Application(tornado.web.Application):
	def __init__(self, treadmill):
		self.treadmill = treadmill
		settings = {
			"template_path": mytornadosettings.TEMPLATE_PATH,
			"static_path": mytornadosettings.STATIC_PATH,
		}
		handlers = [
			(r"/", MainHandler),
			(r'/templates/(.*)', tornado.web.StaticFileHandler, {'path': settings['template_path']}),
			(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': settings['static_path']}),
			(r"/status", StatusHandler),
			(r"/api/action/(.*)", ActionHandler),
			(r"/api/lastimage", LastImageHandler)
		]
		tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
	def get(self):
		#self.write("index.html")
		with open(self.settings['template_path'] + "/index.html", 'r') as file:
			self.write(file.read())	 

#MAX_WORKERS = 4

from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor   # `pip install futures` for python2
#from tornado import gen

"""
class StatusHandler(tornado.web.RequestHandler):
	#@tornado.gen.coroutine
	@tornado.web.asynchronous
	def get(self):
		ret = treadmill.getStatus()
		self.write(treadmill.getStatus())
		self.finish()
		
		#ret = treadmill.getStatus()
		#raise gen.Return(ret)
"""

class StatusHandler(tornado.web.RequestHandler):
	def get(self):
		ret = treadmill.getStatus()
		self.write(ret)

	'''
	executor = ThreadPoolExecutor(5)
 
	@tornado.gen.coroutine
	def get(self):
		ret = yield self.get_complex_result()
		self.write(ret)
 
	#@tornado.concurrent.run_on_executor
	@run_on_executor
	def get_complex_result(self):
		#print('Before Sleep.')
		ret = treadmill.getStatus()
		#time.sleep(1)
		#print('   After Sleep.')
		return ret	   # Assume the final result is 100
	'''
				
	'''
	executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

	@run_on_executor
	def background_task(self):
		""" This will be executed in `executor` pool. """
		return treadmill.getStatus()

	@tornado.gen.coroutine
	def get(self):
		""" Request that asynchronously calls background task. """
		res = yield self.background_task()
		self.write(res)
	'''
			
class ActionHandler(tornado.web.RequestHandler):
	def get(self, thisAction):
		print('ActionHandler:', thisAction)
		if thisAction == 'startRecord':
			treadmill.startRecord()
		if thisAction == 'stopRecord':
			treadmill.stopRecord()

		if thisAction == 'startStream':
			treadmill.startStream()
		if thisAction == 'stopStream':
			treadmill.stopStream()

		if thisAction == 'startArm':
			treadmill.startArm()
		if thisAction == 'stopArm':
			treadmill.stopArm()

		if thisAction == 'startArmVideo':
			treadmill.startArmVideo()
		if thisAction == 'stopArmVideo':
			treadmill.stopArmVideo()

		self.write(treadmill.getStatus())

class LastImageHandler(tornado.web.RequestHandler):
	def get(self):
		self.write('')
		
def main():
	print('tornado port: 9999')
	applicaton = Application(treadmill)
	http_server = tornado.httpserver.HTTPServer(applicaton)
	http_server.listen(9999)

	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()