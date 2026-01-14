/**
 * Escrow Timeline Component
 * Animated progress timeline for escrow milestones
 */
import { CheckCircle2, Clock, Circle, AlertTriangle } from 'lucide-react';

interface Milestone {
    id: string;
    title: string;
    description: string;
    amount: number;
    status: 'pending' | 'in_progress' | 'submitted' | 'approved' | 'rejected' | 'released';
    order: number;
    submitted_at?: string;
    approved_at?: string;
    released_at?: string;
}

interface EscrowTimelineProps {
    milestones: Milestone[];
    currency?: string;
}

const statusConfig = {
    pending: { icon: Circle, color: 'text-gray-400', bgColor: 'bg-gray-500/20' },
    in_progress: { icon: Clock, color: 'text-yellow-400', bgColor: 'bg-yellow-500/20' },
    submitted: { icon: Clock, color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
    approved: { icon: CheckCircle2, color: 'text-cyan-400', bgColor: 'bg-cyan-500/20' },
    rejected: { icon: AlertTriangle, color: 'text-red-400', bgColor: 'bg-red-500/20' },
    released: { icon: CheckCircle2, color: 'text-green-400', bgColor: 'bg-green-500/20' },
};

export function EscrowTimeline({ milestones, currency = 'KES' }: EscrowTimelineProps) {
    const sortedMilestones = [...milestones].sort((a, b) => a.order - b.order);

    const formatCurrency = (amount: number) => {
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
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const getStatusLabel = (status: string) => {
        const labels: Record<string, string> = {
            pending: 'Pending',
            in_progress: 'In Progress',
            submitted: 'Submitted for Review',
            approved: 'Approved',
            rejected: 'Rejected',
            released: 'Funds Released',
        };
        return labels[status] || status;
    };

    const getCompletedCount = () => {
        return sortedMilestones.filter((m) => m.status === 'released').length;
    };

    const progressPercent = sortedMilestones.length > 0
        ? (getCompletedCount() / sortedMilestones.length) * 100
        : 0;

    return (
        <div className="space-y-6">
            {/* Progress bar */}
            <div className="space-y-2">
                <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Progress</span>
                    <span className="text-white font-medium">
                        {getCompletedCount()} of {sortedMilestones.length} milestones
                    </span>
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500 ease-out"
                        style={{ width: `${progressPercent}%` }}
                    />
                </div>
            </div>

            {/* Timeline */}
            <div className="relative">
                {/* Connecting line */}
                <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-white/10" />

                {/* Milestones */}
                <div className="space-y-6">
                    {sortedMilestones.map((milestone, index) => {
                        const config = statusConfig[milestone.status];
                        const Icon = config.icon;
                        const isCompleted = milestone.status === 'released';
                        const isLast = index === sortedMilestones.length - 1;

                        return (
                            <div
                                key={milestone.id}
                                className="relative flex gap-4 animate-fade-in"
                                style={{ animationDelay: `${index * 100}ms` }}
                            >
                                {/* Icon */}
                                <div
                                    className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300
                    ${isCompleted
                                            ? 'border-green-500 bg-green-500/20'
                                            : `border-white/20 ${config.bgColor}`
                                        }
                  `}
                                >
                                    <Icon
                                        className={`w-5 h-5 ${isCompleted ? 'text-green-400' : config.color}`}
                                    />
                                </div>

                                {/* Content */}
                                <div
                                    className={`flex-1 p-4 rounded-xl transition-all duration-300
                    ${isCompleted
                                            ? 'bg-green-500/10 border border-green-500/20'
                                            : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                        }
                  `}
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex-1">
                                            <h4 className="font-medium">{milestone.title}</h4>
                                            <p className="text-sm text-gray-400 mt-1">
                                                {milestone.description}
                                            </p>
                                            {milestone.released_at && (
                                                <p className="text-xs text-green-400 mt-2">
                                                    Released on {formatDate(milestone.released_at)}
                                                </p>
                                            )}
                                            {milestone.submitted_at && !milestone.released_at && (
                                                <p className="text-xs text-blue-400 mt-2">
                                                    Submitted on {formatDate(milestone.submitted_at)}
                                                </p>
                                            )}
                                        </div>
                                        <div className="text-right">
                                            <p className="font-semibold">
                                                {formatCurrency(milestone.amount)}
                                            </p>
                                            <span
                                                className={`text-xs ${config.color} inline-block mt-1 px-2 py-0.5 rounded-full ${config.bgColor}`}
                                            >
                                                {getStatusLabel(milestone.status)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
