import logging
from app.graph.neo4j_client import neo4j_client
from app.llm.extractor import ExtractionSchema

logger = logging.getLogger(__name__)

async def write_extraction_to_graph(
    extraction: ExtractionSchema, 
    workspace_id: int, 
    document_id: int, 
    filename: str
):
    """
    Writes the extracted entities and facts into Neo4j.
    Implements the subject-relation-object triple model.
    """
    if not extraction.entities and not extraction.facts:
        logger.info(f"No entities or facts to write for document {document_id}")
        return

    # 1. Ensure the Document node exists in Neo4j
    doc_query = """
    MERGE (d:Document {id: $document_id})
    ON CREATE SET d.workspace_id = $workspace_id, d.filename = $filename
    """
    await neo4j_client.execute_write(
        doc_query, 
        {"document_id": document_id, "workspace_id": workspace_id, "filename": filename}
    )

    # 2. Write Entities
    # We prefix the entity ID with the document ID to keep local references unique to the document,
    # unless we want cross-document entity linking out of the box. 
    # For now, we will use the exact name as the deduplication key across the workspace.
    entity_query = """
    UNWIND $entities AS ent
    MERGE (e:Entity {id: ent.name, workspace_id: $workspace_id})
    ON CREATE SET e.type = ent.type, e.name = ent.name
    """
    # Create a mapping from the LLM's local ID (e.g. "e1") to the global name for linking facts later
    local_id_to_name = {ent.id: ent.name for ent in extraction.entities}
    
    entities_data = [{"name": e.name, "type": e.type} for e in extraction.entities]
    if entities_data:
        await neo4j_client.execute_write(
            entity_query,
            {"entities": entities_data, "workspace_id": workspace_id}
        )

    # 3. Write Facts (Subject-Relation-Object Model)
    fact_query = """
    UNWIND $facts AS f
    MATCH (sub:Entity {id: f.source_name, workspace_id: $workspace_id})
    MATCH (obj:Entity {id: f.target_name, workspace_id: $workspace_id})
    MATCH (doc:Document {id: $document_id})
    
    // Create the Fact node
    CREATE (fact:Fact {
        id: randomUUID(),
        workspace_id: $workspace_id,
        relation: f.relation,
        valid_from: f.valid_from,
        valid_to: f.valid_to,
        evidence: f.evidence
    })
    
    // Create edges
    CREATE (fact)-[:SUBJECT]->(sub)
    CREATE (fact)-[:OBJECT]->(obj)
    CREATE (fact)-[:SOURCED_FROM]->(doc)
    """
    
    facts_data = []
    for fact in extraction.facts:
        # Resolve the local ID to the actual entity name
        source_name = local_id_to_name.get(fact.source)
        target_name = local_id_to_name.get(fact.target)
        
        if source_name and target_name:
            facts_data.append({
                "source_name": source_name,
                "target_name": target_name,
                "relation": fact.relation,
                "valid_from": fact.valid_from,
                "valid_to": fact.valid_to,
                "evidence": fact.evidence
            })
            
    if facts_data:
        await neo4j_client.execute_write(
            fact_query,
            {"facts": facts_data, "workspace_id": workspace_id, "document_id": document_id}
        )
        logger.info(f"Wrote {len(entities_data)} entities and {len(facts_data)} facts to Neo4j.")
