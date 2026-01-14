/**
 * Escrow Status Badge Component
 * Color-coded badges for escrow states
 */
import { Badge } from '@/components/ui/badge';
import {
    Clock,
    CheckCircle2,
    AlertTriangle,
    XCircle,
    Wallet,
    FileCheck,
    Loader2,
    Scale,
    RefreshCw,
    Archive,
} from 'lucide-react';

type EscrowStatus =
    | 'created'
    | 'funded'
    | 'in_verification'
    | 'milestone_pending'
    | 'partially_released'
    | 'fully_released'
    | 'disputed'
    | 'resolved'
    | 'refunded'
    | 'cancelled'
    | 'closed';

interface StatusConfig {
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
    icon: React.ElementType;
}

const statusConfig: Record<EscrowStatus, StatusConfig> = {
    created: {
        label: 'Awaiting Payment',
        color: 'text-gray-400',
        bgColor: 'bg-gray-500/10',
        borderColor: 'border-gray-500/30',
        icon: Clock,
    },
    funded: {
        label: 'Funded',
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/30',
        icon: Wallet,
    },
    in_verification: {
        label: 'Verifying',
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-500/10',
        borderColor: 'border-yellow-500/30',
        icon: Loader2,
    },
    milestone_pending: {
        label: 'In Progress',
        color: 'text-cyan-400',
        bgColor: 'bg-cyan-500/10',
        borderColor: 'border-cyan-500/30',
        icon: FileCheck,
    },
    partially_released: {
        label: 'Partial Release',
        color: 'text-teal-400',
        bgColor: 'bg-teal-500/10',
        borderColor: 'border-teal-500/30',
        icon: RefreshCw,
    },
    fully_released: {
        label: 'Completed',
        color: 'text-green-400',
        bgColor: 'bg-green-500/10',
        borderColor: 'border-green-500/30',
        icon: CheckCircle2,
    },
    disputed: {
        label: 'Disputed',
        color: 'text-red-400',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/30',
        icon: AlertTriangle,
    },
    resolved: {
        label: 'Resolved',
        color: 'text-purple-400',
        bgColor: 'bg-purple-500/10',
        borderColor: 'border-purple-500/30',
        icon: Scale,
    },
    refunded: {
        label: 'Refunded',
        color: 'text-orange-400',
        bgColor: 'bg-orange-500/10',
        borderColor: 'border-orange-500/30',
        icon: RefreshCw,
    },
    cancelled: {
        label: 'Cancelled',
        color: 'text-gray-500',
        bgColor: 'bg-gray-500/10',
        borderColor: 'border-gray-500/30',
        icon: XCircle,
    },
    closed: {
        label: 'Closed',
        color: 'text-gray-500',
        bgColor: 'bg-gray-500/10',
        borderColor: 'border-gray-500/30',
        icon: Archive,
    },
};

interface EscrowStatusBadgeProps {
    status: string;
    showIcon?: boolean;
    size?: 'sm' | 'md' | 'lg';
}

export function EscrowStatusBadge({
    status,
    showIcon = true,
    size = 'md',
}: EscrowStatusBadgeProps) {
    const config = statusConfig[status as EscrowStatus] || statusConfig.created;
    const Icon = config.icon;

    const sizeClasses = {
        sm: 'text-xs px-2 py-0.5',
        md: 'text-sm px-3 py-1',
        lg: 'text-base px-4 py-1.5',
    };

    const iconSizes = {
        sm: 'w-3 h-3',
        md: 'w-4 h-4',
        lg: 'w-5 h-5',
    };

    return (
        <Badge
            variant="outline"
            className={`
        ${config.bgColor} ${config.color} ${config.borderColor}
        ${sizeClasses[size]}
        font-medium inline-flex items-center gap-1.5
      `}
        >
            {showIcon && <Icon className={`${iconSizes[size]} ${status === 'in_verification' ? 'animate-spin' : ''}`} />}
            {config.label}
        </Badge>
    );
}

export { statusConfig, type EscrowStatus };
