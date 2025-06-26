import { useEffect, useState } from 'react';
import { Play, Info, Lock, Handshake } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useParallaxTransform } from '@/hooks/use-parallax';

export function HeroSection() {
  const [isVisible, setIsVisible] = useState(false);
  const parallaxTransform = useParallaxTransform(0.5);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden" id="hero">
      {/* Parallax Background */}
      <div 
        className="absolute inset-0 parallax-bg"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1560472354-b33ff0c44a43?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1926&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
          transform: parallaxTransform,
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-r from-slate-900/80 to-blue-900/60" />
      
      <div className="relative z-10 max-w-6xl mx-auto px-4 text-center">
        <div className={`glass-card rounded-2xl p-8 md:p-12 transition-all duration-1000 ${
          isVisible ? 'animate-fade-in' : 'opacity-0'
        }`}>
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Secure <span className="text-accent">Escrow Services</span><br />
            You Can Trust
          </h1>
          <p className="text-xl md:text-2xl mb-8 text-gray-200 max-w-3xl mx-auto">
            Protect your transactions with our professional escrow services. Safe, secure, and trusted by thousands of businesses worldwide.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              onClick={() => scrollToSection('contact')}
              className="bg-accent hover:bg-accent/90 text-white px-8 py-4 text-lg font-semibold hover-lift"
              size="lg"
            >
              <Play className="w-5 h-5 mr-2" />
              Start Your Transaction
            </Button>
            <Button 
              onClick={() => scrollToSection('how-it-works')}
              variant="outline"
              className="glass border-white/20 hover:bg-white/20 text-white px-8 py-4 text-lg font-semibold hover-lift"
              size="lg"
            >
              <Info className="w-5 h-5 mr-2" />
              Learn More
            </Button>
          </div>
        </div>
      </div>

      {/* Floating Elements */}
      <div className="absolute top-1/4 left-4 md:left-10 animate-float">
        <div className="glass rounded-full p-4">
          <Lock className="w-8 h-8 text-accent" />
        </div>
      </div>
      <div className="absolute top-1/3 right-4 md:right-10 animate-float" style={{ animationDelay: '-2s' }}>
        <div className="glass rounded-full p-4">
          <Handshake className="w-8 h-8 text-accent" />
        </div>
      </div>
    </section>
  );
}
