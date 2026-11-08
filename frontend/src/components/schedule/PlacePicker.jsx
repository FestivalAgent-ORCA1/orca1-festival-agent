import { useCallback, useEffect, useState } from "react";
import { repository } from "../../api/repository.js";
import { useResource } from "../../hooks/useResource.js";
import Button from "../common/Button.jsx";
import Loading from "../common/Loading.jsx";
import ErrorState from "../common/ErrorState.jsx";
import EmptyState from "../common/EmptyState.jsx";

// FE2 지원용 부품. 선택 상태와 일정 계산은 부모가 관리합니다.
export default function PlacePicker({
  festivalContentId,
  selectedIds = [],
  onAdd,
  onRemove,
}) {
  const [category, setCategory] = useState("attraction");
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [festivalContentId]);
  const resource = useResource(
    useCallback(
      (signal) =>
        repository.getNearby(
          { content_id: festivalContentId, category, page, size: 10 },
          signal,
        ),
      [festivalContentId, category, page],
    ),
    Boolean(festivalContentId) && repository.mode === "api",
  );
  return (
    <section className="place-picker" aria-label="일정에 넣을 주변 장소">
      <h3>축제 가는 길, 한 곳 더.</h3>
      <div className="filters" role="group" aria-label="주변 장소 종류">
        {[
          ["attraction", "관광지"],
          ["restaurant", "음식점"],
          ["cafe", "카페"],
        ].map(([value, label]) => (
          <button
            type="button"
            className="mood"
            key={value}
            aria-pressed={category === value}
            onClick={() => {
              setCategory(value);
              setPage(1);
            }}
          >
            {label}
          </button>
        ))}
      </div>
      {resource.status === "idle" && (
        <p className="place-picker-note">
          축제의 주변 장소는 서버 연결 후 확인할 수 있어요.
        </p>
      )}
      {resource.status === "loading" && (
        <Loading text="가까운 곳을 찾아보고 있어요." />
      )}
      {resource.status === "error" && (
        <ErrorState error={resource.error} onRetry={resource.retry} />
      )}
      {resource.status === "success" &&
        (resource.data.items.length ? (
          <ul className="place-list">
            {resource.data.items.map((place) => {
              const selected = selectedIds.includes(place.content_id);
              return (
                <li key={place.content_id}>
                  <div>
                    <strong>{place.name}</strong>
                    <p>{place.address}</p>
                    {Number.isFinite(place.distance_m) && (
                      <p>
                        {place.distance_m >= 1000
                          ? `${(place.distance_m / 1000).toFixed(1)}km`
                          : `${place.distance_m}m`}{" "}
                        거리
                      </p>
                    )}
                  </div>
                  <Button
                    variant={selected ? "" : "white"}
                    aria-pressed={selected}
                    disabled={selected ? !onRemove : !onAdd}
                    onClick={() =>
                      selected ? onRemove(place.content_id) : onAdd(place)
                    }
                  >
                    {selected ? "빼기" : "담기"}
                  </Button>
                </li>
              );
            })}
          </ul>
        ) : (
          <EmptyState title="가까운 장소를 찾지 못했어요.">
            다른 종류의 장소를 찾아볼까요?
          </EmptyState>
        ))}
      {resource.data?.total > 10 && (
        <nav className="pagination" aria-label="주변 장소 페이지">
          <Button disabled={page === 1} onClick={() => setPage(page - 1)}>
            이전
          </Button>
          <span>
            {page} / {Math.ceil(resource.data.total / 10)}
          </span>
          <Button
            disabled={page >= Math.ceil(resource.data.total / 10)}
            onClick={() => setPage(page + 1)}
          >
            다음
          </Button>
        </nav>
      )}
    </section>
  );
}
