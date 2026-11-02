import { Link } from "react-router-dom";
import { useCallback } from "react";
import { repository } from "../../api/repository.js";
import { demoFestivals } from "../../data/festivals.js";
import { useResource } from "../../hooks/useResource.js";
import FestivalImage from "./FestivalImage.jsx";
import Button from "../common/Button.jsx";
import Icon from "../common/Icon.jsx";

export default function Hero({ onPreview }) {
  const resource = useResource(
    useCallback(
      (signal) => repository.getFestivals({ size: 2, page: 1 }, signal),
      [],
    ),
    repository.mode === "api",
  );
  const items =
    repository.mode === "mock" ? demoFestivals : resource.data?.items || [];
  return (
    <section className="hero wrap" aria-labelledby="hero-title">
      <div className="hero-copy">
        <div className="hero-kicker eyebrow">
          <Icon name="spark" className="small-flower" />A LITTLE GETAWAY, A GOOD
          WEEKEND.
        </div>
        <h1 id="hero-title" className="display">
          이번 주말은
          <br />
          조금, <span className="word-orange">들떠도 돼.</span>
        </h1>
        <p className="hero-desc">
          가까운 동네의 즐거움부터 처음 만나는 풍경까지.
          <br />
          좋아하는 장면을 골라, 주말의 입장권을 모아봐요.
        </p>
        <div className="hero-actions">
          <Button as={Link} to="/festivals" variant="blue" className="hero-cta">
            내 주말 찾으러 가기 <Icon name="arrow" />
          </Button>
          <span className="aside-note">
            <span>멀리 안 가도 괜찮아요.</span>
            <span>설레는 곳이면 충분하니까.</span>
          </span>
        </div>
      </div>
      <div className="hero-art" aria-label="축제 사진으로 만든 주말의 입장권">
        <div className="orbital" aria-hidden="true" />
        <span className="art-label">
          이번엔 진짜,
          <br />
          밖으로 나가볼까?
          <svg viewBox="0 0 80 44" fill="none" aria-hidden="true">
            <path
              d="M6 3C3 29 40 42 68 27m-12-2 14 1-7 12"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <Icon name="spark" className="art-star" />
        <div className="lucky-stamp" aria-hidden="true">
          좋아하는 곳으로<strong>나가자!</strong>YOUR WEEKEND PASS
        </div>
        {items.slice(0, 2).map((festival, i) => (
          <button
            key={festival.content_id}
            className={`postcard ${i === 0 ? "fireworks" : "apple"}`}
            type="button"
            onClick={() => onPreview(festival.content_id)}
            aria-label={`${festival.title} 미리 보기`}
          >
            <FestivalImage
              festival={festival}
              width={i === 0 ? 284 : 194}
              height={i === 0 ? 293 : 176}
            />
            <span className="photo-caption">
              <span>{i === 0 ? "좋아하는 장면 하나" : "조금 다른 하루"}</span>
              <span>{festival.area_name} ↗</span>
            </span>
          </button>
        ))}
        {!items.length && (
          <div className="hero-no-photo" aria-hidden="true">
            <Icon name="ticket" />
            <span>
              YOUR
              <br />
              NEXT
              <br />
              WEEKEND
            </span>
          </div>
        )}
        <div className="stub" aria-hidden="true">
          <span className="stub-copy">
            <small>YOUR WEEKEND PASS</small>
            <strong>좋아하는 하루에 입장</strong>
          </span>
          <span className="stub-date">
            ORCA<small>LET'S GO OUT</small>
          </span>
        </div>
        <Icon name="spark" className="tiny-star" />
        <span className="art-smallprint">
          {repository.mode === "mock"
            ? "사진: 지난 행사 및 공식 프로그램 자료"
            : "마음에 드는 장면에서 시작해요."}
        </span>
      </div>
    </section>
  );
}
