import {BrowserRouter, Routes, Route} from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import Dashboard from "./pages/Dashboard";

function App(){
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path = "/"
          element = {
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App;