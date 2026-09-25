import logging
from app.graph.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

CONSTRAINTS = [
    "CREATE CONSTRAINT entity_id_workspace IF NOT EXISTS FOR (e:Entity) REQUIRE (e.id, e.workspace_id) IS UNIQUE;",
    "CREATE CONSTRAINT fact_id IF NOT EXISTS FOR (f:Fact) REQUIRE f.id IS UNIQUE;",
    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;",
    "CREATE CONSTRAINT workspace_id IF NOT EXISTS FOR (w:Workspace) REQUIRE w.id IS UNIQUE;"
]

INDEXES = [
    "CREATE INDEX entity_workspace IF NOT EXISTS FOR (e:Entity) ON (e.workspace_id);",
    "CREATE INDEX fact_workspace IF NOT EXISTS FOR (f:Fact) ON (f.workspace_id);",
    "CREATE INDEX fact_validity IF NOT EXISTS FOR (f:Fact) ON (f.valid_from, f.valid_to);"
]

async def apply_schema():
    """Run all constraints and indexes during startup"""
    try:
        async with neo4j_client.driver.session() as session:
            for query in CONSTRAINTS + INDEXES:
                await session.run(query)
                logger.info(f"Executed Neo4j query: {query}")
        logger.info("Neo4j schema constraints and indexes applied successfully.")
    except Exception as e:
        logger.error(f"Failed to apply Neo4j schema: {e}")
        raise
