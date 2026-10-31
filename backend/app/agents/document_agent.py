"""
Agent 2: Document Intelligence Agent.
Extracts structured canonical fields with evidence provenance from commercial PDFs.
Uses PyMuPDF with honest OCR fallback.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.database.models import Document, DocumentExtraction
from app.orchestration.state import WorkflowState
from app.services.field_extractor import FieldExtractor
from app.services.pdf_extractor import PDFExtractor, PDFExtractionError


class DocumentIntelligenceAgent:
    """Specialist agent responsible for commercial document extraction and provenance."""

    AGENT_NAME = "DocumentIntelligenceAgent"

    @classmethod
    def execute(cls, state: WorkflowState, db: Session) -> WorkflowState:
        """Processes all documents in state.document_ids."""
        start_time = datetime.now(timezone.utc).isoformat()
        logs = list(state.agent_execution_log)
        extracted_docs = dict(state.extracted_documents)
        extraction_errors = list(state.extraction_errors)

        for doc_id in state.document_ids:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                extraction_errors.append({"document_id": doc_id, "error": f"Document ID '{doc_id}' not found in database."})
                continue

            file_path = Path(doc.file_path)
            if not file_path.exists():
                extraction_errors.append({"document_id": doc_id, "error": f"Physical file '{doc.file_path}' is missing."})
                continue

            try:
                # 1. Page by page text extraction
                extraction_result = PDFExtractor.extract_document(file_path)
                pages = extraction_result["pages"]

                # 2. Extract canonical commercial fields
                canonical = FieldExtractor.extract_fields(
                    document_id=doc.id,
                    filename=doc.original_filename,
                    pages=pages,
                    document_type_hint=doc.document_type if doc.document_type != "unknown" else None,
                )

                # Update document record
                doc.document_type = canonical.document_type
                doc.status = "EXTRACTED"
                db.commit()

                # Save into state
                extracted_docs[doc.id] = canonical.model_dump()

            except PDFExtractionError as e:
                extraction_errors.append({"document_id": doc_id, "error": str(e)})
            except Exception as e:
                extraction_errors.append({"document_id": doc_id, "error": f"Extraction error: {str(e)}"})

        # Update execution log
        action_desc = f"Extracted {len(extracted_docs)} document(s)"
        status = "SUCCESS" if not extraction_errors else "PARTIAL_FAILURE"
        logs.append({
            "agent_name": cls.AGENT_NAME,
            "action": action_desc,
            "status": status,
            "details": {
                "extracted_count": len(extracted_docs),
                "error_count": len(extraction_errors),
                "errors": extraction_errors,
            },
            "timestamp": start_time,
        })

        if extraction_errors:
            state.retry_count += 1
            state.requires_human_review = True

        state.extracted_documents = extracted_docs
        state.extraction_errors = extraction_errors
        state.agent_execution_log = logs

        return state
