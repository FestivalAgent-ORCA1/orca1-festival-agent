import { Link } from "react-router-dom";
import FestivalImage from "./FestivalImage.jsx";
import LikeButton from "./LikeButton.jsx";
import Button from "../common/Button.jsx";
import Icon from "../common/Icon.jsx";
import TagChip from "../common/TagChip.jsx";
import {
  dateLabel,
  plainText,
  safeExternalUrl,
  festivalStatus,
  statusNames,
} from "../../lib/format.js";
import { tagNames } from "../../data/festivals.js";

export default function DetailContent({
  festival,
  preview = false,
  next,
  onNext,
  onClose,
}) {
  const homepage = safeExternalUrl(festival.homepage);
  const Heading = preview ? "h3" : "h1";
  return (
    <div className="detail-layout">
      <div className="detail-photo-wrap">
        <FestivalImage
          festival={festival}
          className="detail-photo"
          width="390"
          height="510"
        />
        {festival.photo_credit && <small>{festival.photo_credit}</small>}
      </div>
      <div className="detail-body">
        <span className="eyebrow">
          ONE SCENE, A GOOD WEEKEND · {statusNames[festivalStatus(festival)]}
        </span>
        <Heading className="detail-heading">{festival.title}</Heading>
        <div className="detail-tags">
          {festival.tags?.map((tag) => (
            <TagChip key={tag}>{tagNames[tag] || tag}</TagChip>
          ))}
        </div>
        <p className="detail-intro">
          {plainText(festival.overview) ||
            festival.summary ||
            "상세 소개를 준비 중이에요. 방문 전 공식 안내를 확인해 주세요."}
        </p>
        <dl className="detail-meta">
          <dt>언제</dt>
          <dd>
            {dateLabel(festival.start_date, festival.end_date, { year: true })}
          </dd>
          <dt>어디</dt>
          <dd>{festival.place || festival.address || "장소 안내 준비 중"}</dd>
          {festival.place && festival.address && (
            <>
              <dt>주소</dt>
              <dd>{festival.address}</dd>
            </>
          )}
          <dt>시간</dt>
          <dd>
            {plainText(festival.playtime) || "공식 안내에서 확인해 주세요."}
          </dd>
          <dt>요금</dt>
          <dd>{plainText(festival.fee) || "공식 안내에서 확인해 주세요."}</dd>
          {festival.tel && (
            <>
              <dt>문의</dt>
              <dd>{festival.tel}</dd>
            </>
          )}
        </dl>
        <div className="detail-actions">
          {preview ? (
            <Button
              as={Link}
              to={`/festivals/${encodeURIComponent(festival.content_id)}`}
              variant="blue"
              onClick={onClose}
            >
              축제 더 구경하기 <Icon name="arrow" />
            </Button>
          ) : (
            homepage && (
              <Button
                as="a"
                href={homepage}
                target="_blank"
                rel="noopener noreferrer"
                variant="blue"
              >
                공식 안내 보기 <Icon name="arrow" />
              </Button>
            )
          )}
          <LikeButton festival={festival} className="detail-save" />
        </div>
        {preview && next && (
          <button
            type="button"
            className="detail-next"
            onClick={() => onNext(next.content_id)}
          >
            <span>한 곳 더 둘러볼까요? · {next.title}</span>
            <Icon name="arrow" />
          </button>
        )}
        {!preview && (
          <p className="visit-note">
            방문 전 운영 시간과 행사 변경 사항을 공식 안내에서 확인해 주세요.
          </p>
        )}
      </div>
    </div>
  );
}
