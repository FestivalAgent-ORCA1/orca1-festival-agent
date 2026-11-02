import { useState } from "react";
import Hero from "../components/festival/Hero.jsx";
import FestivalBrowser from "../components/festival/FestivalBrowser.jsx";
import SavedCollection from "../components/festival/SavedCollection.jsx";
import FestivalPreview from "../components/festival/FestivalPreview.jsx";
import Recommendations from "../components/festival/Recommendations.jsx";
export default function HomePage() {
  const [previewId, setPreviewId] = useState(null);
  return (
    <>
      <Hero onPreview={setPreviewId} />
      <Recommendations onPreview={setPreviewId} />
      <FestivalBrowser home onPreview={setPreviewId} />
      <SavedCollection />
      <FestivalPreview
        contentId={previewId}
        onNext={setPreviewId}
        onClose={() => setPreviewId(null)}
      />
    </>
  );
}
