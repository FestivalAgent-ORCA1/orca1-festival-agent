export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function createApiClient({
  baseUrl = "",
  getToken = () => null,
  onUnauthorized = () => {},
  fetcher = globalThis.fetch,
  // Render 개발 서버가 절전에서 깨어나는 시간(약 1분)을 기다립니다.
  timeoutMs = 90000,
} = {}) {
  return async function request(
    path,
    { query, body, signal, method = "GET", allowEmptyResponse = false } = {},
  ) {
    const search = new URLSearchParams();
    Object.entries(query || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "")
        search.set(key, Array.isArray(value) ? value.join(",") : String(value));
    });
    const controller = new AbortController();
    const abort = () => controller.abort(signal.reason);
    if (signal?.aborted) abort();
    else signal?.addEventListener("abort", abort, { once: true });
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);
    const token = getToken();
    try {
      const response = await fetcher(
        `${baseUrl.replace(/\/$/, "")}${path}${search.size ? `?${search}` : ""}`,
        {
          method,
          signal: controller.signal,
          headers: {
            Accept: "application/json",
            ...(body !== undefined
              ? { "Content-Type": "application/json" }
              : {}),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
        },
      );
      const responseText = response.status === 204 ? "" : await response.text();
      let content = null;
      if (responseText.trim()) {
        try {
          content = JSON.parse(responseText);
        } catch {
          // 성공 응답이라도 잘못된 JSON을 빈 응답으로 취급하지 않습니다.
        }
      }
      if (!response.ok) {
        if (response.status === 401) onUnauthorized();
        throw new ApiError(
          response.status,
          content?.code || "HTTP_ERROR",
          typeof content?.message === "string"
            ? content.message
            : "요청을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.",
        );
      }
      if (
        response.status !== 204 &&
        content === null &&
        !(allowEmptyResponse && !responseText.trim())
      )
        throw new ApiError(
          response.status,
          "INVALID_RESPONSE",
          "서버 응답을 읽지 못했어요.",
        );
      return content;
    } catch (error) {
      if (signal?.aborted) throw error;
      if (timedOut)
        throw new ApiError(
          0,
          "TIMEOUT",
          "응답이 늦어지고 있어요. 다시 시도해 주세요.",
        );
      if (error instanceof ApiError) throw error;
      throw new ApiError(
        0,
        "NETWORK_ERROR",
        "서버에 연결하지 못했어요. 연결 상태를 확인하고 다시 시도해 주세요.",
      );
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
    }
  };
}
