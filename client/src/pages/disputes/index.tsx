/**
 * Dispute List Page
 */
import { useEffect, useState } from 'react';
import { Link } from 'wouter';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { api } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
    AlertTriangle,
    Clock,
    CheckCircle2,
    Scale,
    Eye,
} from 'lucide-react';

interface Dispute {
    id: string;
    escrow: { id: string; title: string; reference_code: string };
    reason: string;
    status: string;
    created_at: string;
    resolution_deadline?: string;
    priority_score: number;
    evidence_folder_url?: string;
}

const statusConfig: Record<string, { label: string; color: string; bgColor: string; icon: any }> = {
    open: { label: 'Open', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10', icon: AlertTriangle },
    under_review: { label: 'Under Review', color: 'text-blue-400', bgColor: 'bg-blue-500/10', icon: Clock },
    escalated: { label: 'Escalated', color: 'text-red-400', bgColor: 'bg-red-500/10', icon: AlertTriangle },
    resolved: { label: 'Resolved', color: 'text-green-400', bgColor: 'bg-green-500/10', icon: CheckCircle2 },
    closed: { label: 'Closed', color: 'text-gray-400', bgColor: 'bg-gray-500/10', icon: Scale },
};

export default function DisputeList() {
    const [disputes, setDisputes] = useState<Dispute[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDisputes();
    }, []);

    const fetchDisputes = async () => {
        try {
            const data: any = await api.disputes.list();
            setDisputes(data.results || data);
        } catch (error) {
            console.error('Failed to fetch disputes:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
        });
    };

    const getReasonLabel = (reason: string) => {
        const labels: Record<string, string> = {
            not_as_described: 'Not as Described',
            not_received: 'Not Received',
            quality_issues: 'Quality Issues',
            late_delivery: 'Late Delivery',
            partial_delivery: 'Partial Delivery',
            fraud: 'Suspected Fraud',
            other: 'Other',
        };
        return labels[reason] || reason;
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold">Disputes</h1>
                    <p className="text-gray-400 mt-1">
                        View and manage your escrow disputes
                    </p>
                </div>

                {/* Dispute List */}
                {loading ? (
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <Card key={i} className="glass-card border-white/10">
                                <CardContent className="p-6">
                                    <Skeleton className="h-6 w-48 bg-white/10 mb-2" />
                                    <Skeleton className="h-4 w-32 bg-white/10" />
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : disputes.length === 0 ? (
                    <Card className="glass-card border-white/10">
                        <CardContent className="py-12 text-center">
                            <Scale className="w-12 h-12 mx-auto text-gray-500 mb-4" />
                            <p className="text-gray-400">No disputes found</p>
                            <p className="text-sm text-gray-500 mt-1">
                                You haven't raised or received any disputes yet
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-4">
                        {disputes.map((dispute) => {
                            const config = statusConfig[dispute.status] || statusConfig.open;
                            const Icon = config.icon;

                            return (
                                <Card key={dispute.id} className="glass-card border-white/10">
                                    <CardContent className="p-6">
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-start gap-4">
                                                <div className={`p-3 rounded-xl ${config.bgColor}`}>
                                                    <Icon className={`w-5 h-5 ${config.color}`} />
                                                </div>
                                                <div>
                                                    <h3 className="font-medium">{dispute.escrow.title}</h3>
                                                    <p className="text-sm text-gray-400 font-mono">
                                                        {dispute.escrow.reference_code}
                                                    </p>
                                                    <p className="text-sm text-gray-400 mt-2">
                                                        Reason: {getReasonLabel(dispute.reason)}
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="text-right">
                                                <div className="flex flex-col items-end gap-2">
                                                    <Badge className={`${config.bgColor} ${config.color} border-none`}>
                                                        {config.label}
                                                    </Badge>

                                                    {dispute.priority_score > 0 && (
                                                        <Badge variant="outline" className="border-purple-500/50 text-purple-400 bg-purple-500/10">
                                                            Priority: {dispute.priority_score}
                                                        </Badge>
                                                    )}
                                                </div>

                                                <p className="text-xs text-gray-500 mt-2">
                                                    {formatDate(dispute.created_at)}
                                                </p>

                                                {dispute.resolution_deadline && (
                                                    <p className="text-xs text-yellow-400 mt-1">
                                                        Due: {formatDate(dispute.resolution_deadline)}
                                                    </p>
                                                )}

                                                {dispute.evidence_folder_url && (
                                                    <a
                                                        href={dispute.evidence_folder_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-xs text-blue-400 hover:text-blue-300 block mt-1 underline"
                                                    >
                                                        View Evidence
                                                    </a>
                                                )}
                                            </div>
                                        </div>

                                        <div className="mt-4 pt-4 border-t border-white/10 flex justify-end">
                                            <Link href={`/disputes/${dispute.id}`}>
                                                <Button variant="ghost" size="sm">
                                                    <Eye className="w-4 h-4 mr-1" />
                                                    View Details
                                                </Button>
                                            </Link>
                                        </div>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
