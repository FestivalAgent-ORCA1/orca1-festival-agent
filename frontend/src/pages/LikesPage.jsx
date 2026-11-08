import { useState } from "react";
import { Link } from "react-router-dom";
import { repository } from "../api/repository.js";
import { useFavorites } from "../contexts/FavoritesContext.jsx";
import FestivalCard from "../components/festival/FestivalCard.jsx";
import FestivalPreview from "../components/festival/FestivalPreview.jsx";
import Loading from "../components/common/Loading.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import Button from "../components/common/Button.jsx";
export default function LikesPage() {
  const favorites = useFavorites();
  const [previewId, setPreviewId] = useState(null);
  return (
    <section className="wrap likes-page">
      <div className="page-intro">
        <span className="eyebrow">MY WEEKEND PASSES</span>
        <h1 className="display">좋아하는 하루, {favorites.items.length}장.</h1>
        <p>
          {repository.mode === "mock"
            ? "이 브라우저에 모아둔 예시 축제예요."
            : "마음이 먼저 다녀온 곳들을 모았어요."}
        </p>
      </div>
      {favorites.status === "loading" ? (
        <Loading />
      ) : favorites.status === "error" ? (
        <ErrorState error={favorites.error} onRetry={favorites.retry} />
      ) : favorites.items.length ? (
        <div className="result-list">
          {favorites.items.map((festival) => (
            <FestivalCard
              key={festival.content_id}
              festival={festival}
              onPreview={setPreviewId}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title={
            favorites.session
              ? "아직 비어 있는 주말의 티켓"
              : "로그인하고 나만의 티켓을 모아요."
          }
        >
          <span>
            {favorites.session
              ? "축제를 구경하다 마음에 드는 곳에 하트를 눌러보세요."
              : "계정에 찜한 축제는 로그인한 뒤 볼 수 있어요."}
          </span>
          <br />
          <Button as={Link} variant="white" to="/festivals">
            축제 구경하러 가기
          </Button>
        </EmptyState>
      )}
      <FestivalPreview
        contentId={previewId}
        onNext={setPreviewId}
        onClose={() => setPreviewId(null)}
      />
    </section>
  );
}
