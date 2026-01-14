/**
 * Dispute Creation Page
 */
import { useState, useEffect } from 'react';
import { useLocation, useSearch } from 'wouter';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
    ArrowLeft,
    AlertTriangle,
    Loader2,
    Upload,
    FileText,
} from 'lucide-react';

const disputeReasons = [
    { value: 'not_as_described', label: 'Item/Service Not as Described' },
    { value: 'not_received', label: 'Item/Service Not Received' },
    { value: 'quality_issues', label: 'Quality Issues' },
    { value: 'late_delivery', label: 'Late Delivery' },
    { value: 'partial_delivery', label: 'Partial Delivery' },
    { value: 'fraud', label: 'Suspected Fraud' },
    { value: 'other', label: 'Other' },
];

export default function CreateDispute() {
    const [, setLocation] = useLocation();
    const searchString = useSearch();
    const params = new URLSearchParams(searchString);
    const escrowId = params.get('escrow');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [escrow, setEscrow] = useState<any>(null);

    const [formData, setFormData] = useState({
        reason: '',
        description: '',
        disputed_amount: '',
        evidence_description: '',
    });

    useEffect(() => {
        if (escrowId) {
            fetchEscrow();
        }
    }, [escrowId]);

    const fetchEscrow = async () => {
        try {
            const data = await api.escrow.get(escrowId!);
            setEscrow(data);
            setFormData((prev) => ({
                ...prev,
                disputed_amount: String(data.total_amount),
            }));
        } catch (err) {
            console.error('Failed to fetch escrow:', err);
        }
    };

    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            // 1. Create Dispute
            const result = await api.disputes.create({
                escrow_id: escrowId!,
                reason: formData.reason,
                description: formData.description,
                disputed_amount: parseFloat(formData.disputed_amount),
            });

            // 2. Upload Evidence (if selected)
            if (selectedFile) {
                const evidenceData = new FormData();
                evidenceData.append('file', selectedFile);
                evidenceData.append('title', 'Initial Evidence');
                evidenceData.append('description', formData.evidence_description || 'Evidence submitted with dispute creation');
                evidenceData.append('evidence_type', 'document');

                await api.disputes.submitEvidence(result.id, evidenceData);
            }

            setLocation(`/disputes/${result.id}`);
        } catch (err: any) {
            setError(err.message || 'Failed to create dispute');
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

    return (
        <DashboardLayout>
            <div className="max-w-2xl mx-auto space-y-6">
                {/* Header */}
                <div>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="mb-2 -ml-2"
                        onClick={() => window.history.back()}
                    >
                        <ArrowLeft className="w-4 h-4 mr-1" />
                        Back
                    </Button>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <AlertTriangle className="w-6 h-6 text-red-400" />
                        Raise a Dispute
                    </h1>
                    <p className="text-gray-400 mt-1">
                        Report an issue with your escrow transaction
                    </p>
                </div>

                {/* Escrow Info */}
                {escrow && (
                    <Card className="glass-card border-white/10">
                        <CardContent className="pt-6">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-sm text-gray-400">Escrow</p>
                                    <p className="font-medium">{escrow.title}</p>
                                    <p className="text-xs text-gray-500 font-mono">{escrow.reference_code}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm text-gray-400">Amount</p>
                                    <p className="font-bold text-lg">
                                        {formatCurrency(escrow.total_amount, escrow.currency)}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Dispute Form */}
                <Card className="glass-card border-white/10">
                    <CardHeader>
                        <CardTitle>Dispute Details</CardTitle>
                        <CardDescription>
                            Please provide details about your dispute. Our arbitration team will review it.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-6">
                            {error && (
                                <Alert variant="destructive" className="bg-red-500/10 border-red-500/20">
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}

                            <div className="space-y-2">
                                <Label>Reason for Dispute *</Label>
                                <Select
                                    value={formData.reason}
                                    onValueChange={(v) => setFormData((prev) => ({ ...prev, reason: v }))}
                                >
                                    <SelectTrigger className="bg-white/5 border-white/10">
                                        <SelectValue placeholder="Select a reason" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {disputeReasons.map((reason) => (
                                            <SelectItem key={reason.value} value={reason.value}>
                                                {reason.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="description">Description *</Label>
                                <Textarea
                                    id="description"
                                    placeholder="Describe the issue in detail..."
                                    value={formData.description}
                                    onChange={(e) =>
                                        setFormData((prev) => ({ ...prev, description: e.target.value }))
                                    }
                                    className="bg-white/5 border-white/10 min-h-[150px]"
                                    required
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="disputed_amount">Disputed Amount</Label>
                                <Input
                                    id="disputed_amount"
                                    type="number"
                                    value={formData.disputed_amount}
                                    onChange={(e) =>
                                        setFormData((prev) => ({ ...prev, disputed_amount: e.target.value }))
                                    }
                                    className="bg-white/5 border-white/10"
                                />
                                <p className="text-xs text-gray-400">
                                    The amount you believe should be refunded or adjusted
                                </p>
                            </div>

                            <div className="space-y-2">
                                <Label>Evidence (Optional)</Label>
                                <div className="border-2 border-dashed border-white/10 rounded-xl p-6 text-center">
                                    <input
                                        type="file"
                                        id="evidence-upload"
                                        className="hidden"
                                        onChange={handleFileChange}
                                    />
                                    <label
                                        htmlFor="evidence-upload"
                                        className="cursor-pointer flex flex-col items-center justify-center"
                                    >
                                        <Upload className={`w-8 h-8 mx-auto mb-2 ${selectedFile ? 'text-green-400' : 'text-gray-400'}`} />
                                        <p className="text-sm text-gray-400">
                                            {selectedFile ? selectedFile.name : 'Click to select a file'}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {selectedFile ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : 'Screenshots, contracts, messages, etc.'}
                                        </p>
                                    </label>
                                </div>
                                {selectedFile && (
                                    <div className="mt-2 text-right">
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            className="text-red-400 hover:text-red-300 h-6 text-xs"
                                            onClick={() => setSelectedFile(null)}
                                        >
                                            Remove
                                        </Button>
                                    </div>
                                )}
                            </div>

                            <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                                <div className="flex gap-3">
                                    <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                                    <p className="text-sm text-yellow-400">
                                        Once submitted, the escrow will be placed on hold until the dispute is resolved.
                                        Both parties will be notified and given a chance to respond.
                                    </p>
                                </div>
                            </div>

                            <div className="flex gap-3">
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="flex-1 border-white/10"
                                    onClick={() => window.history.back()}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    type="submit"
                                    disabled={loading || !formData.reason || !formData.description}
                                    className="flex-1 bg-red-500 hover:bg-red-600"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Submitting...
                                        </>
                                    ) : (
                                        'Submit Dispute'
                                    )}
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
