import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useFavorites } from "../../contexts/FavoritesContext.jsx";
import Icon from "../common/Icon.jsx";

export default function LikeButton({ festival, className = "" }) {
  const { isLiked, toggle, pending, status } = useFavorites();
  const [burst, setBurst] = useState(null);
  const timer = useRef(null);
  useEffect(() => () => clearTimeout(timer.current), []);
  const liked = isLiked(festival.content_id);
  return (
    <>
      <button
        className={`save-btn ${className} ${burst ? "celebrate" : ""}`}
        type="button"
        aria-pressed={liked}
        aria-label={`${festival.title} ${liked ? "찜 해제" : "찜하기"}`}
        disabled={pending.has(festival.content_id) || status === "loading"}
        aria-busy={pending.has(festival.content_id)}
        onClick={async (event) => {
          const button = event.currentTarget;
          const result = await toggle(festival);
          if (
            result?.added &&
            button.isConnected &&
            !window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ) {
            const rect = button.getBoundingClientRect();
            clearTimeout(timer.current);
            setBurst({
              x: rect.left + rect.width / 2,
              y: rect.top + rect.height / 2,
              target: button.closest("dialog") || document.body,
            });
            timer.current = setTimeout(() => setBurst(null), 650);
          }
        }}
      >
        <Icon name="heart" />
      </button>
      {burst &&
        createPortal(
          <span aria-hidden="true" className="burst-layer">
            <span
              className="spark-ring"
              style={{ left: burst.x, top: burst.y }}
            />
            {Array.from({ length: 12 }, (_, i) => (
              <span
                key={i}
                className={`spark-particle ${i % 3 === 0 ? "streak" : ""}`}
                style={{
                  left: burst.x,
                  top: burst.y,
                  "--dx": `${Math.cos((i / 12) * Math.PI * 2) * (27 + (i % 3) * 7)}px`,
                  "--dy": `${Math.sin((i / 12) * Math.PI * 2) * (27 + (i % 3) * 7) - 5}px`,
                  "--turn": `${i * 37}deg`,
                  "--particle-color": ["#e87c59", "#8eaa62", "#6685e3"][i % 3],
                }}
              />
            ))}
          </span>,
          burst.target,
        )}
    </>
  );
}
