import { Link } from "react-router-dom";
import { useFavorites } from "../../contexts/FavoritesContext.jsx";
import Icon from "../common/Icon.jsx";
import Button from "../common/Button.jsx";
import Loading from "../common/Loading.jsx";
import ErrorState from "../common/ErrorState.jsx";
import FestivalImage from "./FestivalImage.jsx";
import { dateLabel } from "../../lib/format.js";

export default function SavedCollection() {
  const favorites = useFavorites();
  return (
    <section className="collection" id="saved" aria-labelledby="saved-title">
      <div className="collection-inner wrap">
        <div>
          <span className="eyebrow">LITTLE PLANS, GOOD MEMORIES</span>
          <h2 className="display" id="saved-title">
            가고 싶은 곳은
            <br />
            하트로 모아두세요.
          </h2>
          <p className="collection-copy">
            당장 떠나지 않아도 괜찮아요.
            <br />
            좋아하는 곳을 모으다 보면, 다음 주말이 기다려질 거예요.
          </p>
        </div>
        <div className="saved-panel">
          {favorites.status === "loading" ? (
            <Loading text="모아둔 티켓을 찾고 있어요." />
          ) : favorites.status === "error" ? (
            <ErrorState error={favorites.error} onRetry={favorites.retry} />
          ) : favorites.items.length ? (
            <div className="saved-list">
              {favorites.items.slice(0, 3).map((festival) => (
                <Link
                  className="saved-row"
                  key={festival.content_id}
                  to={`/festivals/${encodeURIComponent(festival.content_id)}`}
                >
                  <FestivalImage festival={festival} width="64" height="55" />
                  <span>
                    <span className="saved-row-title">{festival.title}</span>
                    <span className="saved-row-date">
                      {dateLabel(festival.start_date, festival.end_date)} ·{" "}
                      {festival.area_name}
                    </span>
                  </span>
                  <Icon name="arrow" />
                </Link>
              ))}
              <Button as={Link} to="/likes" variant="white">
                나의 티켓 {favorites.items.length}장 모두 보기
              </Button>
            </div>
          ) : (
            <div className="empty-pass">
              <Icon name="ticket" />
              <div>
                <strong>아직 비어 있는 주말의 티켓</strong>
                <p>
                  {favorites.session ? (
                    <>
                      위에서 하트를 눌러 하나 모아보세요.
                      <br />
                      좋아하는 곳이 생기면 여기에 담아둘게요.
                    </>
                  ) : (
                    "로그인하면 좋아하는 곳을 모아둘 수 있어요."
                  )}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
