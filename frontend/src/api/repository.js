import { createApiClient } from "./client.js";
import { createFestivalApi } from "./festivals.js";
import { createLikesApi } from "./likes.js";
import { createPlacesApi } from "./places.js";
import { createDemoRepository } from "./demo.js";

// FE3 AuthContext 연결점: access_token 저장 후 orca:auth-changed 이벤트를 보냅니다.
export function getAccessToken() {
  try {
    return localStorage.getItem("access_token");
  } catch {
    return null;
  }
}
const mode = import.meta.env.VITE_DATA_MODE || "mock";
if (!["mock", "api"].includes(mode))
  throw new Error("VITE_DATA_MODE must be mock or api");
const request = createApiClient({
  baseUrl: import.meta.env.VITE_API_BASE_URL || "",
  getToken: getAccessToken,
  onUnauthorized() {
    try {
      localStorage.removeItem("access_token");
    } catch {
      /* blocked browser storage */
    }
    window.dispatchEvent(new Event("orca:auth-changed"));
    if (window.location.pathname !== "/login")
      window.location.assign(
        `/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`,
      );
  },
});
let storage;
try {
  storage = window.localStorage;
} catch {
  /* demo still works in memory */
}
export const repository =
  mode === "mock"
    ? createDemoRepository(storage)
    : {
        mode,
        hasSession: () => Boolean(getAccessToken()),
        ...createFestivalApi(request),
        ...createLikesApi(request),
        ...createPlacesApi(request),
      };
