import { useState } from "react";
import FestivalBrowser from "../components/festival/FestivalBrowser.jsx";
import FestivalPreview from "../components/festival/FestivalPreview.jsx";
export default function FestivalListPage() {
  const [previewId, setPreviewId] = useState(null);
  return (
    <>
      <div className="page-intro wrap">
        <span className="eyebrow">YOUR NEXT WEEKEND</span>
        <h1 className="display">이번엔 어디로 가볼까요?</h1>
        <p>한 번쯤 가보고 싶었던 하루를 찾아보세요.</p>
      </div>
      <FestivalBrowser onPreview={setPreviewId} />
      <FestivalPreview
        contentId={previewId}
        onNext={setPreviewId}
        onClose={() => setPreviewId(null)}
      />
    </>
  );
}
