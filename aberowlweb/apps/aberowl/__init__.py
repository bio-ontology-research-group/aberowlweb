import redis

redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
