import { useCallback } from "react";
import { repository } from "../../api/repository.js";
import { useFavorites } from "../../contexts/FavoritesContext.jsx";
import { useResource } from "../../hooks/useResource.js";
import FestivalCard from "./FestivalCard.jsx";
import Loading from "../common/Loading.jsx";
import ErrorState from "../common/ErrorState.jsx";

export default function Recommendations({ onPreview }) {
  const { session } = useFavorites();
  const resource = useResource(
    useCallback((signal) => repository.getRecommended(signal), []),
    repository.mode === "api" && session,
  );
  if (resource.status === "idle") return null;
  return (
    <section className="wrap recommendations" aria-labelledby="recommend-title">
      <div className="section-head">
        <div>
          <span className="eyebrow">A LITTLE MORE YOU</span>
          <h2 id="recommend-title" className="display">
            당신의 취향에 가까운 곳.
          </h2>
        </div>
      </div>
      {resource.status === "loading" && (
        <Loading text="취향에 맞는 축제를 고르고 있어요." />
      )}
      {resource.status === "error" && (
        <ErrorState error={resource.error} onRetry={resource.retry} />
      )}
      {resource.status === "success" &&
        (resource.data.length ? (
          <div className="result-list">
            {resource.data.map((festival) => (
              <FestivalCard
                key={festival.content_id}
                festival={festival}
                reason={festival.reason}
                onPreview={onPreview}
              />
            ))}
          </div>
        ) : (
          <p className="section-intro">
            아직 추천할 축제가 없어요. 아래에서 직접 둘러볼까요?
          </p>
        ))}
    </section>
  );
}
