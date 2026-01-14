/**
 * Escrow List Page
 * Displays all escrows with filters and search
 */
import { useEffect, useState } from 'react';
import { Link } from 'wouter';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { EscrowStatusBadge } from '@/components/dashboard/EscrowStatusBadge';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    Plus,
    Search,
    Filter,
    ArrowUpDown,
    Eye,
} from 'lucide-react';

interface Escrow {
    id: string;
    reference_code: string;
    title: string;
    total_amount: number;
    currency: string;
    status: string;
    escrow_type: string;
    created_at: string;
    expires_at: string;
    buyer: { email: string; full_name: string };
    seller: { email: string; full_name: string };
    progress_percentage: number;
}

type TabFilter = 'all' | 'active' | 'completed' | 'disputed';

const tabFilters: Record<TabFilter, string[]> = {
    all: [],
    active: ['created', 'funded', 'milestone_pending', 'partially_released', 'in_verification'],
    completed: ['fully_released', 'closed', 'refunded', 'cancelled'],
    disputed: ['disputed', 'resolved'],
};

export default function EscrowList() {
    const [escrows, setEscrows] = useState<Escrow[]>([]);
    const [filteredEscrows, setFilteredEscrows] = useState<Escrow[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState<TabFilter>('all');

    useEffect(() => {
        fetchEscrows();
    }, []);

    useEffect(() => {
        filterEscrows();
    }, [escrows, searchQuery, activeTab]);

    const fetchEscrows = async () => {
        try {
            const data = await api.escrow.list();
            const escrowList = data.results || data;
            setEscrows(escrowList);
        } catch (error) {
            console.error('Failed to fetch escrows:', error);
        } finally {
            setLoading(false);
        }
    };

    const filterEscrows = () => {
        let filtered = [...escrows];

        // Tab filter
        if (activeTab !== 'all') {
            filtered = filtered.filter((e) => tabFilters[activeTab].includes(e.status));
        }

        // Search filter
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(
                (e) =>
                    e.title.toLowerCase().includes(query) ||
                    e.reference_code.toLowerCase().includes(query) ||
                    e.buyer?.email?.toLowerCase().includes(query) ||
                    e.seller?.email?.toLowerCase().includes(query)
            );
        }

        setFilteredEscrows(filtered);
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

    const tabCounts = {
        all: escrows.length,
        active: escrows.filter((e) => tabFilters.active.includes(e.status)).length,
        completed: escrows.filter((e) => tabFilters.completed.includes(e.status)).length,
        disputed: escrows.filter((e) => tabFilters.disputed.includes(e.status)).length,
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold">Escrows</h1>
                        <p className="text-gray-400 mt-1">
                            Manage all your escrow transactions
                        </p>
                    </div>
                    <Link href="/escrows/new">
                        <Button className="bg-blue-500 hover:bg-blue-600">
                            <Plus className="w-4 h-4 mr-2" />
                            New Escrow
                        </Button>
                    </Link>
                </div>

                {/* Filters */}
                <Card className="glass-card border-white/10">
                    <CardContent className="p-4">
                        <div className="flex flex-col md:flex-row gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                <Input
                                    placeholder="Search by title, reference, or email..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-10 bg-white/5 border-white/10"
                                />
                            </div>
                            <Button variant="outline" className="border-white/10">
                                <Filter className="w-4 h-4 mr-2" />
                                Filters
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Tabs */}
                <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabFilter)}>
                    <TabsList className="bg-white/5 border border-white/10">
                        <TabsTrigger value="all" className="data-[state=active]:bg-blue-500/20">
                            All ({tabCounts.all})
                        </TabsTrigger>
                        <TabsTrigger value="active" className="data-[state=active]:bg-cyan-500/20">
                            Active ({tabCounts.active})
                        </TabsTrigger>
                        <TabsTrigger value="completed" className="data-[state=active]:bg-green-500/20">
                            Completed ({tabCounts.completed})
                        </TabsTrigger>
                        <TabsTrigger value="disputed" className="data-[state=active]:bg-red-500/20">
                            Disputed ({tabCounts.disputed})
                        </TabsTrigger>
                    </TabsList>

                    {/* Escrow Table */}
                    <TabsContent value={activeTab} className="mt-6">
                        <Card className="glass-card border-white/10">
                            <CardContent className="p-0">
                                {loading ? (
                                    <div className="p-6 space-y-4">
                                        {[1, 2, 3, 4, 5].map((i) => (
                                            <div key={i} className="flex gap-4">
                                                <Skeleton className="h-8 flex-1 bg-white/10" />
                                                <Skeleton className="h-8 w-24 bg-white/10" />
                                                <Skeleton className="h-8 w-20 bg-white/10" />
                                            </div>
                                        ))}
                                    </div>
                                ) : filteredEscrows.length === 0 ? (
                                    <div className="p-12 text-center">
                                        <p className="text-gray-400">No escrows found</p>
                                        {searchQuery && (
                                            <Button
                                                variant="ghost"
                                                onClick={() => setSearchQuery('')}
                                                className="mt-4"
                                            >
                                                Clear search
                                            </Button>
                                        )}
                                    </div>
                                ) : (
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="border-white/10 hover:bg-transparent">
                                                <TableHead className="text-gray-400">Reference</TableHead>
                                                <TableHead className="text-gray-400">Title</TableHead>
                                                <TableHead className="text-gray-400">Counterparty</TableHead>
                                                <TableHead className="text-gray-400">Amount</TableHead>
                                                <TableHead className="text-gray-400">Status</TableHead>
                                                <TableHead className="text-gray-400">Date</TableHead>
                                                <TableHead className="text-gray-400 text-right">Actions</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {filteredEscrows.map((escrow) => (
                                                <TableRow
                                                    key={escrow.id}
                                                    className="border-white/10 hover:bg-white/5"
                                                >
                                                    <TableCell className="font-mono text-sm">
                                                        {escrow.reference_code}
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="max-w-[200px] truncate font-medium">
                                                            {escrow.title}
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="text-sm text-gray-400">
                                                            {escrow.seller?.email || escrow.buyer?.email}
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="font-semibold">
                                                        {formatCurrency(escrow.total_amount, escrow.currency)}
                                                    </TableCell>
                                                    <TableCell>
                                                        <EscrowStatusBadge status={escrow.status} size="sm" />
                                                    </TableCell>
                                                    <TableCell className="text-gray-400 text-sm">
                                                        {formatDate(escrow.created_at)}
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        <Link href={`/escrows/${escrow.id}`}>
                                                            <Button variant="ghost" size="sm">
                                                                <Eye className="w-4 h-4" />
                                                            </Button>
                                                        </Link>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </div>
        </DashboardLayout>
    );
}
