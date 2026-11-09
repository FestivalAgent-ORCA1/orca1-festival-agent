from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.post import Comment, Post
from app.models.user import User
from app.schemas.post import AuthorResponse, CommentResponse, PostResponse


def _author_of(db: Session, user_id: int) -> AuthorResponse:
    user = db.get(User, user_id)
    nickname = user.nickname if user else "(탈퇴한 사용자)"
    return AuthorResponse(id=user_id, nickname=nickname)


def to_post_response(db: Session, post: Post, viewer: User | None, preview: bool = False) -> PostResponse:
    comment_count = db.scalar(select(func.count()).select_from(Comment).where(Comment.post_id == post.id))
    content = post.content[:100] if preview else post.content   # 목록에서는 앞 100자만 (api-spec)
    return PostResponse(
        id=post.id, title=post.title, content=content,
        author=_author_of(db, post.user_id),
        festival=None,   # TODO(BE1 연동): festival_content_id로 {content_id, title} 채우기
        view_count=post.view_count, comment_count=comment_count,
        is_mine=(viewer is not None and viewer.id == post.user_id),
        created_at=post.created_at, updated_at=post.updated_at,
    )


def list_posts(db: Session, viewer: User | None, page: int, size: int,
               festival_content_id: str | None) -> tuple[list, int]:
    query = select(Post)
    if festival_content_id:
        query = query.where(Post.festival_content_id == festival_content_id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    posts = db.scalars(
        query.order_by(Post.created_at.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return [to_post_response(db, p, viewer, preview=True) for p in posts], total


def create_post(db: Session, user: User, title: str, content: str,
                festival_content_id: str | None) -> Post:
    post = Post(user_id=user.id, title=title, content=content,
                festival_content_id=festival_content_id, view_count=0)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_post(db: Session, post_id: int, count_view: bool = True) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise AppError(404, "POST_NOT_FOUND", "게시글을 찾을 수 없어요.")
    if count_view:
        post.view_count += 1   # 상세 조회 시 조회수 +1 (api-spec)
        db.commit()
        db.refresh(post)
    return post


def update_post(db: Session, user: User, post_id: int, title: str, content: str,
                festival_content_id: str | None) -> Post:
    post = get_post(db, post_id, count_view=False)
    if post.user_id != user.id:
        raise AppError(403, "FORBIDDEN", "본인이 쓴 글만 수정할 수 있어요.")
    post.title = title
    post.content = content
    post.festival_content_id = festival_content_id
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, user: User, post_id: int) -> None:
    post = get_post(db, post_id, count_view=False)
    if post.user_id != user.id:
        raise AppError(403, "FORBIDDEN", "본인이 쓴 글만 삭제할 수 있어요.")
    db.delete(post)   # 댓글은 ON DELETE CASCADE로 함께 삭제
    db.commit()


def list_comments(db: Session, viewer: User | None, post_id: int) -> list[CommentResponse]:
    get_post(db, post_id, count_view=False)   # 글이 없으면 404
    comments = db.scalars(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc())  # 오래된 순
    ).all()
    return [
        CommentResponse(
            id=c.id, content=c.content, author=_author_of(db, c.user_id),
            is_mine=(viewer is not None and viewer.id == c.user_id),
            created_at=c.created_at,
        )
        for c in comments
    ]


def create_comment(db: Session, user: User, post_id: int, content: str) -> Comment:
    get_post(db, post_id, count_view=False)   # 글이 없으면 404
    comment = Comment(post_id=post_id, user_id=user.id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, user: User, comment_id: int) -> None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise AppError(404, "COMMENT_NOT_FOUND", "댓글을 찾을 수 없어요.")
    if comment.user_id != user.id:
        raise AppError(403, "FORBIDDEN", "본인이 쓴 댓글만 삭제할 수 있어요.")
    db.delete(comment)
    db.commit()