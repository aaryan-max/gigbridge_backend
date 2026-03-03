import { Link } from 'react-router-dom';

interface NavbarProps {
  onSignUpClick: () => void;
}

export default function Navbar({ onSignUpClick }: NavbarProps) {
  return (
    <nav className="fixed top-0 left-0 right-0 bg-white shadow-sm z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white text-xl font-bold">G</span>
            </div>
            <span className="text-xl font-semibold text-gray-900">GigBridge</span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link to="/" className="text-gray-600 hover:text-gray-900 transition-colors">
              Home
            </Link>
            <Link to="/browse-artists" className="text-gray-600 hover:text-gray-900 transition-colors">
              Browse Artists
            </Link>
            <Link to="/how-it-works" className="text-gray-600 hover:text-gray-900 transition-colors">
              How It Works
            </Link>
            <Link to="/contact" className="text-gray-600 hover:text-gray-900 transition-colors">
              Contact
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              Login
            </Link>
            <button
              onClick={onSignUpClick}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
            >
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
