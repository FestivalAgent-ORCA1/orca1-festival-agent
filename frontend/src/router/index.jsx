import { Routes, Route } from "react-router-dom";
import PageLayout from "../components/layout/PageLayout.jsx";
import HomePage from "../pages/HomePage.jsx";
import FestivalListPage from "../pages/FestivalListPage.jsx";
import FestivalDetailPage from "../pages/FestivalDetailPage.jsx";
import LikesPage from "../pages/LikesPage.jsx";
import UnavailablePage from "../pages/UnavailablePage.jsx";
import LoginPage from "../pages/LoginPage.jsx";
import SignupPage from "../pages/SignupPage.jsx";
import OnboardingPage from "../pages/OnboardingPage.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<PageLayout />}>
        <Route index element={<HomePage />} />
        <Route path="festivals" element={<FestivalListPage />} />
        <Route path="festivals/:contentId" element={<FestivalDetailPage />} />
        <Route path="likes" element={<LikesPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="signup" element={<SignupPage />} />
        <Route path="onboarding" element={<OnboardingPage />} />
        <Route path="*" element={<UnavailablePage />} />
      </Route>
    </Routes>
  );
}
