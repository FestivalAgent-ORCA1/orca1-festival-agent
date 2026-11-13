const postPath = (id) => `/api/posts/${encodeURIComponent(id)}`;

export function createPostsApi(request) {
  return {
    getPosts: (query, signal) => request("/api/posts", { query, signal }),
    getPost: (id, signal) => request(postPath(id), { signal }),
    createPost: (body) => request("/api/posts", { method: "POST", body }),
    updatePost: (id, body) => request(postPath(id), { method: "PUT", body }),
    deletePost: (id) => request(postPath(id), { method: "DELETE" }),
    getComments: (id, signal) => request(`${postPath(id)}/comments`, { signal }),
    createComment: (id, content) =>
      request(`${postPath(id)}/comments`, {
        method: "POST",
        body: { content },
      }),
    deleteComment: (id) =>
      request(`/api/comments/${encodeURIComponent(id)}`, { method: "DELETE" }),
  };
}
