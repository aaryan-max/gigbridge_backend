import { X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface SignupModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SignupModal({ isOpen, onClose }: SignupModalProps) {
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleFreelancerClick = () => {
    navigate('/signup/freelancer');
    onClose();
  };

  const handleClientClick = () => {
    navigate('/signup/client');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      ></div>

      <div className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 p-8 md:p-12">
        <button
          onClick={onClose}
          className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={24} />
        </button>

        <div className="mb-8">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
            Welcome to GigBridge
          </h2>
          <p className="text-gray-600 text-lg">
            Choose how you'd like to continue
          </p>
        </div>

        <div className="space-y-4">
          <button
            onClick={handleFreelancerClick}
            className="w-full text-left p-8 rounded-xl border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50/50 transition-all group"
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
              I'm a Freelancer
            </h3>
            <p className="text-gray-600">Create your freelancer account</p>
          </button>

          <button
            onClick={handleClientClick}
            className="w-full text-left p-8 rounded-xl border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50/50 transition-all group"
          >
            <h3 className="text-2xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
              I'm a Client
            </h3>
            <p className="text-gray-600">Create your client account</p>
          </button>
        </div>
      </div>
    </div>
  );
}
