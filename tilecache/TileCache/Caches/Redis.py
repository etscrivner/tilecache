# BSD Licensed, Copyright (c) 2006-2010 TileCache Contributors

from TileCache.Cache import Cache
import time


class Redis(Cache):
    """Redis-based caching mechanism"""

    def __init__(self, host, port, expiration=0, **kwargs):
        """Initialize redis"""
        Cache.__init__(self, **kwargs)
        import redis
        self.cache = redis.StrictRedis(host=host, port=port, db=0)
        self.expiration = int(expiration)

    def getKey(self, tile):
        """Construct the cache key for the given tile.

        :param tile: A tile
        :type tile: TileCache.Layer.Tile
        :rtype: str or unicode
        """
        return ":".join(map(str, [tile.layer.name, tile.x, tile.y, tile.z]))

    def getLockName(self, tile):
        """Construct the lock name for the given tile.

        :param tile: A tile
        :type tile: TileCache.Layer.Tile
        :rtype: str or unicode
        """
        return self.getKey(tile) + ":lock"

    def get(self, tile):
        """Retrieve the cached data for the given tile.

        :param tile: A tile
        :type tile: TileCache.Layer.Tile
        :rtype: str or unicode
        """
        key = self.getKey(tile)
        tile.data = self.cache.get(key)
        return tile.data

    def set(self, tile, data):
        """Cache data for the given tile.

        :param tile: A tile
        :type tile: TileCache.Layer.Tile
        :rtype: str or unicode
        """
        if self.readonly:
            return data
        key = self.getKey(tile)
        self.cache.setex(key, data, self.expiration)
        return data

    def delete(self, tile):
        """Delete the cached data for the given tile.

        :param tile: A tile
        :type tile: TileCache.Layer.Tile
        """
        key = self.getKey(tile)
        self.cache.delete(key)

    def attemptLock(self, tile):
        """Attempt to acquire a lock for the given tile.

        :param tile: A tile
        :type tile: TileCache.Layer.Tile
        :rtype: bool
        """
        result = self.cache.setnx(
            self.getLockName(tile),
            time.time() + self.timeout + 1
        )

        # Expire the lock so it can't become stuck permanently
        if result:
            self.cache.expire(
                self.getLockName(tile),
                self.timeout() + 1
            )

        return result

    def unlock(self, tile):
        """Unlock the given tile

        :param tile: A tile
        :type tile: TileCache.Layer.Tile
        """
        self.cache.delete(self.getLockName(tile))
