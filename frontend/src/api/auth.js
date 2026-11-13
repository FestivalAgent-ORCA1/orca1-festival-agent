export function createAuthApi(request) {
  return {
    signup: (body) => request("/api/auth/signup", { method: "POST", body }),
    login: (body) => request("/api/auth/login", { method: "POST", body }),
  };
}
