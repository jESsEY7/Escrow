import { FileText, CreditCard, Truck, CheckCircle, Rocket } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useIntersectionObserver } from '@/hooks/use-intersection-observer';
import { useParallaxTransform } from '@/hooks/use-parallax';

const steps = [
  {
    number: '01',
    icon: FileText,
    title: 'Create Agreement',
    description: 'Set up your escrow agreement with clear terms, conditions, and milestones for all parties involved.',
  },
  {
    number: '02',
    icon: CreditCard,
    title: 'Secure Payment',
    description: 'Buyer deposits funds into our secure escrow account, ensuring seller confidence before delivery begins.',
  },
  {
    number: '03',
    icon: Truck,
    title: 'Delivery & Inspection',
    description: 'Seller delivers goods or services. Buyer has the agreed inspection period to verify everything meets expectations.',
  },
  {
    number: '04',
    icon: CheckCircle,
    title: 'Release Funds',
    description: 'Once buyer approves, we release the funds to seller. If issues arise, we provide professional dispute resolution.',
  },
];

export function HowItWorksSection() {
  const { ref, isIntersecting } = useIntersectionObserver();
  const parallaxTransform = useParallaxTransform(0.2);

  const scrollToContact = () => {
    const element = document.getElementById('contact');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section ref={ref} className="relative py-20" id="how-it-works">
      {/* Parallax Background */}
      <div 
        className="absolute inset-0 parallax-bg opacity-5"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1563013544-824ae1b704d3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80')`,
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
            How <span className="text-accent">It Works</span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Our streamlined escrow process ensures secure transactions with complete transparency and professional handling at every step.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div 
                key={step.number}
                className={`text-center transition-all duration-700 ${
                  isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
                }`}
                style={{ animationDelay: `${index * 150}ms` }}
              >
                <div className="glass-card rounded-2xl p-8 mb-6 hover-lift relative">
                  <div className="bg-accent/20 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                    <span className="text-2xl font-bold text-accent">{step.number}</span>
                  </div>
                  <div className="bg-primary/20 w-16 h-16 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <Icon className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-4">{step.title}</h3>
                  <p className="text-gray-300">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        <div className={`text-center transition-all duration-1000 ${
          isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
        }`} style={{ animationDelay: '600ms' }}>
          <Button 
            onClick={scrollToContact}
            className="bg-accent hover:bg-accent/90 text-white px-8 py-4 text-lg font-semibold hover-lift"
            size="lg"
          >
            <Rocket className="w-5 h-5 mr-2" />
            Start Your Escrow Today
          </Button>
        </div>
      </div>
    </section>
  );
}
