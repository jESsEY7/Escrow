/**
 * Admin User Management Page
 */
import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
    Search,
    MoreVertical,
    Shield,
    Ban,
    Mail,
    CheckCircle2,
    Clock,
    XCircle,
} from 'lucide-react';

interface User {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    role: string;
    status: string;
    kyc_status: string;
    created_at: string;
    escrow_count: number;
}

const statusConfig: Record<string, { label: string; color: string }> = {
    active: { label: 'Active', color: 'bg-green-500/10 text-green-400' },
    pending_verification: { label: 'Pending', color: 'bg-yellow-500/10 text-yellow-400' },
    suspended: { label: 'Suspended', color: 'bg-red-500/10 text-red-400' },
    inactive: { label: 'Inactive', color: 'bg-gray-500/10 text-gray-400' },
};

const kycStatusConfig: Record<string, { label: string; icon: any; color: string }> = {
    verified: { label: 'Verified', icon: CheckCircle2, color: 'text-green-400' },
    pending: { label: 'Pending', icon: Clock, color: 'text-yellow-400' },
    rejected: { label: 'Rejected', icon: XCircle, color: 'text-red-400' },
    not_started: { label: 'Not Started', icon: Shield, color: 'text-gray-400' },
};

export default function AdminUsers() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        // Simulate fetching users
        setTimeout(() => {
            setUsers([
                {
                    id: '1',
                    email: 'john@example.com',
                    first_name: 'John',
                    last_name: 'Doe',
                    role: 'buyer',
                    status: 'active',
                    kyc_status: 'verified',
                    created_at: '2026-01-15',
                    escrow_count: 12,
                },
                {
                    id: '2',
                    email: 'jane@example.com',
                    first_name: 'Jane',
                    last_name: 'Smith',
                    role: 'seller',
                    status: 'active',
                    kyc_status: 'pending',
                    created_at: '2026-01-20',
                    escrow_count: 8,
                },
                {
                    id: '3',
                    email: 'bob@example.com',
                    first_name: 'Bob',
                    last_name: 'Johnson',
                    role: 'buyer',
                    status: 'suspended',
                    kyc_status: 'rejected',
                    created_at: '2026-02-01',
                    escrow_count: 2,
                },
            ]);
            setLoading(false);
        }, 500);
    }, []);

    const filteredUsers = users.filter(
        (user) =>
            user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
            user.first_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            user.last_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
        });
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold">User Management</h1>
                        <p className="text-gray-400 mt-1">
                            Manage platform users and their permissions
                        </p>
                    </div>
                </div>

                {/* Search */}
                <Card className="glass-card border-white/10">
                    <CardContent className="p-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <Input
                                placeholder="Search users by name or email..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10 bg-white/5 border-white/10"
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* Users Table */}
                <Card className="glass-card border-white/10">
                    <CardContent className="p-0">
                        {loading ? (
                            <div className="p-6 space-y-4">
                                {[1, 2, 3].map((i) => (
                                    <div key={i} className="flex gap-4">
                                        <Skeleton className="h-10 w-10 rounded-full bg-white/10" />
                                        <Skeleton className="h-10 flex-1 bg-white/10" />
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow className="border-white/10 hover:bg-transparent">
                                        <TableHead className="text-gray-400">User</TableHead>
                                        <TableHead className="text-gray-400">Role</TableHead>
                                        <TableHead className="text-gray-400">Status</TableHead>
                                        <TableHead className="text-gray-400">KYC</TableHead>
                                        <TableHead className="text-gray-400">Escrows</TableHead>
                                        <TableHead className="text-gray-400">Joined</TableHead>
                                        <TableHead className="text-gray-400 text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredUsers.map((user) => {
                                        const status = statusConfig[user.status] || statusConfig.inactive;
                                        const kyc = kycStatusConfig[user.kyc_status] || kycStatusConfig.not_started;
                                        const KycIcon = kyc.icon;

                                        return (
                                            <TableRow key={user.id} className="border-white/10 hover:bg-white/5">
                                                <TableCell>
                                                    <div className="flex items-center gap-3">
                                                        <Avatar className="h-10 w-10">
                                                            <AvatarFallback className="bg-blue-500/20 text-blue-400">
                                                                {user.first_name[0]}{user.last_name[0]}
                                                            </AvatarFallback>
                                                        </Avatar>
                                                        <div>
                                                            <p className="font-medium">
                                                                {user.first_name} {user.last_name}
                                                            </p>
                                                            <p className="text-sm text-gray-400">{user.email}</p>
                                                        </div>
                                                    </div>
                                                </TableCell>
                                                <TableCell>
                                                    <span className="capitalize">{user.role}</span>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge className={`${status.color} border-none`}>
                                                        {status.label}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <div className="flex items-center gap-1">
                                                        <KycIcon className={`w-4 h-4 ${kyc.color}`} />
                                                        <span className={`text-sm ${kyc.color}`}>{kyc.label}</span>
                                                    </div>
                                                </TableCell>
                                                <TableCell>{user.escrow_count}</TableCell>
                                                <TableCell className="text-gray-400">
                                                    {formatDate(user.created_at)}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <DropdownMenu>
                                                        <DropdownMenuTrigger asChild>
                                                            <Button variant="ghost" size="sm">
                                                                <MoreVertical className="w-4 h-4" />
                                                            </Button>
                                                        </DropdownMenuTrigger>
                                                        <DropdownMenuContent align="end">
                                                            <DropdownMenuItem>
                                                                <Mail className="w-4 h-4 mr-2" />
                                                                Send Email
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem>
                                                                <Shield className="w-4 h-4 mr-2" />
                                                                View KYC
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem className="text-red-400">
                                                                <Ban className="w-4 h-4 mr-2" />
                                                                Suspend User
                                                            </DropdownMenuItem>
                                                        </DropdownMenuContent>
                                                    </DropdownMenu>
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
