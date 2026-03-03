import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login';
import SignupFreelancer from './pages/SignupFreelancer';
import SignupClient from './pages/SignupClient';
import BrowseArtists from './pages/BrowseArtists';
import HowItWorks from './pages/HowItWorks';
import Contact from './pages/Contact';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup/freelancer" element={<SignupFreelancer />} />
        <Route path="/signup/client" element={<SignupClient />} />
        <Route path="/browse-artists" element={<BrowseArtists />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
        <Route path="/contact" element={<Contact />} />
      </Routes>
    </Router>
  );
}

export default App;
