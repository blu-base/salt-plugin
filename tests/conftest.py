def pytest_addoption(parser):
    parser.addoption(
         '--salt-api-backend',
         action='store',
         default='rest_cherrypy',
         help='which backend to use for salt-api, must be one of rest_cherrypy or rest_tornado',
     )
