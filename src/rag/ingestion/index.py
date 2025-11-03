from src.services.supabase import supabase
import time
import os


def process_document(document_id: str):
    """
    * Step 1 : Extract text, tables, and images from the PDF (using Unstructured Library) from the AWS S3 document.
    * Step 2 : Split the extracted content into chunks.
    * Step 3 : Generate AI summaries for each chunk.
    * Step 4 : Create vector embeddings (1536 dimensions per chunk).
    * Step 5 : Store everything in PostgreSQL.
    * Update the project document record with the processing_status on every step.
    """

    try:
        # Updating processing_status to "processing"
        document_update_result = (
            supabase.table("project_documents")
            .update({"processing_status": "processing"})
            .eq("id", document_id)
            .execute()
        )
        if not document_update_result.data:
            raise Exception(
                "Failed to update project document record with processing_status"
            )
        # Step 1 : Extract text from the document (using Unstructured Library)
        time.sleep(10)  # TODO : Remove this after testing

        # Updating processing_status to "completed"
        document_update_result = (
            supabase.table("project_documents")
            .update({"processing_status": "completed"})
            .eq("id", document_id)
            .execute()
        )
        if not document_update_result.data:
            raise Exception(
                "Failed to update project document record with processing_status"
            )

        return {
            "success": True,
            "document_id": document_id,
        }
    except Exception as e:
        raise Exception(f"Failed to extract text from the document: {str(e)}")
