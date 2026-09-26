import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.graph.neo4j_client import neo4j_client
from app.config import settings

logger = logging.getLogger(__name__)

embedder = None

def get_embedder():
    global embedder
    if embedder is None:
        logger.info("Loading sentence-transformers model...")
        embedder = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded.")
    return embedder

async def resolve_entities(workspace_id: int):
    """
    Finds and merges duplicate entities in a workspace based on cosine similarity 
    of their names using APOC mergeNodes.
    """
    logger.info(f"Starting entity resolution for workspace {workspace_id}...")
    
    # 1. Fetch all entities in this workspace
    query_fetch = """
    MATCH (e:Entity {workspace_id: $workspace_id})
    RETURN e.id AS name
    """
    records = await neo4j_client.execute_write(query_fetch, {"workspace_id": workspace_id})
    
    if not records or len(records) < 2:
        logger.info("Not enough entities to resolve.")
        return []

    entities = [record["name"] for record in records]
    
    # 2. Generate embeddings
    logger.info(f"Generating embeddings for {len(entities)} entities...")
    emb = get_embedder()
    embeddings = emb.encode(entities)
    
    # 3. Calculate similarity matrix
    similarity_matrix = cosine_similarity(embeddings)
    
    merged_pairs = []
    
    # Keep track of already merged entities to avoid chaining or re-merging
    processed_entities = set()
    
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            name_a = entities[i]
            name_b = entities[j]
            score = float(similarity_matrix[i][j])
            
            # Log the similarity scores for calibration
            logger.info(f"Similarity Score: '{name_a}' vs '{name_b}' = {score:.4f}")
            
            if score >= settings.auto_resolve_confidence_threshold:
                if name_a in processed_entities or name_b in processed_entities:
                    continue
                
                logger.info(f"Threshold met! Merging '{name_b}' into '{name_a}' (score: {score:.4f})")
                
                # Using APOC to merge nodes. We merge B into A.
                # apoc.refactor.mergeNodes takes a list of nodes and merges them into the first node in the list.
                merge_query = """
                MATCH (ea:Entity {id: $name_a, workspace_id: $workspace_id})
                MATCH (eb:Entity {id: $name_b, workspace_id: $workspace_id})
                // Use apoc to merge eb into ea
                CALL apoc.refactor.mergeNodes([ea, eb], {
                    properties: "combine",
                    mergeRels: true
                }) YIELD node
                RETURN node
                """
                
                try:
                    await neo4j_client.execute_write(merge_query, {
                        "workspace_id": workspace_id,
                        "name_a": name_a,
                        "name_b": name_b
                    })
                    merged_pairs.append((name_b, name_a, score))
                    
                    processed_entities.add(name_a)
                    processed_entities.add(name_b)
                except Exception as e:
                    logger.error(f"Failed to merge '{name_b}' into '{name_a}': {e}")
                    
            elif score >= 0.75:
                # Borderline candidate for manual review
                logger.info(f"Merge Candidate found: '{name_a}' and '{name_b}' (score: {score:.4f})")
                candidate_query = """
                CREATE (mc:MergeCandidate {
                    workspace_id: $workspace_id,
                    entity_a: $name_a,
                    entity_b: $name_b,
                    score: $score,
                    status: 'PENDING'
                })
                """
                try:
                    await neo4j_client.execute_write(candidate_query, {
                        "workspace_id": workspace_id,
                        "name_a": name_a,
                        "name_b": name_b,
                        "score": score
                    })
                except Exception as e:
                    logger.error(f"Failed to create MergeCandidate for '{name_a}' and '{name_b}': {e}")

    logger.info(f"Entity resolution complete. Merged {len(merged_pairs)} pairs.")
    return merged_pairs
