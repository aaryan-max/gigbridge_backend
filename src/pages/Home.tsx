import { useState } from 'react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import SignupModal from '../components/SignupModal';

export default function Home() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div>
      <Navbar onSignUpClick={() => setIsModalOpen(true)} />
      <Hero onBecomeArtistClick={() => setIsModalOpen(true)} />
      <SignupModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}
