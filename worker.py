import os
import urlparse
from redis import Redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

#redis_url = os.getenv('redistogo-spherical-73382','redis://redistogo:897d4c29fb07e5d500bb38d2c26c64f1@crestfish.redistogo.com:9158/')
url = urlparse.urlparse(os.environ.get('redistogo-spherical-73382','redis://redistogo:897d4c29fb07e5d500bb38d2c26c64f1@crestfish.redistogo.com:9158/'))
conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)
if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
