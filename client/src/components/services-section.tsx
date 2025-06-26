import { Home, Laptop, Car, Building, Globe, Award, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useIntersectionObserver } from '@/hooks/use-intersection-observer';
import { useParallaxTransform } from '@/hooks/use-parallax';

const services = [
  {
    icon: Home,
    title: 'Real Estate Escrow',
    description: 'Secure property transactions with our comprehensive real estate escrow services, ensuring all parties are protected throughout the process.',
  },
  {
    icon: Laptop,
    title: 'Digital Asset Escrow',
    description: 'Safe handling of digital assets, domain names, and online business transactions with specialized security protocols.',
  },
  {
    icon: Car,
    title: 'Vehicle Escrow',
    description: 'Protect your automotive purchases and sales with our specialized vehicle escrow services for cars, boats, and more.',
  },
  {
    icon: Building,
    title: 'Business Escrow',
    description: 'Facilitate complex business transactions, mergers, and acquisitions with our enterprise-grade escrow solutions.',
  },
  {
    icon: Globe,
    title: 'International Escrow',
    description: 'Cross-border transaction protection with compliance to international regulations and currency exchange support.',
  },
  {
    icon: Award,
    title: 'IP & Patent Escrow',
    description: 'Secure intellectual property transactions with specialized handling of patents, trademarks, and licensing agreements.',
  },
];

export function ServicesSection() {
  const { ref, isIntersecting } = useIntersectionObserver();
  const parallaxTransform = useParallaxTransform(0.3);

  return (
    <section ref={ref} className="relative py-20" id="services">
      {/* Parallax Background */}
      <div 
        className="absolute inset-0 parallax-bg opacity-10"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1974&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
          transform: parallaxTransform,
        }}
      />
      
      <div className="relative z-10 max-w-7xl mx-auto px-4">
        <div className={`text-center mb-16 transition-all duration-1000 ${
          isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
        }`}>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Our <span className="text-accent">Services</span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Comprehensive escrow solutions tailored to meet your business needs with the highest level of security and professionalism.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {services.map((service, index) => {
            const Icon = service.icon;
            return (
              <div 
                key={service.title}
                className={`glass-card rounded-xl p-8 hover-lift transition-all duration-700 ${
                  isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
                }`}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="bg-accent/20 w-16 h-16 rounded-lg flex items-center justify-center mb-6">
                  <Icon className="w-8 h-8 text-accent" />
                </div>
                <h3 className="text-2xl font-semibold mb-4">{service.title}</h3>
                <p className="text-gray-300 mb-6">{service.description}</p>
                <Button 
                  variant="link" 
                  className="text-accent hover:text-accent/80 font-semibold p-0"
                >
                  Learn More <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
