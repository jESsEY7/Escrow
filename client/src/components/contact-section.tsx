import React, { useState, useCallback, useMemo } from 'react';
import { Phone, Mail, MapPin, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useIntersectionObserver } from '@/hooks/use-intersection-observer';
import { useParallaxTransform } from '@/hooks/use-parallax'; // Assuming this hook is well-defined
import { useMutation } from '@tanstack/react-query';
import { apiRequest } from '@/lib/queryClient'; // Ensure apiRequest handles errors gracefully

// --- Interfaces ---

/**
 * Defines the structure for the contact form data.
 */
interface ContactFormData {
  firstName: string;
  lastName: string;
  email: string;
  transactionType: string; // Consider making this an enum or predefined list for type safety
  transactionValue: string; // Could be a number type if strictly numeric, or a string for flexible input
  message: string;
}

/**
 * Defines the structure for contact information details.
 */
interface ContactInfoItem {
  icon: React.ElementType; // Type for LucideReact icons
  title: string;
  content: string;
}

/**
 * Defines the structure for business hours.
 */
interface BusinessHoursItem {
  day: string;
  hours: string;
}

// --- Constants and Configuration ---

// Initial state for the contact form to ensure consistency.
const INITIAL_FORM_STATE: ContactFormData = {
  firstName: '',
  lastName: '',
  email: '',
  transactionType: '',
  transactionValue: '',
  message: '',
};

// Data for contact information, using useMemo for stability if needed in other contexts.
const CONTACT_INFO: ContactInfoItem[] = [
  {
    icon: Phone,
    title: 'Phone',
    content: '+254-759-589-107 ESCROW-1',
  },
  {
    icon: Mail,
    title: 'Email',
    content: 'support@secureescrow.com',
  },
  {
    icon: MapPin,
    title: 'Address',
    content: '00100 Bunyala District\nNairobi, KE 00200',
  },
];

// Data for business hours.
const BUSINESS_HOURS: BusinessHoursItem[] = [
  { day: 'Monday - Friday', hours: '8:00 AM - 6:00 PM PST' },
  { day: 'Saturday', hours: '9:00 AM - 3:00 PM PST' },
  { day: 'Sunday', hours: 'Closed' },
];

// --- ContactSection Component ---

/**
 * Renders a comprehensive contact section, including a form,
 * contact details, and business hours. Features include parallax background
 * and entrance animations.
 */
export function ContactSection() {
  const { ref, isIntersecting } = useIntersectionObserver({ threshold: 0.1 });
  const parallaxTransform = useParallaxTransform(0.2);
  const { toast } = useToast();

  const [formData, setFormData] = useState<ContactFormData>(INITIAL_FORM_STATE);

  // Mutation for sending contact form data
  const contactMutation = useMutation({
    mutationFn: async (data: ContactFormData) => {
      // It's good practice to log or provide more detailed error handling here if apiRequest fails.
      return await apiRequest('POST', '/api/contact', data);
    },
    onSuccess: () => {
      toast({
        title: 'Message sent successfully!',
        description: 'We will contact you shortly to discuss your transaction.',
      });
      setFormData(INITIAL_FORM_STATE); // Reset form on successful submission
    },
    onError: (error) => {
      // Log the actual error for debugging, but provide a generic message to the user
      console.error('Error sending contact message:', error);
      toast({
        title: 'Error sending message',
        description: 'Please try again or contact us directly. Our team is ready to assist.',
        variant: 'destructive',
      });
    },
  });

  /**
   * Handles form submission.
   * @param e - The form event.
   */
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    contactMutation.mutate(formData);
  }, [formData, contactMutation]);

  /**
   * Handles changes for input fields, updating the form data state.
   * Uses useCallback for performance optimization with React.
   * @param field - The name of the form field being changed.
   * @param value - The new value of the form field.
   */
  const handleChange = useCallback((field: keyof ContactFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  return (
    <section ref={ref} className="relative py-20 overflow-hidden" id="contact">
      {/* Parallax Background - positioned absolutely to cover the section */}
      <div
        className="absolute inset-0 parallax-bg opacity-5"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1497366754035-f200968a6e72?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2069&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed', // Enables the parallax scrolling effect
          transform: parallaxTransform, // Apply parallax transformation
        }}
        aria-hidden="true" // Indicate to screen readers that this is a decorative element
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className={`text-center mb-16 transition-all duration-1000 ${
          isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
        }`}>
          <h2 className="text-4xl md:text-5xl font-extrabold mb-6 text-white leading-tight">
            Start Your <span className="text-accent">Secure Transaction</span> Today
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Ready to protect your valuable assets? Our expert team is here to guide you through a seamless and secure escrow process.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Contact Form */}
          <div className={`glass-card rounded-2xl p-8 shadow-lg transition-all duration-1000 ${
            isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
          }`}>
            <h3 className="text-3xl font-bold mb-8 text-white">Get Started With Us</h3>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="firstName" className="block text-sm font-medium mb-2 text-gray-200">First Name</label>
                  <Input
                    id="firstName"
                    type="text"
                    value={formData.firstName}
                    onChange={(e) => handleChange('firstName', e.target.value)}
                    className="bg-white/10 border-white/20 text-white placeholder-gray-400 focus:border-accent focus:ring-accent"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="lastName" className="block text-sm font-medium mb-2 text-gray-200">Last Name</label>
                  <Input
                    id="lastName"
                    type="text"
                    value={formData.lastName}
                    onChange={(e) => handleChange('lastName', e.target.value)}
                    className="bg-white/10 border-white/20 text-white placeholder-gray-400 focus:border-accent focus:ring-accent"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label htmlFor="email" className="block text-sm font-medium mb-2 text-gray-200">Email Address</label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  className="bg-white/10 border-white/20 text-white placeholder-gray-400 focus:border-accent focus:ring-accent"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="transactionType" className="block text-sm font-medium mb-2 text-gray-200">Type of Transaction</label>
                <Select value={formData.transactionType} onValueChange={(value) => handleChange('transactionType', value)}>
                  <SelectTrigger id="transactionType" className="bg-white/10 border-white/20 text-white placeholder-gray-400 focus:border-accent focus:ring-accent">
                    <SelectValue placeholder="Select transaction type" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700 text-white">
                    <SelectItem value="real-estate">Real Estate</SelectItem>
                    <SelectItem value="digital-assets">Digital Assets</SelectItem>
                    <SelectItem value="vehicles">Vehicles</SelectItem>
                    <SelectItem value="business">Business Acquisition</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label htmlFor="transactionValue" className="block text-sm font-medium mb-2 text-gray-200">Estimated Transaction Value</label>
                <Input
                  id="transactionValue"
                  type="text" // Keep as text to allow for various currency formats/descriptions
                  placeholder="e.g., $1,000,000 or Ksh 10,000,000"
                  value={formData.transactionValue}
                  onChange={(e) => handleChange('transactionValue', e.target.value)}
                  className="bg-white/10 border-white/20 text-white placeholder-gray-400 focus:border-accent focus:ring-accent"
                />
              </div>
              
              <div>
                <label htmlFor="message" className="block text-sm font-medium mb-2 text-gray-200">Your Message</label>
                <Textarea
                  id="message"
                  rows={4}
                  value={formData.message}
                  onChange={(e) => handleChange('message', e.target.value)}
                  className="bg-white/10 border-white/20 text-white placeholder-gray-400 focus:border-accent focus:ring-accent"
                  placeholder="Provide details about your escrow needs or any questions you have."
                />
              </div>
              
              <Button 
                type="submit" 
                disabled={contactMutation.isPending}
                className="w-full bg-accent hover:bg-accent/90 text-white py-3 font-semibold text-lg flex items-center justify-center transition-all duration-300 hover-lift"
              >
                <Send className="w-5 h-5 mr-2" />
                {contactMutation.isPending ? 'Sending Request...' : 'Start My Secure Transaction'}
              </Button>
            </form>
          </div>

          {/* Contact Information & Business Hours */}
          <div className="space-y-8">
            {/* Contact Info Card */}
            <div className={`glass-card rounded-2xl p-8 shadow-lg transition-all duration-1000 ${
              isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
            }`} style={{ animationDelay: '200ms' }}>
              <h3 className="text-3xl font-bold mb-6 text-white">Reach Out to Us</h3>
              <div className="space-y-6">
                {CONTACT_INFO.map((info) => {
                  const Icon = info.icon; // Destructure Icon component
                  return (
                    <div key={info.title} className="flex items-center">
                      <div className="bg-accent/20 w-12 h-12 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                        <Icon className="w-6 h-6 text-accent" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-white">{info.title}</h4>
                        <p className="text-gray-300 whitespace-pre-line">{info.content}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Business Hours Card */}
            <div className={`glass-card rounded-2xl p-8 shadow-lg transition-all duration-1000 ${
              isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
            }`} style={{ animationDelay: '300ms' }}>
              <h3 className="text-3xl font-bold mb-6 text-white">Our Business Hours</h3>
              <div className="space-y-3 text-gray-300">
                {BUSINESS_HOURS.map((schedule) => (
                  <div key={schedule.day} className="flex justify-between items-center border-b border-gray-700 pb-2 last:border-b-0">
                    <span className="font-medium text-gray-200">{schedule.day}</span>
                    <span>{schedule.hours}</span>
                  </div>
                ))}
              </div>
              <p className="text-sm text-gray-400 mt-6">
                For urgent matters or active transactions, **emergency support is available 24/7**.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
