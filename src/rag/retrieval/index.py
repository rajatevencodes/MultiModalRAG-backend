from src.services.llm import openAI
from fastapi import HTTPException
from src.services.supabase import supabase
from src.rag.retrieval.utils import (
    get_project_settings,
    get_project_document_ids,
    build_context_from_retrieved_chunks,
    validate_context_from_retrieved_chunks,
    prepare_prompt_and_invoke_llm,
)


def retrieve_context(project_id, user_query):
    try:
        """
        * Step 1: get user's project settings from the database.
        * Step 2: Retrieve the document IDs for the current project.
        * Step 3: Generate embeddings for the user query.
        * Step 4: Perform a vector search using the RPC function to find the most relevant chunks.
        * Step 5: Build the context from the retrieved chunks and format them into a structured context with citations.
        """
        # Step 1 : get user's project settings from the database.
        project_settings = get_project_settings(project_id)

        # Step 2: Retrieve the document IDs for the current project.
        document_ids = get_project_document_ids(project_id)
        # print("Found document IDs: ", len(document_ids))

        # Step 3 : Generate embeddings for the user query.
        user_query_embedding = openAI["embeddings"].embed_documents([user_query])[0]
        # print("User query embedding: ", user_query_embedding)

        # Step 4 : Perform a vector search using the RPC function to find the most relevant chunks.
        vector_search_result_chunks = supabase.rpc(
            "vector_search_document_chunks",
            {
                "query_embedding": user_query_embedding,
                "filter_document_ids": document_ids,
                "match_threshold": project_settings["similarity_threshold"],
                # "chunks_per_search": project_settings["chunks_per_search"],
                "chunks_per_search": 2,  # ! TODO : Reduced for testing
            },
        ).execute()
        print(
            f"Vector search resulted in: {len(vector_search_result_chunks.data)} chunks"
        )

        # Step 5: Build the context from the retrieved chunks and format them into a structured context with citations.
        texts, images, tables, citations = build_context_from_retrieved_chunks(
            vector_search_result_chunks.data
        )
        # validate_context_from_retrieved_chunks(texts, images, tables, citations)

        return texts, images, tables, citations
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed in RAG's Retrieval: {str(e)}"
        )
