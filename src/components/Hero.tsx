import { Palette, Music, Camera, PenTool, Sparkles } from 'lucide-react';

interface HeroProps {
  onBecomeArtistClick: () => void;
}

export default function Hero({ onBecomeArtistClick }: HeroProps) {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-blue-500 to-blue-700">
        <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-bl from-blue-600 to-transparent transform skew-x-12 origin-top-right"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-6 pt-32 pb-20">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="backdrop-blur-md bg-white/20 rounded-3xl p-12 shadow-2xl border border-white/30">
            <div className="inline-block mb-6">
              <span className="bg-white/30 backdrop-blur-sm text-white px-4 py-2 rounded-full text-sm font-medium border border-white/40">
                #1 Platform for Creative Talent
              </span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              Hire Talented Artists for Your{' '}
              <span className="text-gray-900">Creative Projects</span>
            </h1>

            <p className="text-white/90 text-lg mb-8 leading-relaxed">
              Connect with professional designers, illustrators, painters, and digital artists worldwide.
            </p>

            <div className="flex flex-wrap gap-4">
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3.5 rounded-lg font-medium transition-all shadow-lg hover:shadow-xl">
                Hire a Freelancer
              </button>
              <button
                onClick={onBecomeArtistClick}
                className="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white px-8 py-3.5 rounded-lg font-medium transition-all border border-white/40"
              >
                Become an Artist
              </button>
            </div>
          </div>

          <div className="hidden md:flex items-center justify-center relative">
            <div className="relative w-full max-w-lg h-96">
              <div className="absolute top-1/4 left-1/4 transform -translate-x-1/2 -translate-y-1/2 bg-white/20 backdrop-blur-lg rounded-full p-8 shadow-2xl border border-white/30 animate-float">
                <Palette className="w-16 h-16 text-white" />
              </div>

              <div className="absolute top-1/3 right-1/4 transform translate-x-1/2 -translate-y-1/2 bg-white/20 backdrop-blur-lg rounded-full p-8 shadow-2xl border border-white/30 animate-float-delay-1">
                <Music className="w-16 h-16 text-white" />
              </div>

              <div className="absolute bottom-1/4 left-1/3 transform -translate-x-1/2 translate-y-1/2 bg-white/20 backdrop-blur-lg rounded-full p-8 shadow-2xl border border-white/30 animate-float-delay-2">
                <Camera className="w-16 h-16 text-white" />
              </div>

              <div className="absolute bottom-1/3 right-1/3 transform translate-x-1/2 translate-y-1/2 bg-white/20 backdrop-blur-lg rounded-full p-8 shadow-2xl border border-white/30 animate-float-delay-3">
                <PenTool className="w-16 h-16 text-white" />
              </div>

              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white/30 backdrop-blur-lg rounded-full p-12 shadow-2xl border border-white/40">
                <Sparkles className="w-20 h-20 text-white" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
