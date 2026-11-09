// POST /api/itinerary/calculate — 저장하지 않고 시간표만 계산 (api-spec.md 6장)
export const createItineraryApi = (request) => ({
  calculateItinerary: (
    { festival_content_id, visit_date, start_time, end_time, place_ids = [], auto_fill = true },
    signal,
  ) =>
    request("/api/itinerary/calculate", {
      method: "POST",
      body: {
        festival_content_id,
        visit_date,
        start_time,
        end_time,
        place_ids,
        auto_fill,
      },
      signal,
    }),
});
