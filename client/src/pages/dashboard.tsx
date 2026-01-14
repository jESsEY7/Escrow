/**
 * Dashboard Home Page
 * Overview with stats and recent escrows
 */
import { useEffect, useState } from 'react';
import { Link } from 'wouter';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { EscrowStatusBadge } from '@/components/dashboard/EscrowStatusBadge';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
    Briefcase,
    TrendingUp,
    AlertTriangle,
    CheckCircle2,
    Plus,
    ArrowRight,
    Clock,
} from 'lucide-react';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

interface DashboardStats {
    total_escrows: number;
    active_escrows: number;
    completed_escrows: number;
    disputed_escrows: number;
    total_volume: number;
    pending_amount: number;
}

interface Escrow {
    id: string;
    reference_code: string;
    title: string;
    total_amount: number;
    currency: string;
    status: string;
    created_at: string;
    buyer: { email: string };
    seller: { email: string };
    platform_fee_percent?: string;
    fee_applied?: string;
    auto_release_at?: string;
}

export default function Dashboard() {
    const { user } = useAuth();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [recentEscrows, setRecentEscrows] = useState<Escrow[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const [escrowsData] = await Promise.all([
                api.escrow.list(),
            ]);

            // Calculate stats from escrows
            const escrows = (escrowsData as any).results || escrowsData;
            const calculatedStats: DashboardStats = {
                total_escrows: escrows.length,
                active_escrows: escrows.filter((e: Escrow) =>
                    ['created', 'funded', 'milestone_pending', 'partially_released'].includes(e.status)
                ).length,
                completed_escrows: escrows.filter((e: Escrow) =>
                    ['fully_released', 'closed'].includes(e.status)
                ).length,
                disputed_escrows: escrows.filter((e: Escrow) =>
                    ['disputed', 'resolved'].includes(e.status)
                ).length,
                total_volume: escrows.reduce((sum: number, e: Escrow) => sum + Number(e.total_amount), 0),
                pending_amount: escrows
                    .filter((e: Escrow) => ['funded', 'milestone_pending', 'partially_released'].includes(e.status))
                    .reduce((sum: number, e: Escrow) => sum + Number(e.total_amount), 0),
            };

            setStats(calculatedStats);
            setRecentEscrows(escrows.slice(0, 5));
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount: number, currency = 'KES') => {
        return new Intl.NumberFormat('en-KE', {
            style: 'currency',
            currency,
            minimumFractionDigits: 0,
        }).format(amount);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
        });
    };

    const statCards = [
        {
            title: 'Total Escrows',
            value: stats?.total_escrows || 0,
            icon: Briefcase,
            color: 'text-blue-400',
            bgColor: 'bg-blue-500/10',
        },
        {
            title: 'Active',
            value: stats?.active_escrows || 0,
            icon: Clock,
            color: 'text-cyan-400',
            bgColor: 'bg-cyan-500/10',
        },
        {
            title: 'Completed',
            value: stats?.completed_escrows || 0,
            icon: CheckCircle2,
            color: 'text-green-400',
            bgColor: 'bg-green-500/10',
        },
        {
            title: 'Disputed',
            value: stats?.disputed_escrows || 0,
            icon: AlertTriangle,
            color: 'text-red-400',
            bgColor: 'bg-red-500/10',
        },
    ];

    return (
        <DashboardLayout>
            <div className="space-y-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold">
                            Welcome back, {user?.first_name || 'User'}
                        </h1>
                        <p className="text-gray-400 mt-1">
                            Here's what's happening with your escrows today.
                        </p>
                    </div>

                    <div className="flex gap-4 items-center">
                        <ThemeSwitcher />
                        <Link href="/escrows/new">
                            <Button className="bg-blue-500 hover:bg-blue-600">
                                <Plus className="w-4 h-4 mr-2" />
                                New Escrow
                            </Button>
                        </Link>
                    </div>
                </div>

                {/* Plan Overview */}
                {user?.effective_plan && (
                    <Card className="glass-card border-white/10 bg-gradient-to-r from-indigo-500/10 to-purple-500/10">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-lg font-semibold text-white">Current Plan: {user.effective_plan.name}</h3>
                                    <p className="text-sm text-gray-400">
                                        Fee: <span className="text-green-400 font-mono">{user.effective_plan.fee_percent}%</span> |
                                        SLA: <span className="text-blue-400 font-mono">{user.effective_plan.sla_hours}h</span>
                                    </p>
                                </div>
                                <div className="flex gap-2">
                                    {user.effective_plan.features.api_access && (
                                        <span className="px-2 py-1 bg-white/10 rounded text-xs">API</span>
                                    )}
                                    {user.effective_plan.features.dedicated_support && (
                                        <span className="px-2 py-1 bg-white/10 rounded text-xs">Support</span>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {statCards.map((stat) => (
                        <Card key={stat.title} className="glass-card border-white/10">
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
                    ))}
                </div>

                {/* Volume Stats */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className="glass-card border-white/10">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-4">
                                <div className="p-3 rounded-xl bg-green-500/10">
                                    <TrendingUp className="w-6 h-6 text-green-400" />
                                </div>
                                <div>
                                    <p className="text-gray-400 text-sm">Total Volume</p>
                                    <p className="text-2xl font-bold">
                                        {loading ? <Skeleton className="h-7 w-32 bg-white/10" /> : formatCurrency(stats?.total_volume || 0)}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="glass-card border-white/10">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-4">
                                <div className="p-3 rounded-xl bg-yellow-500/10">
                                    <Briefcase className="w-6 h-6 text-yellow-400" />
                                </div>
                                <div>
                                    <p className="text-gray-400 text-sm">Pending Amount</p>
                                    <p className="text-2xl font-bold">
                                        {loading ? <Skeleton className="h-7 w-32 bg-white/10" /> : formatCurrency(stats?.pending_amount || 0)}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Recent Escrows */}
                <Card className="glass-card border-white/10">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Recent Escrows</CardTitle>
                        <Link href="/escrows">
                            <Button variant="ghost" size="sm" className="text-blue-400">
                                View all
                                <ArrowRight className="w-4 h-4 ml-1" />
                            </Button>
                        </Link>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="space-y-4">
                                {[1, 2, 3].map((i) => (
                                    <div key={i} className="flex items-center gap-4">
                                        <Skeleton className="h-12 w-12 rounded-lg bg-white/10" />
                                        <div className="flex-1 space-y-2">
                                            <Skeleton className="h-4 w-40 bg-white/10" />
                                            <Skeleton className="h-3 w-24 bg-white/10" />
                                        </div>
                                        <Skeleton className="h-6 w-20 bg-white/10" />
                                    </div>
                                ))}
                            </div>
                        ) : recentEscrows.length === 0 ? (
                            <div className="text-center py-12">
                                <Briefcase className="w-12 h-12 mx-auto text-gray-500 mb-4" />
                                <p className="text-gray-400">No escrows yet</p>
                                <Link href="/escrows/new">
                                    <Button className="mt-4" variant="outline">
                                        Create your first escrow
                                    </Button>
                                </Link>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {recentEscrows.map((escrow) => (
                                    <Link key={escrow.id} href={`/escrows/${escrow.id}`}>
                                        <div className="flex items-center gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <p className="font-medium truncate">{escrow.title}</p>
                                                    <span className="text-xs text-gray-500">{escrow.reference_code}</span>
                                                </div>
                                                <div className="flex flex-col gap-1 mt-1">
                                                    <p className="text-sm text-gray-400">
                                                        {formatDate(escrow.created_at)}
                                                    </p>
                                                    {/* Automation & Fee Info */}
                                                    <div className="flex gap-3 text-xs">
                                                        {escrow.status === 'funded' && escrow.auto_release_at && (
                                                            <span className="text-blue-400 flex items-center gap-1">
                                                                <Clock className="w-3 h-3" />
                                                                Auto-release: {new Date(escrow.auto_release_at).toLocaleString()}
                                                            </span>
                                                        )}
                                                        {escrow.platform_fee_percent && (
                                                            <span className="text-gray-500">
                                                                Fee: {escrow.platform_fee_percent}%
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-semibold">
                                                    {formatCurrency(escrow.total_amount, escrow.currency)}
                                                </p>
                                                <EscrowStatusBadge status={escrow.status} size="sm" />
                                            </div>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
