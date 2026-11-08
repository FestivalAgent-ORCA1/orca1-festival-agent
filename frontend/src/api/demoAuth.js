import { ApiError } from "./client.js";

// 예시 모드의 계정은 이 브라우저에만 저장합니다. 비밀번호는 저장하지 않으므로
// 가입한 이메일과 8자 이상의 아무 비밀번호로 로그인됩니다.
export function createDemoAuth(storage, getToken) {
  const key = "orca:demo:users:v1";
  let users = {};
  try {
    const stored = JSON.parse(storage?.getItem(key) || "{}");
    if (stored && typeof stored === "object" && !Array.isArray(stored))
      users = stored;
  } catch {
    /* 깨진 값은 비우고 시작합니다 */
  }
  const persist = () => {
    try {
      storage?.setItem(key, JSON.stringify(users));
    } catch {
      /* blocked browser storage */
    }
  };
  const tokenFor = (user) => `demo-token:${user.id}`;
  const session = (user) => ({
    access_token: tokenFor(user),
    token_type: "bearer",
    user,
  });
  const save = (user) => {
    users[user.email] = user;
    persist();
    return user;
  };
  const current = () => {
    const token = getToken();
    const user = Object.values(users).find((item) => tokenFor(item) === token);
    if (!user) throw new ApiError(401, "UNAUTHORIZED", "다시 로그인해 주세요.");
    return user;
  };
  const invalid = (message) => new ApiError(422, "VALIDATION_ERROR", message);
  const checkNickname = (nickname = "") => {
    const value = nickname.trim();
    if (value.length < 2 || value.length > 15)
      throw invalid("닉네임은 2~15자로 입력해 주세요.");
    return value;
  };
  return {
    async signup({ email = "", password = "", nickname }) {
      const address = email.trim().toLowerCase();
      if (!address.includes("@")) throw invalid("이메일 형식을 확인해 주세요.");
      if (password.length < 8)
        throw invalid("비밀번호는 8자 이상 입력해 주세요.");
      const name = checkNickname(nickname);
      if (users[address])
        throw new ApiError(409, "EMAIL_DUPLICATED", "이미 가입된 이메일이에요.");
      return session(
        save({
          id: Date.now(),
          email: address,
          nickname: name,
          age_group: null,
          regions: [],
          tags: [],
          onboarded: false,
          created_at: new Date().toISOString(),
        }),
      );
    },
    async login({ email = "", password = "" }) {
      const user = users[email.trim().toLowerCase()];
      if (!user || password.length < 8)
        throw new ApiError(
          401,
          "INVALID_CREDENTIALS",
          "이메일 또는 비밀번호를 확인해 주세요.",
        );
      return session(user);
    },
    getMe: async () => current(),
    updateMe: async ({ nickname }) =>
      save({ ...current(), nickname: checkNickname(nickname) }),
    async updatePreferences({ age_group, regions = [], tags = [] }) {
      if (regions.length > 3) throw invalid("지역은 3곳까지 고를 수 있어요.");
      if (tags.length < 1 || tags.length > 5)
        throw invalid("관심사는 1~5개 골라 주세요.");
      return save({ ...current(), age_group, regions, tags, onboarded: true });
    },
    async deleteMe() {
      delete users[current().email];
      persist();
    },
  };
}
