# Review comment endpoints — add/list comments against a document version.

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.review_comment import create_review_comment, list_review_comments
from app.deps import get_current_user, get_db, require_document_access
from app.models.user import User
from app.schemas.review_comment import ReviewCommentCreate, ReviewCommentRead

router = APIRouter()


@router.get("/documents/{document_id}/comments", response_model=list[ReviewCommentRead])
def get_comments(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_document_access),
) -> list[ReviewCommentRead]:
    return list_review_comments(db, document_id=document_id)


@router.post("/documents/{document_id}/comments", response_model=ReviewCommentRead)
def post_comment(
    document_id: uuid.UUID,
    payload: ReviewCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_document_access),
) -> ReviewCommentRead:
    # Matches the frontend's own restriction (composer hidden for developers) —
    # enforced here too since a UI hint alone isn't a real boundary.
    if current_user.persona != "auditor":
        raise HTTPException(status_code=403, detail="Only auditors can add review comments")
    return create_review_comment(db, document_id=document_id, reviewed_by=current_user.id, comment_text=payload.comment_text)
