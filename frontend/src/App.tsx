import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import HomePage from "@pages/HomePage/HomePage";
import SubmitPage from "@pages/SubmitPage/SubmitPage";
import HistoryPage from "@pages/HistoryPage/HistoryPage";

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/submit" element={<SubmitPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;