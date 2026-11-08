import { useState } from "react";
import { safeImageUrl } from "../../lib/format.js";
import Icon from "../common/Icon.jsx";
export default function FestivalImage({ festival, className = "", ...props }) {
  const src = safeImageUrl(festival.image_url);
  const [failed, setFailed] = useState(null);
  return src && failed !== src ? (
    <img
      className={className}
      src={src}
      alt={festival.image_alt || `${festival.title} 행사 사진`}
      onError={() => setFailed(src)}
      {...props}
    />
  ) : (
    <span
      className={`photo-fallback ${className}`}
      role="img"
      aria-label={`${festival.title} 사진 준비 중`}
    >
      <Icon name="ticket" />
      <span>기대되는 다음 장면</span>
    </span>
  );
}
