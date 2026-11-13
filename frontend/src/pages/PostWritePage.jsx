import { useCallback, useState } from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { repository } from "../api/repository.js";
import { useAuth } from "../contexts/AuthContext.jsx";
import { useResource } from "../hooks/useResource.js";
import PostEditor from "../components/community/PostEditor.jsx";
import Loading from "../components/common/Loading.jsx";
import ErrorState from "../components/common/ErrorState.jsx";

// /community/write (새 글) 와 /community/:id/edit (수정) 를 함께 맡습니다.
export default function PostWritePage() {
  const { id } = useParams();
  const { status } = useAuth();
  const location = useLocation();
  if (status === "loading") return <Loading text="로그인 정보를 확인하고 있어요." />;
  if (status !== "authenticated")
    return (
      <Navigate
        to={`/login?redirect=${encodeURIComponent(location.pathname + location.search)}`}
        replace
      />
    );
  return id ? <EditPost id={id} /> : <NewPost />;
}

function NewPost() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [festivalId, setFestivalId] = useState(params.get("festival") || "");
  const loadFestival = useCallback(
    (signal) => repository.getDetail(festivalId, signal),
    [festivalId],
  );
  const festival = useResource(loadFestival, Boolean(festivalId));
  return (
    <WriteLayout title="축제 이야기 남기기">
      <PostEditor
        festival={
          festivalId && {
            title:
              festival.data?.title ||
              (festival.status === "loading" ? "불러오는 중…" : festivalId),
          }
        }
        onRemoveFestival={() => setFestivalId("")}
        submitLabel="올리기"
        onSubmit={async (body) => {
          const created = await repository.createPost({
            ...body,
            festival_content_id: festivalId || null,
          });
          navigate(`/community/${created.id}`, { replace: true });
        }}
      />
    </WriteLayout>
  );
}

function EditPost({ id }) {
  const navigate = useNavigate();
  const passed = useLocation().state?.post;
  const loadPost = useCallback(
    (signal) => repository.getPost(id, signal),
    [id],
  );
  // 상세 화면에서 넘어오면 글을 다시 불러오지 않습니다.
  const fetched = useResource(loadPost, !passed);
  const post = passed || fetched.data;
  const [festival, setFestival] = useState(undefined);
  if (!post && fetched.status === "loading")
    return <Loading text="글을 불러오고 있어요." />;
  if (!post)
    return (
      <WriteLayout title="글 수정">
        <ErrorState error={fetched.error} onRetry={fetched.retry} />
      </WriteLayout>
    );
  if (!post.is_mine)
    return (
      <WriteLayout title="글 수정">
        <p className="community-filter">
          내가 쓴 글만 수정할 수 있어요.{" "}
          <Link to={`/community/${id}`}>글로 돌아가기</Link>
        </p>
      </WriteLayout>
    );
  const linked = festival === undefined ? post.festival : festival;
  return (
    <WriteLayout title="글 수정">
      <PostEditor
        initial={{ title: post.title, content: post.content }}
        festival={linked}
        onRemoveFestival={() => setFestival(null)}
        submitLabel="수정 완료"
        onSubmit={async (body) => {
          await repository.updatePost(id, {
            ...body,
            festival_content_id: linked?.content_id || null,
          });
          navigate(`/community/${id}`, { replace: true });
        }}
      />
    </WriteLayout>
  );
}

function WriteLayout({ title, children }) {
  return (
    <section className="wrap auth-page">
      <div className="auth-card wide">
        <div className="page-intro">
          <span className="eyebrow">WEEKEND TALK</span>
          <h1 className="display">{title}</h1>
          <p>축제의 팁, 후기, 함께 가고 싶은 이야기를 자유롭게 적어주세요.</p>
        </div>
        {children}
      </div>
    </section>
  );
}
