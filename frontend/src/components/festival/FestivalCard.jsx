import { Link } from "react-router-dom";
import Card from "../common/Card.jsx";
import Icon from "../common/Icon.jsx";
import FestivalImage from "./FestivalImage.jsx";
import LikeButton from "./LikeButton.jsx";
import {
  dateLabel,
  festivalStatus,
  plainText,
  statusNames,
} from "../../lib/format.js";
import { tagNames } from "../../data/festivals.js";

export default function FestivalCard({ festival, onPreview, reason }) {
  const url = `/festivals/${encodeURIComponent(festival.content_id)}`;
  return (
    <Card
      className="festival-ticket"
      style={{ "--ticket-bg": festival.ticket_color || "#fffdf5" }}
    >
      <div className="ticket-visual">
        <button
          className="photo-open"
          type="button"
          onClick={() => onPreview(festival.content_id)}
          aria-label={`${festival.title} 미리 보기`}
        >
          <FestivalImage
            festival={festival}
            className="ticket-photo"
            width="380"
            height="240"
            loading="lazy"
          />
        </button>
        <span className="date-chip">
          {dateLabel(festival.start_date, festival.end_date)}
        </span>
        <LikeButton festival={festival} />
        {festival.photo_credit && (
          <span className="ticket-photo-note">{festival.photo_credit}</span>
        )}
      </div>
      <div className="ticket-main">
        <p className="ticket-location">
          <Icon name="pin" />
          {festival.area_name || "전국"}에서 보내는 하루
        </p>
        <Link className="ticket-title" to={url}>
          <h3>{festival.title}</h3>
        </Link>
        <p className="ticket-summary">
          {reason ||
            festival.summary ||
            plainText(festival.overview) ||
            `${festival.place || festival.address || "축제 현장"}에서 새로운 하루를 만나보세요.`}
        </p>
      </div>
      <div className="ticket-perforation" aria-hidden="true" />
      <div className="ticket-foot">
        <span>
          {festivalStatus(festival) === "ended"
            ? statusNames.ended
            : festival.tags?.includes("night")
              ? "반짝이는 밤"
              : festival.tags?.includes("food")
                ? "맛있는 하루"
                : tagNames[festival.tags?.[0]] || "설레는 하루"}
        </span>
        <Link
          className="peek"
          to={url}
          aria-label={`${festival.title} 구경하기`}
        >
          구경하기 <Icon name="arrow" />
        </Link>
      </div>
    </Card>
  );
}
