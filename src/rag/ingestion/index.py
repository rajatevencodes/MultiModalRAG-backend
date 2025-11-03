from src.services.supabase import supabase
import os
from src.services.awsS3 import s3_client
from src.config.index import appConfig
from src.rag.ingestion.utils import partition_document
from src.models.index import ProcessingStatus


def process_document(document_id: str):
    """
    * Step 1 : Download from S3 (file) or Crawl the URL (url) and Extract text, tables, and images from the PDF (using Unstructured Library) from the AWS S3 document.
    * Step 2 : Split the extracted content into chunks.
    * Step 3 : Generate AI summaries for each chunk.
    * Step 4 : Create vector embeddings (1536 dimensions per chunk).
    * Step 5 : Store everything in PostgreSQL.
    * Update the project document record with the processing_status and processing_details as needed.
    *   - `processing_details` : What type of elements or metadata did we retrieve from the document to show in the UI.
    """

    try:
        update_status_in_database(document_id, ProcessingStatus.PROCESSING)

        document_result = (
            supabase.table("project_documents")
            .select("*")
            .eq("id", document_id)
            .execute()
        )
        if not document_result.data:
            raise Exception(
                f"Failed to get project document record with id: {document_id}"
            )
        document = document_result.data[0]

        # Step 1 : Download from S3 (file) or Crawl the URL (url) and Extract content.
        update_status_in_database(document_id, ProcessingStatus.PARTITIONING)
        elements_retrieved = download_content_and_partition(document_id, document)

        # Step 2 : Split the extracted content into chunks.
        # Step 3 : Generate AI summaries for each chunk.
        # Step 4 : Create vector embeddings (1536 dimensions per chunk).
        # Step 5 : Store everything in PostgreSQL.

        update_status_in_database(document_id, ProcessingStatus.COMPLETED)

        return {
            "success": True,
            "document_id": document_id,
        }
    except Exception as e:
        raise Exception(f"Failed to process document {document_id}: {str(e)}")


def update_status_in_database(
    document_id: str, status: ProcessingStatus, details: dict = None
):
    """
    Update the project document record with the new status and details.
    """
    try:
        # Get the project document record
        document_result = (
            supabase.table("project_documents")
            .select("*")
            .eq("id", document_id)
            .execute()
        )
        if not document_result.data:
            raise Exception(
                f"Failed to get project document record with id: {document_id}"
            )
        # Add processing details to the project document record if there are any
        current_details = {}
        if document_result.data[0]["processing_details"]:
            current_details = document_result.data[0]["processing_details"]

        # Add new details if provided
        if details:
            current_details.update(
                details
            )  # Note : update() - built-in dict method that merges another dictionary into the current one.

        # Update the project document record with the new details
        document_update_result = (
            supabase.table("project_documents")
            .update(
                {"processing_status": status, "processing_details": current_details}
            )
            .eq("id", document_id)
            .execute()
        )

        if not document_update_result.data:
            raise Exception(
                f"Failed to update project document record with id: {document_id}"
            )

    except Exception as e:
        raise Exception(f"Failed to update status in database: {str(e)}")


def download_content_and_partition(document_id: str, document: dict):
    """
    Content either a file or a url.
    if :  Document - Download from S3
    else : URL - Crawl the URL
    Partition into elements like text, tables, images, etc. and analyze the elements summary and upload to db.
    """
    try:
        # Get the project document record
        document_source_type = document["source_type"]
        elements = None
        if document_source_type == "file":
            # Download the file from S3
            s3_key = document["s3_key"]
            filename = document["filename"]
            file_type = filename.split(".")[-1].lower()

            # Download the file to a temporary directory - for all OS - Linux , Windows , Mac
            temp_file_path = f"/tmp/{document_id}.{file_type}"
            s3_client.download_file(appConfig["s3_bucket_name"], s3_key, temp_file_path)

            elements = partition_document(temp_file_path, file_type)

        if document_source_type == "url":
            # TODO :Crawl the url
            return None

        # Delete the temprary file
        os.remove(temp_file_path)

        return elements

    except Exception as e:
        raise Exception(
            f"Failed in Step 1 to download content and partition elements: {str(e)}"
        )
