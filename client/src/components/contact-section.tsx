import { useState } from 'react';
import { Phone, Mail, MapPin, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useIntersectionObserver } from '@/hooks/use-intersection-observer';
import { useParallaxTransform } from '@/hooks/use-parallax';
import { useMutation } from '@tanstack/react-query';
import { apiRequest } from '@/lib/queryClient';

interface ContactForm {
  firstName: string;
  lastName: string;
  email: string;
  transactionType: string;
  transactionValue: string;
  message: string;
}

export function ContactSection() {
  const { ref, isIntersecting } = useIntersectionObserver();
  const parallaxTransform = useParallaxTransform(0.2);
  const { toast } = useToast();
  
  const [formData, setFormData] = useState<ContactForm>({
    firstName: '',
    lastName: '',
    email: '',
    transactionType: '',
    transactionValue: '',
    message: '',
  });

  const contactMutation = useMutation({
    mutationFn: async (data: ContactForm) => {
      return await apiRequest('POST', '/api/contact', data);
    },
    onSuccess: () => {
      toast({
        title: 'Message sent successfully!',
        description: 'We will contact you shortly to discuss your transaction.',
      });
      setFormData({
        firstName: '',
        lastName: '',
        email: '',
        transactionType: '',
        transactionValue: '',
        message: '',
      });
    },
    onError: () => {
      toast({
        title: 'Error sending message',
        description: 'Please try again or contact us directly.',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    contactMutation.mutate(formData);
  };

  const handleChange = (field: keyof ContactForm, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const contactInfo = [
    {
      icon: Phone,
      title: 'Phone',
      content: '1-800-ESCROW-1',
    },
    {
      icon: Mail,
      title: 'Email',
      content: 'support@secureescrow.com',
    },
    {
      icon: MapPin,
      title: 'Address',
      content: '123 Financial District\nSan Francisco, CA 94111',
    },
  ];

  const businessHours = [
    { day: 'Monday - Friday', hours: '8:00 AM - 6:00 PM PST' },
    { day: 'Saturday', hours: '9:00 AM - 3:00 PM PST' },
    { day: 'Sunday', hours: 'Closed' },
  ];

  return (
    <section ref={ref} className="relative py-20" id="contact">
      {/* Parallax Background */}
      <div 
        className="absolute inset-0 parallax-bg opacity-5"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1497366754035-f200968a6e72?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2069&q=80')`,
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
            Start Your Secure <span className="text-accent">Transaction</span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Ready to protect your next transaction? Contact our expert team or start your escrow process today.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Contact Form */}
          <div className={`glass-card rounded-2xl p-8 transition-all duration-1000 ${
            isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
          }`}>
            <h3 className="text-2xl font-bold mb-6">Get Started</h3>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">First Name</label>
                  <Input
                    type="text"
                    value={formData.firstName}
                    onChange={(e) => handleChange('firstName', e.target.value)}
                    className="bg-white/10 border-white/20 focus:border-accent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Last Name</label>
                  <Input
                    type="text"
                    value={formData.lastName}
                    onChange={(e) => handleChange('lastName', e.target.value)}
                    className="bg-white/10 border-white/20 focus:border-accent"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Email</label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  className="bg-white/10 border-white/20 focus:border-accent"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Transaction Type</label>
                <Select value={formData.transactionType} onValueChange={(value) => handleChange('transactionType', value)}>
                  <SelectTrigger className="bg-white/10 border-white/20 focus:border-accent">
                    <SelectValue placeholder="Select transaction type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="real-estate">Real Estate</SelectItem>
                    <SelectItem value="digital-assets">Digital Assets</SelectItem>
                    <SelectItem value="vehicles">Vehicles</SelectItem>
                    <SelectItem value="business">Business</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Transaction Value</label>
                <Input
                  type="text"
                  placeholder="$0.00"
                  value={formData.transactionValue}
                  onChange={(e) => handleChange('transactionValue', e.target.value)}
                  className="bg-white/10 border-white/20 focus:border-accent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Message</label>
                <Textarea
                  rows={4}
                  value={formData.message}
                  onChange={(e) => handleChange('message', e.target.value)}
                  className="bg-white/10 border-white/20 focus:border-accent"
                  placeholder="Tell us about your transaction..."
                />
              </div>
              
              <Button 
                type="submit" 
                disabled={contactMutation.isPending}
                className="w-full bg-accent hover:bg-accent/90 text-white py-3 font-semibold hover-lift"
              >
                <Send className="w-5 h-5 mr-2" />
                {contactMutation.isPending ? 'Sending...' : 'Start My Transaction'}
              </Button>
            </form>
          </div>

          {/* Contact Information */}
          <div className="space-y-8">
            <div className={`glass-card rounded-xl p-8 transition-all duration-1000 ${
              isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
            }`} style={{ animationDelay: '200ms' }}>
              <h3 className="text-2xl font-bold mb-6">Contact Information</h3>
              <div className="space-y-6">
                {contactInfo.map((info, index) => {
                  const Icon = info.icon;
                  return (
                    <div key={info.title} className="flex items-center">
                      <div className="bg-accent/20 w-12 h-12 rounded-lg flex items-center justify-center mr-4">
                        <Icon className="w-6 h-6 text-accent" />
                      </div>
                      <div>
                        <h4 className="font-semibold">{info.title}</h4>
                        <p className="text-gray-300 whitespace-pre-line">{info.content}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className={`glass-card rounded-xl p-8 transition-all duration-1000 ${
              isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
            }`} style={{ animationDelay: '300ms' }}>
              <h3 className="text-xl font-bold mb-4">Business Hours</h3>
              <div className="space-y-2 text-gray-300">
                {businessHours.map((schedule) => (
                  <div key={schedule.day} className="flex justify-between">
                    <span>{schedule.day}</span>
                    <span>{schedule.hours}</span>
                  </div>
                ))}
              </div>
              <p className="text-sm text-gray-400 mt-4">
                Emergency support available 24/7 for active transactions
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
