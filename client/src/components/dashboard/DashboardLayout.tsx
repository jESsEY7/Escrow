/**
 * Dashboard Layout Component
 * Provides consistent layout for authenticated pages
 */
import { ReactNode } from 'react';
import { Link, useLocation } from 'wouter';
import { useAuth } from '@/contexts/AuthContext';
import {
    Home,
    Briefcase,
    CreditCard,
    AlertTriangle,
    Settings,
    LogOut,
    Bell,
    User,
    Shield,
    Menu,
    X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { useState } from 'react';

interface DashboardLayoutProps {
    children: ReactNode;
}

const navigationItems = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Escrows', href: '/escrows', icon: Briefcase },
    { name: 'Transactions', href: '/transactions', icon: CreditCard },
    { name: 'Disputes', href: '/disputes', icon: AlertTriangle },
];

const adminNavItems = [
    { name: 'Admin Panel', href: '/admin', icon: Shield },
];

export function DashboardLayout({ children }: DashboardLayoutProps) {
    const { user, logout } = useAuth();
    const [location] = useLocation();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const isAdmin = user?.role === 'admin' || user?.role === 'arbitrator';
    const userInitials = user?.first_name && user?.last_name
        ? `${user.first_name[0]}${user.last_name[0]}`
        : user?.email?.substring(0, 2).toUpperCase() || 'U';

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900/50 to-slate-900">
            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`fixed top-0 left-0 z-50 h-full w-64 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                    }`}
            >
                <div className="h-full glass-card flex flex-col">
                    {/* Logo */}
                    <div className="p-6 border-b border-white/10">
                        <Link href="/dashboard">
                            <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent cursor-pointer">
                                Escrow Pro
                            </span>
                        </Link>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 p-4 space-y-2">
                        {navigationItems.map((item) => {
                            const isActive = location === item.href || location.startsWith(item.href + '/');
                            return (
                                <Link key={item.name} href={item.href}>
                                    <span
                                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer ${isActive
                                                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                                            }`}
                                    >
                                        <item.icon className="w-5 h-5" />
                                        {item.name}
                                    </span>
                                </Link>
                            );
                        })}

                        {isAdmin && (
                            <>
                                <div className="pt-4 pb-2">
                                    <span className="px-4 text-xs text-gray-500 uppercase tracking-wider">
                                        Admin
                                    </span>
                                </div>
                                {adminNavItems.map((item) => {
                                    const isActive = location === item.href;
                                    return (
                                        <Link key={item.name} href={item.href}>
                                            <span
                                                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer ${isActive
                                                        ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                                                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                                                    }`}
                                            >
                                                <item.icon className="w-5 h-5" />
                                                {item.name}
                                            </span>
                                        </Link>
                                    );
                                })}
                            </>
                        )}
                    </nav>

                    {/* User section */}
                    <div className="p-4 border-t border-white/10">
                        <div className="flex items-center gap-3 px-4 py-3">
                            <Avatar className="h-10 w-10">
                                <AvatarImage src={user?.profile_image} />
                                <AvatarFallback className="bg-blue-500/20 text-blue-400">
                                    {userInitials}
                                </AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-white truncate">
                                    {user?.first_name} {user?.last_name}
                                </p>
                                <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <div className="lg:pl-64">
                {/* Top bar */}
                <header className="sticky top-0 z-30 glass border-b border-white/10">
                    <div className="flex items-center justify-between px-4 lg:px-8 py-4">
                        {/* Mobile menu button */}
                        <button
                            className="lg:hidden p-2 rounded-lg hover:bg-white/10"
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                        >
                            {sidebarOpen ? (
                                <X className="w-6 h-6" />
                            ) : (
                                <Menu className="w-6 h-6" />
                            )}
                        </button>

                        {/* Spacer */}
                        <div className="flex-1" />

                        {/* Right actions */}
                        <div className="flex items-center gap-4">
                            {/* Notifications */}
                            <Button variant="ghost" size="icon" className="relative">
                                <Bell className="w-5 h-5" />
                                <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center bg-red-500 text-white text-xs">
                                    3
                                </Badge>
                            </Button>

                            {/* User menu */}
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" className="flex items-center gap-2">
                                        <Avatar className="h-8 w-8">
                                            <AvatarImage src={user?.profile_image} />
                                            <AvatarFallback className="bg-blue-500/20 text-blue-400 text-sm">
                                                {userInitials}
                                            </AvatarFallback>
                                        </Avatar>
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" className="w-56">
                                    <DropdownMenuLabel>My Account</DropdownMenuLabel>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem asChild>
                                        <Link href="/settings">
                                            <User className="mr-2 h-4 w-4" />
                                            Profile
                                        </Link>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem asChild>
                                        <Link href="/settings">
                                            <Settings className="mr-2 h-4 w-4" />
                                            Settings
                                        </Link>
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem onClick={logout} className="text-red-400">
                                        <LogOut className="mr-2 h-4 w-4" />
                                        Logout
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>
                    </div>
                </header>

                {/* Page content */}
                <main className="p-4 lg:p-8">{children}</main>
            </div>
        </div>
    );
}
