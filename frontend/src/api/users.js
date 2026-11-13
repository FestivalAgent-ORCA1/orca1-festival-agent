export function createUsersApi(request) {
  return {
    getMe: (signal) => request("/api/users/me", { signal }),
    updateMe: (body) => request("/api/users/me", { method: "PATCH", body }),
    updatePreferences: (body) =>
      request("/api/users/me/preferences", { method: "PUT", body }),
    deleteMe: () =>
      request("/api/users/me", { method: "DELETE", allowEmptyResponse: true }),
  };
}
