import { Link } from "react-router-dom";
import TagChip from "../common/TagChip.jsx";
import { postDate } from "../../lib/postDate.js";

export default function PostItem({ post }) {
  return (
    <Link className="post-item" to={`/community/${post.id}`}>
      {post.festival && <TagChip>{post.festival.title}</TagChip>}
      <h3>{post.title}</h3>
      <p className="post-preview">{post.content}</p>
      <div className="post-meta">
        <span>{post.author.nickname}</span>
        <span>{postDate(post.created_at)}</span>
        <span>조회 {post.view_count}</span>
        <span>댓글 {post.comment_count}</span>
      </div>
    </Link>
  );
}
