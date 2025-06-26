import { Shield, University, Award, Clock, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useIntersectionObserver } from '@/hooks/use-intersection-observer';
import { useParallaxTransform } from '@/hooks/use-parallax';

const securityFeatures = [
  {
    icon: Shield,
    title: '256-bit SSL Encryption',
    description: 'Bank-grade security protocols',
  },
  {
    icon: University,
    title: 'FDIC Insured',
    description: 'Up to $250,000 protection',
  },
  {
    icon: Award,
    title: 'Licensed & Regulated',
    description: 'State and federal compliance',
  },
  {
    icon: Clock,
    title: '24/7 Monitoring',
    description: 'Continuous security oversight',
  },
];

export function TrustSection() {
  const { ref, isIntersecting } = useIntersectionObserver();
  const parallaxTransform = useParallaxTransform(0.2);

  return (
    <section ref={ref} className="relative py-20">
      {/* Parallax Background */}
      <div 
        className="absolute inset-0 parallax-bg opacity-5"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1497366216548-37526070297c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2069&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
          transform: parallaxTransform,
        }}
      />
      
      <div className="relative z-10 max-w-7xl mx-auto px-4">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className={`transition-all duration-1000 ${
            isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
          }`}>
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Your Security is Our <span className="text-accent">Priority</span>
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              We employ bank-level security measures and are licensed and regulated to ensure your transactions are protected with the highest standards of safety and compliance.
            </p>

            <div className="grid grid-cols-2 gap-6 mb-8">
              {securityFeatures.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div 
                    key={feature.title}
                    className={`glass-card rounded-lg p-6 hover-lift transition-all duration-700 ${
                      isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
                    }`}
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <Icon className="w-8 h-8 text-accent mb-4" />
                    <h3 className="font-semibold mb-2">{feature.title}</h3>
                    <p className="text-sm text-gray-300">{feature.description}</p>
                  </div>
                );
              })}
            </div>

            <Button 
              className="bg-primary hover:bg-primary/90 text-white px-8 py-3 font-semibold hover-lift"
            >
              <Lock className="w-5 h-5 mr-2" />
              Learn About Our Security
            </Button>
          </div>

          <div className={`relative transition-all duration-1000 ${
            isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
          }`} style={{ animationDelay: '200ms' }}>
            <div className="glass-card rounded-2xl p-8">
              <img 
                src="https://images.unsplash.com/photo-1563013544-824ae1b704d3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=800&q=80" 
                alt="Digital security and encryption visualization" 
                className="rounded-xl w-full h-auto"
              />
            </div>
            
            {/* Floating trust badges */}
            <div className="absolute -bottom-6 -left-6 glass rounded-lg p-4 animate-float">
              <div className="flex items-center space-x-2">
                <Award className="text-accent w-6 h-6" />
                <span className="font-semibold text-sm">A+ Rating</span>
              </div>
            </div>
            
            <div className="absolute -top-6 -right-6 glass rounded-lg p-4 animate-float" style={{ animationDelay: '-3s' }}>
              <div className="flex items-center space-x-2">
                <Shield className="text-accent w-6 h-6" />
                <span className="font-semibold text-sm">50K+ Customers</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
