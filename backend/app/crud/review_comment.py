# DB access functions for DocumentReviewComment.

import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.review_comment import DocumentReviewComment


def create_review_comment(
    db: Session, *, document_id: uuid.UUID, reviewed_by: uuid.UUID, comment_text: str
) -> DocumentReviewComment:
    comment = DocumentReviewComment(document_id=document_id, reviewed_by=reviewed_by, comment_text=comment_text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_review_comments(db: Session, *, document_id: uuid.UUID) -> list[DocumentReviewComment]:
    return (
        db.query(DocumentReviewComment)
        .options(joinedload(DocumentReviewComment.reviewed_by_user))
        .filter(DocumentReviewComment.document_id == document_id)
        .order_by(DocumentReviewComment.created_at)
        .all()
    )
