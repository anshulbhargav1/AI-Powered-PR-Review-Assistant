import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { Reviews } from "./pages/Reviews";
import { ReviewDetail } from "./pages/ReviewDetail";
import { Repositories } from "./pages/Repositories";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Dashboard />} />
        <Route path="reviews" element={<Reviews />} />
        <Route path="reviews/:id" element={<ReviewDetail />} />
        <Route path="repositories" element={<Repositories />} />
      </Route>
    </Routes>
  );
}
