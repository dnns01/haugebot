import os

import redis


class VoteRedis(redis.Redis):
    def __init__(self):
        self.host = os.getenv("REDIS_HOST")
        self.port = os.getenv("REDIS_PORT")
        self.db = os.getenv("REDIS_DB")
        self.password = os.getenv("REDIS_PW")
        super().__init__(host=self.host, port=self.port, db=self.db, password=self.password)

        try:
            self.ping()
            print('Redis: Connected!')
            self.is_connected = True
            self.init_db()
        except Exception:
            print('A connection to the Redis server could not be established. Redis querys are avoided.')
            self.is_connected = False

    def init_db(self):
        # update constants in Redis-DB
        self.set('voteMin', os.getenv("VOTE_MIN_VOTES"))
        self.set('voteDelayEnd', os.getenv("VOTE_DELAY_END"))
        self.set('voteDelayInter', os.getenv("VOTE_DELAY_INTERIM"))
        #
        # reset DB
        p = self.pipeline()  # start transaction
        p.set('plus', 0)
        p.set('neutral', 0)
        p.set('minus', 0)
        p.execute()  # transaction end
