import os

import redis


REDIS_KEY = "qq_hot_rank:start_urls"
START_URL = "https://book.qq.com/book-rank"


def main():
    host = os.getenv("REDIS_HOST", "127.0.0.1")
    port = int(os.getenv("REDIS_PORT", "6379"))
    client = redis.Redis(host=host, port=port, db=0)
    client.lpush(REDIS_KEY, START_URL)
    print(f"Pushed {START_URL} to Redis list {REDIS_KEY} at {host}:{port}")


if __name__ == "__main__":
    main()
