from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Dict, Type, TypeVar, Union

from loguru import logger
from pydantic import BaseModel
from redis.asyncio import Redis

T = TypeVar("T", bound=BaseModel)


class CustomRedis(Redis):
    """Extended Redis class with additional methods."""

    async def delete_key(self, key: str) -> None:
        """Delete key from Redis."""
        await self.delete(key)
        logger.info(f"Key {key} deleted")

    async def delete_keys_by_prefix(self, prefix: str) -> None:
        """Delete keys starting with prefix."""
        keys = await self.keys(prefix + '*')
        if keys:
            await self.delete(*keys)
            logger.info(f"Deleted keys starting with {prefix}")

    async def delete_all_keys(self) -> None:
        """Delete all keys from current database."""
        await self.flushdb()
        logger.info("Deleted all keys from current Redis database")

    async def get_value(self, key: str) -> str | None:
        """Get value from Redis."""
        value = await self.get(key)
        if value:
            return value
        logger.info(f"Key {key} not found")
        return None

    async def set_value(self, key: str, value: str) -> None:
        """Set value in Redis."""
        await self.set(key, value)
        logger.info(f"Set value for key {key}")

    async def set_value_with_ttl(self, key: str, value: str, ttl: int = 3600) -> None:
        """Set value with TTL in Redis."""
        await self.setex(key, ttl, value)

    async def get_cached_data(
        self,
        cache_key: str,
        fetch_data_func: Callable[..., Awaitable[Any]],
        model: Type[T],
        *args,
        ttl: int = 3600,
        **kwargs
    ) -> Any:
        """Get data from cache or fetch from source if not cached."""
        cached_data = await self.get(cache_key)

        if cached_data:
            logger.info(f"Data retrieved from cache for key: {cache_key}")
            try:
                # logger.info("Loading data from Redis")
                data = json.loads(cached_data)

                if isinstance(data, list):
                    return [model.model_validate(item) for item in data]
                else:
                    return model.model_validate(data)

            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.error(f"Error deserializing cached data: {e}")
                await self.delete_key(cache_key)

        logger.info(f"Data not found in cache for key: {cache_key}, fetching from source")
        try:
            data = await fetch_data_func(*args, **kwargs)
            if data is None:
                logger.info("Data not found in source")
                return None

            if isinstance(data, list):
                processed_data = [
                    item.model_dump() if hasattr(item, 'model_dump') else item
                    for item in data
                ]
                # models = [model(**item) for item in processed_data]
                models = data # Assuming fetch_data_func returns models
                await self.set_value_with_ttl(key=cache_key, ttl=ttl, value=json.dumps(processed_data))
                logger.info(f"List data saved to cache for key: {cache_key} with TTL: {ttl}s")
                return models

            else:
                processed_data = data.model_dump() if hasattr(data, 'model_dump') else data
                # model_instance = model(**processed_data)
                model_instance = data # Assuming fetch_data_func returns model
                await self.set_value_with_ttl(key=cache_key, ttl=ttl, value=json.dumps(processed_data))
                logger.info(f"Data saved to cache for key: {cache_key} with TTL: {ttl}s")
                return model_instance

        except Exception as e:
            logger.error(f"Error fetching data or creating Pydantic model: {e}")
            return None

    @staticmethod
    def convert_redis_data(data: Dict[str, str]) -> Dict[str, Union[str, int, float]]:
        """Convert Redis data (strings) to Python types."""
        converted_data = {}
        for key, value in data.items():
            if isinstance(key, bytes):
                key = key.decode()
            if isinstance(value, bytes):
                value = value.decode()

            try:
                converted_data[key] = int(value)
            except ValueError:
                try:
                    converted_data[key] = float(value)
                except ValueError:
                    converted_data[key] = value
        return converted_data


class RedisClient:
    """Redis connection manager."""

    def __init__(self, url: str, socket_timeout: int = 20):
        self.url = url
        self.socket_timeout = socket_timeout
        self._client: CustomRedis | None = None

    async def connect(self) -> None:
        """Create and store Redis connection."""
        if self._client is None:
            try:
                self._client = CustomRedis.from_url(
                    url=self.url, 
                    socket_timeout=self.socket_timeout,
                    decode_responses=True # Important for string operations
                )
                await self._client.ping()
                logger.info("Redis connected successfully")
            except Exception as e:
                logger.error(f"Redis connection error: {e}")
                raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis connection closed")

    def get_client(self) -> CustomRedis:
        """Get Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis client not initialized")
        return self._client

    async def __aenter__(self) -> RedisClient:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
