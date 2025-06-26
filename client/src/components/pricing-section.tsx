import { Check, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useIntersectionObserver } from '@/hooks/use-intersection-observer';

const pricingTiers = [
  {
    name: 'Standard',
    price: '1.5%',
    description: 'Most popular for general transactions',
    features: [
      'Secure fund holding',
      'Dispute resolution',
      'Email support',
      'Basic reporting',
    ],
    popular: false,
  },
  {
    name: 'Professional',
    price: '1.0%',
    description: 'Best value for business transactions',
    features: [
      'Everything in Standard',
      'Priority support',
      'Advanced reporting',
      'Dedicated account manager',
      'API access',
    ],
    popular: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    description: 'Tailored for high-volume clients',
    features: [
      'Everything in Professional',
      'Custom fee structure',
      'White-label options',
      'SLA guarantees',
      '24/7 phone support',
    ],
    popular: false,
  },
];

export function PricingSection() {
  const { ref, isIntersecting } = useIntersectionObserver();

  const scrollToContact = () => {
    const element = document.getElementById('contact');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section ref={ref} className="relative py-20" id="pricing">
      <div className="relative z-10 max-w-7xl mx-auto px-4">
        <div className={`text-center mb-16 transition-all duration-1000 ${
          isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
        }`}>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Transparent <span className="text-accent">Pricing</span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Simple, competitive pricing with no hidden fees. Pay only when your transaction closes successfully.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {pricingTiers.map((tier, index) => (
            <div 
              key={tier.name}
              className={`glass-card rounded-2xl p-8 hover-lift transition-all duration-700 ${
                tier.popular ? 'border-2 border-accent relative' : ''
              } ${
                isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
              }`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-accent text-white px-4 py-1 rounded-full text-sm font-semibold flex items-center">
                    <Star className="w-4 h-4 mr-1" />
                    Most Popular
                  </span>
                </div>
              )}
              
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-2">{tier.name}</h3>
                <div className="text-4xl font-bold text-accent mb-2">{tier.price}</div>
                <p className="text-gray-300">{tier.description}</p>
              </div>
              
              <ul className="space-y-4 mb-8">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-center">
                    <Check className="w-5 h-5 text-accent mr-3 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <Button 
                onClick={tier.name === 'Enterprise' ? scrollToContact : scrollToContact}
                className={`w-full py-3 font-semibold transition-all ${
                  tier.popular 
                    ? 'bg-accent hover:bg-accent/90 text-white' 
                    : tier.name === 'Enterprise'
                    ? 'border-2 border-accent text-accent hover:bg-accent hover:text-white bg-transparent'
                    : 'bg-accent hover:bg-accent/90 text-white'
                }`}
                variant={tier.name === 'Enterprise' ? 'outline' : 'default'}
              >
                {tier.name === 'Enterprise' ? 'Contact Sales' : 'Get Started'}
              </Button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
