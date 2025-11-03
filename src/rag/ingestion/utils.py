from unstructured.partition.html import partition_html
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.text import partition_text
from unstructured.partition.md import partition_md


def partition_document(temp_file: str, file_type: str, source_type: str = "file"):
    """Partition document based on file type and source type"""

    source = (source_type or "file").lower()
    if source == "url":
        return partition_html(filename=temp_file)

    kind = (file_type or "").lower()
    dispatch = {
        "pdf": lambda: partition_pdf(
            filename=temp_file,
            strategy="hi_res",
            infer_table_structure=True,
            extract_image_block_types=["Image"],
            extract_image_block_to_payload=True,
        ),
        "docx": lambda: partition_docx(
            filename=temp_file,
            strategy="hi_res",
            infer_table_structure=True,
        ),
        "pptx": lambda: partition_pptx(
            filename=temp_file,
            strategy="hi_res",
            infer_table_structure=True,
        ),
        "txt": lambda: partition_text(filename=temp_file),
        "md": lambda: partition_md(filename=temp_file),
    }

    if kind not in dispatch:
        raise ValueError(f"Unsupported file_type: {file_type}")

    return dispatch[kind]()
