
from langgraph.checkpoint.redis import RedisSaver

from app.config.settings import REDIS_URL


memory = RedisSaver(redis_url=REDIS_URL)
memory.setup()

