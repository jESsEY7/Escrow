/**
 * Escrow Detail Page
 * Shows escrow info, milestones, and actions
 */
import { useEffect, useState } from 'react';
import { useParams, Link } from 'wouter';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { EscrowStatusBadge } from '@/components/dashboard/EscrowStatusBadge';
import { EscrowTimeline } from '@/components/dashboard/EscrowTimeline';
import { MpesaPaymentModal } from '@/components/payments/MpesaPaymentModal';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    ArrowLeft,
    CreditCard,
    User,
    Clock,
    AlertTriangle,
    FileText,
    MessageSquare,
} from 'lucide-react';

interface Escrow {
    id: string;
    reference_code: string;
    title: string;
    description: string;
    total_amount: number;
    currency: string;
    status: string;
    escrow_type: string;
    created_at: string;
    expires_at: string;
    funded_at?: string;
    completed_at?: string;
    buyer: { id: string; email: string; full_name: string };
    seller: { id: string; email: string; full_name: string };
    milestones: any[];
    inspection_period_days: number;
    auto_release_days: number;
    platform_fee_percent: number;
}

export default function EscrowDetail() {
    const { id } = useParams<{ id: string }>();
    const { user } = useAuth();
    const [escrow, setEscrow] = useState<Escrow | null>(null);
    const [loading, setLoading] = useState(true);
    const [showPaymentModal, setShowPaymentModal] = useState(false);

    useEffect(() => {
        if (id) {
            fetchEscrow();
        }
    }, [id]);

    const fetchEscrow = async () => {
        try {
            const data = await api.escrow.get(id!);
            setEscrow(data);
        } catch (error) {
            console.error('Failed to fetch escrow:', error);
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
            month: 'long',
            day: 'numeric',
            year: 'numeric',
        });
    };

    const isBuyer = user?.id === escrow?.buyer?.id;
    const isSeller = user?.id === escrow?.seller?.id;
    const canFund = isBuyer && escrow?.status === 'created';
    const canDispute = ['funded', 'milestone_pending', 'partially_released'].includes(escrow?.status || '');

    if (loading) {
        return (
            <DashboardLayout>
                <div className="space-y-6">
                    <Skeleton className="h-8 w-48 bg-white/10" />
                    <Skeleton className="h-64 w-full bg-white/10" />
                </div>
            </DashboardLayout>
        );
    }

    if (!escrow) {
        return (
            <DashboardLayout>
                <div className="text-center py-12">
                    <p className="text-gray-400">Escrow not found</p>
                    <Link href="/escrows">
                        <Button className="mt-4" variant="outline">
                            Back to Escrows
                        </Button>
                    </Link>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div>
                        <Link href="/escrows">
                            <Button variant="ghost" size="sm" className="mb-2 -ml-2">
                                <ArrowLeft className="w-4 h-4 mr-1" />
                                Back to Escrows
                            </Button>
                        </Link>
                        <div className="flex items-center gap-3">
                            <h1 className="text-2xl font-bold">{escrow.title}</h1>
                            <EscrowStatusBadge status={escrow.status} />
                        </div>
                        <p className="text-gray-400 mt-1 font-mono">{escrow.reference_code}</p>
                    </div>

                    <div className="flex gap-3">
                        {canFund && (
                            <Button
                                onClick={() => setShowPaymentModal(true)}
                                className="bg-green-500 hover:bg-green-600"
                            >
                                <CreditCard className="w-4 h-4 mr-2" />
                                Fund Escrow
                            </Button>
                        )}
                        {canDispute && (
                            <Link href={`/disputes/new?escrow=${escrow.id}`}>
                                <Button variant="outline" className="border-red-500/30 text-red-400">
                                    <AlertTriangle className="w-4 h-4 mr-2" />
                                    Raise Dispute
                                </Button>
                            </Link>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-6">
                        <Tabs defaultValue="milestones">
                            <TabsList className="bg-white/5 border border-white/10">
                                <TabsTrigger value="milestones">Milestones</TabsTrigger>
                                <TabsTrigger value="details">Details</TabsTrigger>
                                <TabsTrigger value="activity">Activity</TabsTrigger>
                            </TabsList>

                            <TabsContent value="milestones" className="mt-6">
                                <Card className="glass-card border-white/10">
                                    <CardHeader>
                                        <CardTitle>Payment Milestones</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        {escrow.milestones && escrow.milestones.length > 0 ? (
                                            <EscrowTimeline
                                                milestones={escrow.milestones}
                                                currency={escrow.currency}
                                            />
                                        ) : (
                                            <div className="text-center py-8 text-gray-400">
                                                <FileText className="w-8 h-8 mx-auto mb-2" />
                                                <p>No milestones defined</p>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            <TabsContent value="details" className="mt-6">
                                <Card className="glass-card border-white/10">
                                    <CardContent className="pt-6 space-y-4">
                                        <div>
                                            <h4 className="text-sm text-gray-400">Description</h4>
                                            <p className="mt-1">{escrow.description || 'No description provided'}</p>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <h4 className="text-sm text-gray-400">Escrow Type</h4>
                                                <p className="mt-1 capitalize">{escrow.escrow_type.replace('_', ' ')}</p>
                                            </div>
                                            <div>
                                                <h4 className="text-sm text-gray-400">Platform Fee</h4>
                                                <p className="mt-1">{escrow.platform_fee_percent}%</p>
                                            </div>
                                            <div>
                                                <h4 className="text-sm text-gray-400">Inspection Period</h4>
                                                <p className="mt-1">{escrow.inspection_period_days} days</p>
                                            </div>
                                            <div>
                                                <h4 className="text-sm text-gray-400">Auto-Release</h4>
                                                <p className="mt-1">{escrow.auto_release_days} days</p>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            <TabsContent value="activity" className="mt-6">
                                <Card className="glass-card border-white/10">
                                    <CardContent className="pt-6">
                                        <div className="text-center py-8 text-gray-400">
                                            <MessageSquare className="w-8 h-8 mx-auto mb-2" />
                                            <p>Activity log coming soon</p>
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>
                        </Tabs>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Amount Card */}
                        <Card className="glass-card border-white/10">
                            <CardContent className="pt-6">
                                <div className="text-center">
                                    <p className="text-sm text-gray-400">Total Amount</p>
                                    <p className="text-3xl font-bold text-green-400 mt-1">
                                        {formatCurrency(escrow.total_amount, escrow.currency)}
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Parties Card */}
                        <Card className="glass-card border-white/10">
                            <CardHeader>
                                <CardTitle className="text-sm">Parties</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                                        <User className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <div>
                                        <p className="text-xs text-gray-400">Buyer</p>
                                        <p className="font-medium">
                                            {isBuyer ? 'You' : escrow.buyer?.full_name || escrow.buyer?.email}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
                                        <User className="w-5 h-5 text-purple-400" />
                                    </div>
                                    <div>
                                        <p className="text-xs text-gray-400">Seller</p>
                                        <p className="font-medium">
                                            {isSeller ? 'You' : escrow.seller?.full_name || escrow.seller?.email}
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Timeline Card */}
                        <Card className="glass-card border-white/10">
                            <CardHeader>
                                <CardTitle className="text-sm">Timeline</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <div className="flex items-center gap-3">
                                    <Clock className="w-4 h-4 text-gray-400" />
                                    <div>
                                        <p className="text-xs text-gray-400">Created</p>
                                        <p className="text-sm">{formatDate(escrow.created_at)}</p>
                                    </div>
                                </div>
                                {escrow.funded_at && (
                                    <div className="flex items-center gap-3">
                                        <CreditCard className="w-4 h-4 text-green-400" />
                                        <div>
                                            <p className="text-xs text-gray-400">Funded</p>
                                            <p className="text-sm">{formatDate(escrow.funded_at)}</p>
                                        </div>
                                    </div>
                                )}
                                {escrow.expires_at && !escrow.funded_at && (
                                    <div className="flex items-center gap-3">
                                        <AlertTriangle className="w-4 h-4 text-yellow-400" />
                                        <div>
                                            <p className="text-xs text-gray-400">Expires</p>
                                            <p className="text-sm">{formatDate(escrow.expires_at)}</p>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>

            {/* Payment Modal */}
            <MpesaPaymentModal
                isOpen={showPaymentModal}
                onClose={() => setShowPaymentModal(false)}
                escrowId={escrow.id}
                amount={escrow.total_amount}
                currency={escrow.currency}
                onSuccess={fetchEscrow}
            />
        </DashboardLayout>
    );
}
