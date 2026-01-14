/**
 * Admin Dashboard Page
 */
import { useEffect, useState } from 'react';
import { Link } from 'wouter';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
    Users,
    Briefcase,
    AlertTriangle,
    DollarSign,
    TrendingUp,
    Shield,
    Activity,
    FileText,
} from 'lucide-react';

interface AdminStats {
    total_users: number;
    active_escrows: number;
    pending_disputes: number;
    total_volume: number;
    pending_kyc: number;
    recent_activity: any[];
}

export default function AdminDashboard() {
    const [stats, setStats] = useState<AdminStats>({
        total_users: 0,
        active_escrows: 0,
        pending_disputes: 0,
        total_volume: 0,
        pending_kyc: 0,
        recent_activity: [],
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Simulate fetching admin stats
        setTimeout(() => {
            setStats({
                total_users: 1247,
                active_escrows: 89,
                pending_disputes: 12,
                total_volume: 45678900,
                pending_kyc: 34,
                recent_activity: [],
            });
            setLoading(false);
        }, 500);
    }, []);

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-KE', {
            style: 'currency',
            currency: 'KES',
            minimumFractionDigits: 0,
            notation: 'compact',
        }).format(amount);
    };

    const statCards = [
        {
            title: 'Total Users',
            value: stats.total_users,
            icon: Users,
            color: 'text-blue-400',
            bgColor: 'bg-blue-500/10',
            href: '/admin/users',
        },
        {
            title: 'Active Escrows',
            value: stats.active_escrows,
            icon: Briefcase,
            color: 'text-cyan-400',
            bgColor: 'bg-cyan-500/10',
            href: '/admin/escrows',
        },
        {
            title: 'Pending Disputes',
            value: stats.pending_disputes,
            icon: AlertTriangle,
            color: 'text-red-400',
            bgColor: 'bg-red-500/10',
            href: '/admin/disputes',
        },
        {
            title: 'Pending KYC',
            value: stats.pending_kyc,
            icon: Shield,
            color: 'text-yellow-400',
            bgColor: 'bg-yellow-500/10',
            href: '/admin/kyc',
        },
    ];

    const quickActions = [
        { title: 'User Management', icon: Users, href: '/admin/users' },
        { title: 'Escrow Oversight', icon: Briefcase, href: '/admin/escrows' },
        { title: 'Dispute Resolution', icon: AlertTriangle, href: '/admin/disputes' },
        { title: 'KYC Verification', icon: Shield, href: '/admin/kyc' },
        { title: 'Audit Logs', icon: FileText, href: '/admin/audit' },
        { title: 'System Health', icon: Activity, href: '/admin/health' },
    ];

    return (
        <DashboardLayout>
            <div className="space-y-8">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold">Admin Dashboard</h1>
                    <p className="text-gray-400 mt-1">
                        Platform overview and management tools
                    </p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {statCards.map((stat) => (
                        <Link key={stat.title} href={stat.href}>
                            <Card className="glass-card border-white/10 hover:bg-white/5 transition-colors cursor-pointer">
                                <CardContent className="pt-6">
                                    {loading ? (
                                        <div className="space-y-3">
                                            <Skeleton className="h-4 w-20 bg-white/10" />
                                            <Skeleton className="h-8 w-16 bg-white/10" />
                                        </div>
                                    ) : (
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="text-gray-400 text-sm">{stat.title}</p>
                                                <p className="text-3xl font-bold mt-1">{stat.value}</p>
                                            </div>
                                            <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                                                <stat.icon className={`w-6 h-6 ${stat.color}`} />
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </Link>
                    ))}
                </div>

                {/* Total Volume */}
                <Card className="glass-card border-white/10">
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400">Total Platform Volume</p>
                                <p className="text-4xl font-bold mt-2 bg-gradient-to-r from-green-400 to-cyan-400 bg-clip-text text-transparent">
                                    {loading ? (
                                        <Skeleton className="h-10 w-48 bg-white/10" />
                                    ) : (
                                        formatCurrency(stats.total_volume)
                                    )}
                                </p>
                            </div>
                            <div className="p-4 rounded-2xl bg-green-500/10">
                                <TrendingUp className="w-8 h-8 text-green-400" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Quick Actions */}
                <div>
                    <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                        {quickActions.map((action) => (
                            <Link key={action.title} href={action.href}>
                                <Card className="glass-card border-white/10 hover:bg-white/10 transition-colors cursor-pointer">
                                    <CardContent className="pt-6 pb-6 text-center">
                                        <action.icon className="w-8 h-8 mx-auto text-blue-400 mb-3" />
                                        <p className="text-sm font-medium">{action.title}</p>
                                    </CardContent>
                                </Card>
                            </Link>
                        ))}
                    </div>
                </div>

                {/* Recent Activity */}
                <Card className="glass-card border-white/10">
                    <CardHeader>
                        <CardTitle>Recent Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-center py-8 text-gray-400">
                            <Activity className="w-8 h-8 mx-auto mb-2" />
                            <p>Activity feed coming soon</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
