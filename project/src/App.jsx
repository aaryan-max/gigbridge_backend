import { useState } from "react";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import SignupModal from "./components/SignupModal";
import "./App.css";

function App() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Navbar onSignup={() => setOpen(true)} />
      <Hero onSignup={() => setOpen(true)} />
      {open && <SignupModal onClose={() => setOpen(false)} />}
    </>
  );
}

export default App;
