import { createApiClient } from "./client.js";
import { createFestivalApi } from "./festivals.js";
import { createLikesApi } from "./likes.js";
import { createPlacesApi } from "./places.js";
import { createAuthApi } from "./auth.js";
import { createUsersApi } from "./users.js";
import { createDemoRepository } from "./demo.js";
import { createDemoAuth } from "./demoAuth.js";
import { createPostsApi } from "./posts.js";
import { createDemoCommunity } from "./demoCommunity.js";
import { createAgentApi } from "./agent.js";
import { createItineraryApi } from "./itinerary.js";
import { createSchedulesApi } from "./schedules.js";
import { createPlannerDemo } from "./plannerDemo.js";

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
function createMockRepository() {
  const auth = createDemoAuth(storage, getAccessToken);
  // spread 대신 Object.assign을 써야 demo의 storageWarning getter가 유지됩니다.
  // FE3 예시 계정·커뮤니티 · FE2 채팅·일정 예시를 함께 붙입니다.
  return Object.assign(
    createDemoRepository(storage),
    auth,
    createDemoCommunity(storage, () => auth.getMe().catch(() => null)),
    createPlannerDemo(storage),
  );
}
export const repository =
  mode === "mock"
    ? createMockRepository()
    : {
        mode,
        hasSession: () => Boolean(getAccessToken()),
        ...createFestivalApi(request),
        ...createLikesApi(request),
        ...createPlacesApi(request),
        ...createAuthApi(request),
        ...createUsersApi(request),
        ...createPostsApi(request),
        ...createAgentApi(request),
        ...createItineraryApi(request),
        ...createSchedulesApi(request),
      };
