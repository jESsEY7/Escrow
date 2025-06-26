import { Star, Users, TrendingUp, Heart } from 'lucide-react';
import { useIntersectionObserver } from '@/hooks/use-intersection-observer';
import { useParallaxTransform } from '@/hooks/use-parallax';

const testimonials = [
  {
    name: 'David Johnson',
    company: 'Real Estate Developer',
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=80&q=80',
    content: '"SecureEscrow made our $2M property transaction completely seamless. Their professionalism and security gave us complete peace of mind throughout the entire process."',
  },
  {
    name: 'Sarah Chen',
    company: 'Tech Startup Founder',
    image: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=80&q=80',
    content: '"Used SecureEscrow for our domain acquisition. The process was transparent, secure, and incredibly professional. Highly recommend for any digital asset transactions."',
  },
  {
    name: 'Michael Rodriguez',
    company: 'Business Owner',
    image: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=80&q=80',
    content: '"Outstanding service! They handled our international business acquisition with expertise and care. The security measures and communication were top-notch throughout."',
  },
];

const stats = [
  { icon: TrendingUp, value: '50,000+', label: 'Transactions' },
  { icon: Users, value: '$2.5B+', label: 'Protected' },
  { icon: Heart, value: '99.8%', label: 'Satisfaction' },
];

export function TestimonialsSection() {
  const { ref, isIntersecting } = useIntersectionObserver();
  const parallaxTransform = useParallaxTransform(0.2);

  return (
    <section ref={ref} className="relative py-20">
      {/* Parallax Background */}
      <div 
        className="absolute inset-0 parallax-bg opacity-5"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1521791136064-7986c2920216?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2069&q=80')`,
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
            What Our <span className="text-accent">Clients Say</span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Trusted by thousands of businesses and individuals worldwide for secure, reliable escrow services.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {testimonials.map((testimonial, index) => (
            <div 
              key={testimonial.name}
              className={`glass-card rounded-xl p-8 hover-lift transition-all duration-700 ${
                isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
              }`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-center mb-6">
                <img 
                  src={testimonial.image} 
                  alt={`${testimonial.name} testimonial`} 
                  className="w-12 h-12 rounded-full mr-4 object-cover"
                />
                <div>
                  <h4 className="font-semibold">{testimonial.name}</h4>
                  <p className="text-sm text-gray-400">{testimonial.company}</p>
                </div>
              </div>
              <div className="flex text-accent mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-current" />
                ))}
              </div>
              <p className="text-gray-300">{testimonial.content}</p>
            </div>
          ))}
        </div>

        <div className={`text-center transition-all duration-1000 ${
          isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
        }`} style={{ animationDelay: '300ms' }}>
          <div className="glass-card rounded-lg p-6 inline-block">
            <div className="flex items-center space-x-8">
              {stats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <div key={stat.label} className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <Icon className="w-6 h-6 text-accent mr-2" />
                      <div className="text-3xl font-bold text-accent">{stat.value}</div>
                    </div>
                    <div className="text-sm text-gray-400">{stat.label}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
