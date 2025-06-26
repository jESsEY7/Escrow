import { Shield, Twitter, Linkedin, Facebook } from 'lucide-react';
import { Link } from 'wouter';

const footerSections = [
  {
    title: 'Services',
    links: [
      'Real Estate Escrow',
      'Digital Asset Escrow',
      'Vehicle Escrow',
      'Business Escrow',
      'International Escrow',
    ],
  },
  {
    title: 'Company',
    links: [
      'About Us',
      'Security',
      'Compliance',
      'Careers',
      'Press',
    ],
  },
  {
    title: 'Support',
    links: [
      'Help Center',
      'Contact Us',
      'FAQ',
      'Status',
      'API Docs',
    ],
  },
];

const socialLinks = [
  { icon: Twitter, href: '#', label: 'Twitter' },
  { icon: Linkedin, href: '#', label: 'LinkedIn' },
  { icon: Facebook, href: '#', label: 'Facebook' },
];

const legalLinks = [
  'Privacy Policy',
  'Terms of Service',
  'Cookie Policy',
];

export function Footer() {
  return (
    <footer className="relative py-16 mt-20">
      <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent" />
      <div className="relative z-10 max-w-7xl mx-auto px-4">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          {/* Company Info */}
          <div>
            <Link href="/" className="flex items-center space-x-2 mb-6 group" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
              <Shield className="h-8 w-8 text-accent transition-transform group-hover:scale-110" />
              <span className="text-xl font-bold">SecureEscrow</span>
            </Link>
            <p className="text-gray-300 mb-6">
              Trusted escrow services protecting transactions worldwide with professional security and reliability.
            </p>
            <div className="flex space-x-4">
              {socialLinks.map((social) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.label}
                    href={social.href}
                    className="glass w-10 h-10 rounded-lg flex items-center justify-center hover:bg-accent/20 transition-colors"
                    aria-label={social.label}
                  >
                    <Icon className="w-5 h-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Footer Sections */}
          {footerSections.map((section) => (
            <div key={section.title}>
              <h4 className="font-semibold text-lg mb-6">{section.title}</h4>
              <ul className="space-y-3 text-gray-300">
                {section.links.map((link) => (
                  <li key={link}>
                    <a href="#" className="hover:text-accent transition-colors">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-white/10 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm">
              © 2024 SecureEscrow. All rights reserved. Licensed and regulated escrow services.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              {legalLinks.map((link) => (
                <a
                  key={link}
                  href="#"
                  className="text-gray-400 hover:text-accent text-sm transition-colors"
                >
                  {link}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
