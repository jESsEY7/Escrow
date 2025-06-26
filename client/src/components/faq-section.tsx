import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { useIntersectionObserver } from '@/hooks/use-intersection-observer';

const faqs = [
  {
    question: 'What is escrow and how does it work?',
    answer: 'Escrow is a financial arrangement where a neutral third party holds and regulates payment of funds required for two parties involved in a given transaction. It helps make transactions more secure by keeping the payment in a secure escrow account which is only released when all terms of an agreement are met.',
  },
  {
    question: 'How long does the escrow process take?',
    answer: 'The duration varies by transaction type. Simple transactions can be completed in 1-3 business days, while complex deals like real estate or business acquisitions may take 2-4 weeks. We work efficiently to minimize delays while ensuring all security protocols are followed.',
  },
  {
    question: 'What fees do you charge?',
    answer: 'Our fees range from 0.89% to 1.5% of the transaction value, depending on the type and complexity of the transaction. There are no hidden fees - you only pay when your transaction successfully closes. Volume discounts are available for enterprise clients.',
  },
  {
    question: 'Is my money safe with SecureEscrow?',
    answer: 'Yes, your funds are completely secure. We use bank-level security, 256-bit SSL encryption, and all funds are held in FDIC-insured accounts. We\'re licensed and regulated, providing multiple layers of protection for your transactions.',
  },
  {
    question: 'What happens if there\'s a dispute?',
    answer: 'We provide professional dispute resolution services. Our experienced team will review all documentation and work with both parties to reach a fair resolution. If needed, we can facilitate mediation or arbitration processes to resolve conflicts efficiently.',
  },
];

export function FAQSection() {
  const [openItems, setOpenItems] = useState<number[]>([]);
  const { ref, isIntersecting } = useIntersectionObserver();

  const toggleFAQ = (index: number) => {
    setOpenItems(prev => 
      prev.includes(index) 
        ? prev.filter(item => item !== index)
        : [...prev, index]
    );
  };

  return (
    <section ref={ref} className="relative py-20" id="faq">
      <div className="relative z-10 max-w-4xl mx-auto px-4">
        <div className={`text-center mb-16 transition-all duration-1000 ${
          isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
        }`}>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Frequently Asked <span className="text-accent">Questions</span>
          </h2>
          <p className="text-xl text-gray-300">
            Find answers to common questions about our escrow services and processes.
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div 
              key={index}
              className={`glass-card rounded-lg transition-all duration-700 ${
                isIntersecting ? 'animate-slide-up' : 'opacity-0 translate-y-20'
              }`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <button
                className="w-full p-6 text-left flex justify-between items-center hover:bg-white/5 transition-colors rounded-lg"
                onClick={() => toggleFAQ(index)}
              >
                <span className="font-semibold text-lg pr-4">{faq.question}</span>
                <ChevronDown 
                  className={`w-5 h-5 text-accent transition-transform duration-200 flex-shrink-0 ${
                    openItems.includes(index) ? 'rotate-180' : ''
                  }`}
                />
              </button>
              {openItems.includes(index) && (
                <div className="px-6 pb-6">
                  <p className="text-gray-300 leading-relaxed">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
