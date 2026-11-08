import test from "node:test";
import assert from "node:assert/strict";
import { createAuthApi } from "../src/api/auth.js";
import { createUsersApi } from "../src/api/users.js";
import { createDemoAuth } from "../src/api/demoAuth.js";

function memoryStorage() {
  const data = new Map();
  return {
    getItem: (key) => (data.has(key) ? data.get(key) : null),
    setItem: (key, value) => data.set(key, String(value)),
  };
}

test("회원·내 정보 API가 명세의 주소와 메서드로 요청한다", async () => {
  const seen = [];
  const request = async (path, options = {}) => {
    seen.push([options.method || "GET", path, options.body]);
    return {};
  };
  const auth = createAuthApi(request),
    users = createUsersApi(request);
  await auth.signup({ email: "a@b.c", password: "password123", nickname: "축제" });
  await auth.login({ email: "a@b.c", password: "password123" });
  await users.getMe();
  await users.updateMe({ nickname: "새이름" });
  await users.updatePreferences({ age_group: "20s", regions: ["1"], tags: ["music"] });
  await users.deleteMe();
  assert.deepEqual(
    seen.map(([method, path]) => `${method} ${path}`),
    [
      "POST /api/auth/signup",
      "POST /api/auth/login",
      "GET /api/users/me",
      "PATCH /api/users/me",
      "PUT /api/users/me/preferences",
      "DELETE /api/users/me",
    ],
  );
});

test("예시 계정으로 가입·로그인·첫 설정·탈퇴를 할 수 있다", async () => {
  const storage = memoryStorage();
  let token = null;
  const demo = createDemoAuth(storage, () => token);
  const joined = await demo.signup({
    email: " Fan@Example.com ",
    password: "password123",
    nickname: "축제러버",
  });
  assert.equal(joined.user.email, "fan@example.com");
  assert.equal(joined.user.onboarded, false);
  await assert.rejects(
    demo.signup({ email: "fan@example.com", password: "password123", nickname: "다른사람" }),
    { status: 409, code: "EMAIL_DUPLICATED" },
  );
  await assert.rejects(demo.login({ email: "fan@example.com", password: "short" }), {
    status: 401,
    code: "INVALID_CREDENTIALS",
  });
  token = (await demo.login({ email: "fan@example.com", password: "anything1" })).access_token;
  const updated = await demo.updatePreferences({
    age_group: "20s",
    regions: ["1"],
    tags: ["music"],
  });
  assert.equal(updated.onboarded, true);
  // 새로고침해도 저장된 계정이 남는다
  const reloaded = createDemoAuth(storage, () => token);
  assert.equal((await reloaded.getMe()).nickname, "축제러버");
  await reloaded.deleteMe();
  await assert.rejects(reloaded.getMe(), { status: 401 });
});

test("예시 계정은 명세의 입력 규칙을 지킨다", async () => {
  const demo = createDemoAuth(memoryStorage(), () => null);
  await assert.rejects(
    demo.signup({ email: "a@b.c", password: "1234567", nickname: "축제" }),
    { status: 422 },
  );
  await assert.rejects(
    demo.signup({ email: "a@b.c", password: "password123", nickname: "가" }),
    { status: 422 },
  );
});
