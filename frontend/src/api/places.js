export const createPlacesApi = (request) => ({
  getNearby: (query, signal) =>
    request("/api/places/nearby", { query, signal }),
});
