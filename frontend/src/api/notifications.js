export function createNotificationsApi(request) {
  return {
    getNotifications: (query, signal) =>
      request("/api/notifications", { query, signal }),
    getUnreadCount: (signal) =>
      request("/api/notifications/unread-count", { signal }),
    markRead: (id) =>
      request(`/api/notifications/${encodeURIComponent(id)}/read`, {
        method: "PATCH",
      }),
    markAllRead: () =>
      request("/api/notifications/read-all", { method: "PATCH" }),
  };
}
