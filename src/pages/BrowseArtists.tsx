import { Link } from 'react-router-dom';

export default function BrowseArtists() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white text-xl font-bold">G</span>
            </div>
            <span className="text-xl font-semibold text-gray-900">GigBridge</span>
          </Link>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-20 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Browse Artists</h1>
        <p className="text-xl text-gray-600 mb-8">Coming soon...</p>
        <Link
          to="/"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}
