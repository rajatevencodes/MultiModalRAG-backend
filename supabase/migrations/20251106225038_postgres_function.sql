----------------------------------------------------------
--- vector_search_document_chunks function ---
-- Start with all rows in `document_chunks`.
-- Keep only rows whose `document_id` is in the `filter_document_ids` array.
-- Drop rows that have no embedding.
-- Compute cosine distance between each remaining `dc.embedding` and the `query_embedding`, convert to similarity (`1 - distance`) and keep only those with similarity ≥ `match_threshold`.
-- Sort the survivors by distance (most similar first).
-- Return the top `chunks_per_search` rows.
----------------------------------------------------------
CREATE OR REPLACE FUNCTION vector_search_document_chunks(
    query_embedding vector, 
    filter_document_ids uuid[], 
    match_threshold double precision DEFAULT 0.3, 
    chunks_per_search integer DEFAULT 20
)
RETURNS TABLE(
    id uuid, 
    document_id uuid, 
    content text, 
    chunk_index integer, 
    created_at timestamp with time zone, 
    page_number integer, 
    char_count integer, 
    type jsonb, 
    original_content jsonb, 
    embedding vector
)
LANGUAGE sql
AS $function$
SELECT
    dc.id,
    dc.document_id,
    dc.content,
    dc.chunk_index,
    dc.created_at,
    dc.page_number,
    dc.char_count,
    dc.type,
    dc.original_content,
    dc.embedding
FROM
    document_chunks dc
WHERE
    dc.document_id = ANY(filter_document_ids)
    AND dc.embedding IS NOT NULL
    AND (1 - (dc.embedding <=> query_embedding)) > match_threshold  
ORDER BY 
    dc.embedding <=> query_embedding ASC  
LIMIT 
    chunks_per_search;
$function$;


----------------------------------------------------------
--- keyword_search_document_chunks function ---
-- 
----------------------------------------------------------
CREATE OR REPLACE FUNCTION keyword_search_document_chunks(
    query_text text, 
    filter_document_ids uuid[], 
    chunks_per_search integer DEFAULT 20
) 
RETURNS TABLE(
    id uuid, 
    document_id uuid, 
    content text, 
    chunk_index integer, 
    created_at timestamp with time zone, 
    page_number integer, 
    char_count integer, 
    type jsonb, 
    original_content jsonb, 
    embedding vector
)
LANGUAGE sql
AS $function$
SELECT
    dc.id,
    dc.document_id,
    dc.content,
    dc.chunk_index,
    dc.created_at, 
    dc.page_number,
    dc.char_count,
    dc.type,
    dc.original_content,
    dc.embedding
FROM
    document_chunks dc
WHERE
    dc.fts @@ websearch_to_tsquery('english', query_text)
    AND dc.document_id = ANY(filter_document_ids)
ORDER BY 
    ts_rank_cd(dc.fts, websearch_to_tsquery('english', query_text)) DESC 
LIMIT 
    chunks_per_search; 
$function$;