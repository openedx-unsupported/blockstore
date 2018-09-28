"""
Asynchronous wrapper for Neo4j Python Driver
By Chris Savvopoulos
https://github.com/neo4j/neo4j-python-driver/issues/180#issuecomment-380056816
"""
import asyncio
from concurrent import futures
import time
import traceback
import neo4j
from neo4j.v1 import GraphDatabase, basic_auth
from neo4j.exceptions import SecurityError, ServiceUnavailable

RETRY_WAITS = [0, 1, 4]  # How long to wait after each successive failure.


class Neo4j:
    """Neo4j database API."""

    def __init__(self, config, loop):
        self.config = config
        self.loop = loop
        self.executor = futures.ThreadPoolExecutor(max_workers=30)
        for retry_wait in RETRY_WAITS:
            try:
                self._init_driver()
                break
            except (ConnectionRefusedError, SecurityError, ServiceUnavailable, BrokenPipeError):
                if retry_wait == RETRY_WAITS[-1]:
                    raise
                else:
                    print('WARNING: retrying to Init DB; err:')
                    traceback.print_exc()
                    time.sleep(retry_wait)  # wait for 0, 1, 3... seconds.

    def _init_driver(self):
        auth = basic_auth(self.config['user'], self.config['pass'])
        self.driver = GraphDatabase.driver(self.config['url'], auth=auth)

    async def _afetch_start(self, query, **kwargs):
        """ Internal method to start asynchronously fetching results """
        session = self.driver.session(access_mode=neo4j.v1.READ_ACCESS)

        def run():
            return session.run(query, **kwargs).records()
        return session, await self.loop.run_in_executor(self.executor, run)

    async def _afetch_iterate(self, iterator):
        """ Internal method to asynchronously iterate over results """
        def iterate():
            try:
                return next(iterator)
            except StopIteration:
                return None
        while True:
            res = await self.loop.run_in_executor(self.executor, iterate)
            if res is None:
                return
            else:
                yield dict(res)

    async def afetch(self, query, **kwargs):
        """ Asynchronously fetch the results of the given Neo4j read query """
        for retry_wait in RETRY_WAITS:
            try:
                session, iterator = await self._afetch_start(query, **kwargs)
                break
            except (BrokenPipeError, neo4j.exceptions.ServiceUnavailable):
                if retry_wait == RETRY_WAITS[-1]:
                    raise
                else:
                    await asyncio.sleep(retry_wait)
                    await self.loop.run_in_executor(self.executor, self._init_driver)
        async for x in self._afetch_iterate(iterator):
            yield x

        await self.loop.run_in_executor(self.executor, session.close)

    async def afetch_one(self, query, **kwargs):
        """ Asynchronously fetch one result from the given Neo4j read query """
        async for i in self.afetch(query, **kwargs):
            return i
        return None

    async def aexec(self, query, **kwargs):
        """ Asynchronously run the given Neo4j query, without retrieving its result """
        async for _ in self.afetch(query, **kwargs):
            pass
        return
