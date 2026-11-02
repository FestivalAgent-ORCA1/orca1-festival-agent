import { useCallback } from "react";
import { repository } from "../../api/repository.js";
import { useResource } from "../../hooks/useResource.js";
import Modal from "../common/Modal.jsx";
import Loading from "../common/Loading.jsx";
import ErrorState from "../common/ErrorState.jsx";
import DetailContent from "./DetailContent.jsx";

export default function FestivalPreview({ contentId, onClose, onNext }) {
  const resource = useResource(
    useCallback(
      async (signal) => {
        const [festival, similar] = await Promise.all([
          repository.getDetail(contentId, signal),
          repository.getSimilar(contentId, signal).catch(() => []),
        ]);
        return { festival, similar };
      },
      [contentId],
    ),
    Boolean(contentId),
  );
  return (
    <Modal open={Boolean(contentId)} title="축제 미리 보기" onClose={onClose}>
      {resource.status === "loading" && <Loading />}
      {resource.status === "error" && (
        <ErrorState error={resource.error} onRetry={resource.retry} />
      )}
      {resource.status === "success" && (
        <DetailContent
          festival={resource.data.festival}
          preview
          next={resource.data.similar[0]}
          onNext={onNext}
          onClose={onClose}
        />
      )}
    </Modal>
  );
}
