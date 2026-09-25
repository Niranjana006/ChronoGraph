from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import settings

class Neo4jClient:
    def __init__(self):
        self.driver: AsyncDriver | None = None

    async def connect(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        await self.driver.verify_connectivity()

    async def close(self):
        if self.driver:
            await self.driver.close()
            
    async def execute_write(self, query: str, parameters: dict = None):
        if not self.driver:
            await self.connect()
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

neo4j_client = Neo4jClient()

async def get_neo4j_session():
    async with neo4j_client.driver.session() as session:
        yield session
