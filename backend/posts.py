from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Post, User

router = APIRouter()

# ----------------------------
# CREATE POST
# ----------------------------
@router.post("/posts")
def create_post(data: dict, db: Session = Depends(get_db)):

    content = data.get("content")
    user_id = data.get("user_id")

    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID missing")

    post = Post(
        content=content,
        user_id=user_id,
        created_at=datetime.utcnow()
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return {
        "message": "Post created successfully",
        "post_id": post.id
    }


# ----------------------------
# GET ALL POSTS
# ----------------------------
@router.get("/posts")
def get_posts(db: Session = Depends(get_db)):

    posts = (
        db.query(Post, User)
        .join(User, Post.user_id == User.id)
        .order_by(Post.id.desc())
        .all()
    )

    result = []

    for post, user in posts:
        result.append({
            "id": post.id,
            "content": post.content,
            "created_at": post.created_at,
            "user": {
                "id": user.id,
                "fullname": user.fullname,
                "email": user.email
            }
        })

    return result