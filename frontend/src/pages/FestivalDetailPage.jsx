import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { repository } from "../api/repository.js";
import { useResource } from "../hooks/useResource.js";
import DetailContent from "../components/festival/DetailContent.jsx";
import FestivalCard from "../components/festival/FestivalCard.jsx";
import FestivalPreview from "../components/festival/FestivalPreview.jsx";
import Loading from "../components/common/Loading.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import Button from "../components/common/Button.jsx";
export default function FestivalDetailPage() {
  const { contentId } = useParams();
  const [previewId, setPreviewId] = useState(null);
  const resource = useResource(
    useCallback(
      (signal) => repository.getDetail(contentId, signal),
      [contentId],
    ),
  );
  const similar = useResource(
    useCallback(
      (signal) => repository.getSimilar(contentId, signal),
      [contentId],
    ),
  );
  useEffect(() => {
    if (resource.data) document.title = `${resource.data.title} — ORCA`;
    return () => {
      document.title = "ORCA — 주말의 입장권";
    };
  }, [resource.data]);
  return (
    <section className="wrap detail-page">
      <Link className="back-link" to="/festivals">
        ← 축제 목록으로
      </Link>
      {resource.status === "loading" && <Loading />}
      {resource.status === "error" &&
        (resource.error.status === 404 ? (
          <EmptyState title="이 축제를 찾을 수 없어요.">
            <Button as={Link} to="/festivals" variant="white">
              다른 축제 구경하기
            </Button>
          </EmptyState>
        ) : (
          <ErrorState error={resource.error} onRetry={resource.retry} />
        ))}
      {resource.status === "success" && (
        <>
          <div className="detail-surface">
            <DetailContent festival={resource.data} />
          </div>
          <section className="similar-section" aria-labelledby="similar-title">
            <div className="section-head">
              <h2 id="similar-title" className="display">
                한 곳 더, 구경할까요?
              </h2>
            </div>
            {similar.status === "loading" && <Loading />}
            {similar.status === "error" && (
              <ErrorState error={similar.error} onRetry={similar.retry} />
            )}
            {similar.status === "success" &&
              (similar.data.length ? (
                <div className="result-list">
                  {similar.data.map((festival) => (
                    <FestivalCard
                      key={festival.content_id}
                      festival={festival}
                      onPreview={setPreviewId}
                    />
                  ))}
                </div>
              ) : (
                <p>
                  아직 비슷한 축제가 없어요. 축제 목록에서 다른 곳을 찾아보세요.
                </p>
              ))}
          </section>
        </>
      )}
      <FestivalPreview
        contentId={previewId}
        onNext={setPreviewId}
        onClose={() => setPreviewId(null)}
      />
    </section>
  );
}
