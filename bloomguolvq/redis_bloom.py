import mmh3


class RedisBloomFilter:
    def __init__(self, server, key, size, num_hashes):
        self.server = server
        self.key = key
        self.size = size
        self.num_hashes = num_hashes
        self._check_script = self.server.register_script(
            """
            local exists = 1
            for i = 1, #ARGV do
                if redis.call('GETBIT', KEYS[1], ARGV[i]) == 0 then
                    exists = 0
                end
            end
            for i = 1, #ARGV do
                redis.call('SETBIT', KEYS[1], ARGV[i], 1)
            end
            return exists
            """
        )

    def _getHash(self, item, seed):
        return mmh3.hash(item, seed, signed=False) % self.size

    def _get_num_hashes_hash(self, item):
        hash_return = []
        for i in range(self.num_hashes):
            hash_return.append(self._getHash(item, i))
        return hash_return

    def check(self, item):
        hash_list = self._get_num_hashes_hash(item)
        exists = self._check_script(keys=[self.key], args=hash_list)
        return not bool(exists)

    def clear(self):
        self.server.delete(self.key)
