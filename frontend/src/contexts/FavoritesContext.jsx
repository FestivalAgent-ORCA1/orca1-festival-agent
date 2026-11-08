import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { repository } from "../api/repository.js";
import { useToast } from "./ToastContext.jsx";

const FavoritesContext = createContext(null);
export function FavoritesProvider({ children }) {
  const [items, setItems] = useState([]);
  const [knownIds, setKnownIds] = useState(new Set());
  const [pending, setPending] = useState(new Set());
  const [session, setSession] = useState(repository.hasSession());
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);
  const locks = useRef(new Set());
  const generation = useRef(0);
  const notify = useToast();
  useEffect(() => {
    const changed = () => {
      setSession(repository.hasSession());
      setAttempt((value) => value + 1);
    };
    const storageChanged = (event) => {
      if (event.key === "access_token") changed();
    };
    window.addEventListener("orca:auth-changed", changed);
    window.addEventListener("storage", storageChanged);
    return () => {
      window.removeEventListener("orca:auth-changed", changed);
      window.removeEventListener("storage", storageChanged);
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    generation.current += 1;
    setItems([]);
    setKnownIds(new Set());
    setError(null);
    if (!session) {
      setStatus("success");
      return () => controller.abort();
    }
    setStatus("loading");
    repository
      .getLikes(controller.signal)
      .then((next) => {
        if (!controller.signal.aborted) {
          setItems(next);
          setKnownIds(new Set(next.map((item) => item.content_id)));
          setStatus("success");
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setError(err);
          setStatus("error");
        }
      });
    return () => {
      controller.abort();
      generation.current += 1;
    };
  }, [session, attempt]);
  const toggle = useCallback(
    async (festival) => {
      const id = festival.content_id;
      if (!session) {
        notify("찜은 로그인 후 이용할 수 있어요.");
        return null;
      }
      if (status !== "success") {
        notify("찜 목록을 먼저 불러온 뒤 다시 시도해 주세요.");
        return null;
      }
      if (locks.current.has(id)) return null;
      locks.current.add(id);
      setPending(new Set(locks.current));
      const currentGeneration = generation.current;
      const added = !knownIds.has(id);
      try {
        await (added ? repository.addLike(id) : repository.removeLike(id));
        if (currentGeneration !== generation.current) return null;
        setKnownIds((previous) => {
          const next = new Set(previous);
          added ? next.add(id) : next.delete(id);
          return next;
        });
        setItems((previous) =>
          added
            ? [
                ...previous.filter((item) => item.content_id !== id),
                { ...festival, is_liked: true },
              ]
            : previous.filter((item) => item.content_id !== id),
        );
        notify(
          repository.storageWarning
            ? "찜을 변경했지만 이 브라우저에서는 새로고침 후 사라질 수 있어요."
            : `${festival.title}${added ? "를 주말의 티켓에 담았어요." : " 찜을 해제했어요."}`,
        );
        return { added };
      } catch (err) {
        if (currentGeneration === generation.current)
          notify(err.message || "찜을 변경하지 못했어요. 다시 시도해 주세요.");
        return null;
      } finally {
        locks.current.delete(id);
        setPending(new Set(locks.current));
      }
    },
    [session, status, knownIds, notify],
  );
  return (
    <FavoritesContext.Provider
      value={{
        items,
        pending,
        status,
        error,
        session,
        toggle,
        isLiked: (id) => knownIds.has(id),
        retry: () => setAttempt((value) => value + 1),
      }}
    >
      {children}
    </FavoritesContext.Provider>
  );
}
export const useFavorites = () => useContext(FavoritesContext);
