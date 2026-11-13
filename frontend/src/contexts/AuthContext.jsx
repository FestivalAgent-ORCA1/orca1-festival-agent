import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { getAccessToken, repository } from "../api/repository.js";

const AuthContext = createContext(null);

// FavoritesContext와 약속한 방식: access_token 저장 후 orca:auth-changed 이벤트를 보냅니다.
function saveToken(token) {
  try {
    if (token) localStorage.setItem("access_token", token);
    else localStorage.removeItem("access_token");
  } catch {
    /* blocked browser storage */
  }
  window.dispatchEvent(new Event("orca:auth-changed"));
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(getAccessToken);
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const changed = () => setToken(getAccessToken());
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
    setError(null);
    if (!token) {
      setUser(null);
      return undefined;
    }
    const controller = new AbortController();
    repository
      .getMe(controller.signal)
      .then((me) => {
        if (!controller.signal.aborted) setUser(me);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setUser(null);
        // API 모드의 401은 client.js가 처리하고, 예시 모드의 401은 여기서 토큰을 비웁니다.
        if (err.status === 401) saveToken(null);
        else setError(err);
      });
    return () => controller.abort();
  }, [token, attempt]);
  const start = useCallback((result) => {
    setUser(result.user);
    saveToken(result.access_token);
    return result.user;
  }, []);
  const login = useCallback(
    async (email, password) => start(await repository.login({ email, password })),
    [start],
  );
  const signup = useCallback(
    async (email, password, nickname) =>
      start(await repository.signup({ email, password, nickname })),
    [start],
  );
  const logout = useCallback(() => {
    setUser(null);
    saveToken(null);
  }, []);
  const updateNickname = useCallback(async (nickname) => {
    const next = await repository.updateMe({ nickname });
    setUser(next);
    return next;
  }, []);
  const updatePreferences = useCallback(async (preferences) => {
    const next = await repository.updatePreferences(preferences);
    setUser(next);
    return next;
  }, []);
  // 탈퇴한 뒤 화면을 먼저 옮길 수 있도록 로그아웃은 부르는 쪽에서 합니다.
  const withdraw = useCallback(() => repository.deleteMe(), []);
  // guest: 비로그인 / loading: 내 정보 확인 중 / authenticated: 로그인 / error: 내 정보를 못 불러옴
  const status = !token
    ? "guest"
    : user
      ? "authenticated"
      : error
        ? "error"
        : "loading";
  return (
    <AuthContext.Provider
      value={{
        user,
        status,
        error,
        login,
        signup,
        logout,
        updateNickname,
        updatePreferences,
        withdraw,
        retry: () => setAttempt((value) => value + 1),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
export const useAuth = () => useContext(AuthContext);

// 로그인 후 돌아갈 주소는 내부 경로만 허용합니다. 로그인 관련 화면으로 돌아가면 무한 이동이 생기므로 첫 화면으로 보냅니다.
export function safeRedirect(value) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/";
  return /^\/(login|signup|onboarding)(\/|\?|$)/.test(value) ? "/" : value;
}
