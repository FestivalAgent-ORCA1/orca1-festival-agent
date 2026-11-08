import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { repository } from "../../api/repository.js";
import { useResource } from "../../hooks/useResource.js";
import FilterBar from "./FilterBar.jsx";
import FestivalCard from "./FestivalCard.jsx";
import Icon from "../common/Icon.jsx";
import Button from "../common/Button.jsx";
import Loading from "../common/Loading.jsx";
import ErrorState from "../common/ErrorState.jsx";
import EmptyState from "../common/EmptyState.jsx";
import { parsePage } from "../../lib/format.js";

export default function FestivalBrowser({ onPreview, home = false }) {
  const [params, setParams] = useSearchParams();
  const query = {
    keyword: params.get("keyword") || "",
    area_code: params.get("area_code") || "",
    tags: params.get("tags") || "",
    sort: ["title", "end_date"].includes(params.get("sort"))
      ? params.get("sort")
      : "start_date",
    page: parsePage(params.get("page")),
    size: 12,
  };
  const key = JSON.stringify(query);
  const resource = useResource(
    useCallback(
      (signal) => repository.getFestivals(JSON.parse(key), signal),
      [key],
    ),
  );
  const update = (changes) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([name, value]) =>
      value ? next.set(name, value) : next.delete(name),
    );
    setParams(next);
  };
  const result = resource.data;
  return (
    <>
      <div className="wrap">
        <FilterBar query={query} onChange={update} />
        {home && (
          <div className="loop-strip" aria-hidden="true">
            <span>THE WEEKEND CLUB</span>
            <span className="spark">✳</span>
            <span>가고 싶은 곳을 발견하고</span>
            <span className="spark">·</span>
            <span>하트로 모아두고</span>
            <span className="spark">·</span>
            <span>한 곳 더 둘러보기</span>
          </div>
        )}
      </div>
      <section
        className="explore wrap"
        id="explore"
        aria-labelledby="explore-title"
      >
        <div className="section-head">
          <div>
            <span className="eyebrow">PICK YOUR SCENE</span>
            <h2 className="display" id="explore-title">
              마음에 드는 장면, 한 곳 더.
            </h2>
          </div>
          <p className="section-intro">
            오늘은 어떤 기분인가요?
            <br />
            기분에 따라, 끌리는 축제도 달라지니까.
          </p>
        </div>
        <div className="filter-tools">
          <div className="filters" role="group" aria-label="축제 분위기 선택">
            {[
              ["", "모두 둘러보기", null],
              ["night", "반짝이는 밤", "moon"],
              ["food", "맛있는 하루", "apple"],
            ].map(([value, label, icon]) => (
              <button
                key={value}
                className="mood"
                type="button"
                aria-pressed={query.tags === value}
                onClick={() => update({ tags: value, page: "" })}
              >
                {icon && <Icon name={icon} />}
                {label}
              </button>
            ))}
          </div>
          <label className="sort-field">
            정렬{" "}
            <select
              value={query.sort}
              onChange={(event) =>
                update({ sort: event.target.value, page: "" })
              }
            >
              <option value="start_date">시작일순</option>
              <option value="end_date">종료일순</option>
              <option value="title">이름순</option>
            </select>
          </label>
        </div>
        <p className="results-caption" aria-live="polite">
          {resource.status === "success"
            ? `${result?.total || 0}곳의 축제를 찾았어요. 마음에 드는 곳을 골라보세요.`
            : resource.status === "loading"
              ? "축제를 불러오고 있어요."
              : ""}
        </p>
        {resource.status === "loading" && <Loading />}
        {resource.status === "error" && (
          <ErrorState error={resource.error} onRetry={resource.retry} />
        )}
        {resource.status === "success" &&
          (result?.items?.length ? (
            <div className="result-list">
              {result.items.map((festival) => (
                <FestivalCard
                  key={festival.content_id}
                  festival={festival}
                  onPreview={onPreview}
                />
              ))}
            </div>
          ) : (
            <EmptyState onReset={() => setParams({})}>
              다른 지역이나 축제 이름으로 다시 찾아볼까요?
            </EmptyState>
          ))}
        {result && result.total > query.size && (
          <nav className="pagination" aria-label="축제 목록 페이지">
            <Button
              disabled={query.page === 1}
              onClick={() => update({ page: query.page - 1 })}
            >
              이전
            </Button>
            <span>
              {query.page} / {Math.ceil(result.total / query.size)}
            </span>
            <Button
              disabled={query.page >= Math.ceil(result.total / query.size)}
              onClick={() => update({ page: query.page + 1 })}
            >
              다음
            </Button>
          </nav>
        )}
      </section>
    </>
  );
}
