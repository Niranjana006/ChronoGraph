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

neo4j_client = Neo4jClient()

async def get_neo4j_session():
    async with neo4j_client.driver.session() as session:
        yield session
