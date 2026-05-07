from scrapy_redis import defaults
from scrapy_redis.connection import get_redis_from_settings
from scrapy_redis.dupefilter import RFPDupeFilter

from bloomguolvq.redis_bloom import RedisBloomFilter


class RedisBloomDupeFilter(RFPDupeFilter):
    def __init__(self, server, key, debug=False, size=10000000, num_hashes=7):
        self.server = server
        self.key = key
        self.debug = debug
        self.logdupes = True
        self.bloom = RedisBloomFilter(
            server=server,
            key=key,
            size=size,
            num_hashes=num_hashes,
        )

    @classmethod
    def from_settings(cls, settings):
        server = get_redis_from_settings(settings)
        key = settings.get("BLOOMFILTER_KEY", "dupefilter:bloom")
        debug = settings.getbool("DUPEFILTER_DEBUG")
        size = settings.getint("BLOOMFILTER_SIZE", 10000000)
        num_hashes = settings.getint("BLOOMFILTER_HASHES", 7)
        return cls(
            server=server,
            key=key,
            debug=debug,
            size=size,
            num_hashes=num_hashes,
        )

    @classmethod
    def from_spider(cls, spider):
        settings = spider.settings
        server = get_redis_from_settings(settings)
        dupefilter_key = settings.get(
            "SCHEDULER_DUPEFILTER_KEY", defaults.SCHEDULER_DUPEFILTER_KEY
        )
        key = settings.get("BLOOMFILTER_KEY") or dupefilter_key % {
            "spider": spider.name
        }
        debug = settings.getbool("DUPEFILTER_DEBUG")
        size = settings.getint("BLOOMFILTER_SIZE", 10000000)
        num_hashes = settings.getint("BLOOMFILTER_HASHES", 7)
        return cls(
            server=server,
            key=key,
            debug=debug,
            size=size,
            num_hashes=num_hashes,
        )

    def request_seen(self, request):
        fp = self.request_fingerprint(request)
        is_new = self.bloom.check(fp)
        return not is_new

    def clear(self):
        self.bloom.clear()
