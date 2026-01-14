/**
 * Escrow Creation Wizard
 * Multi-step form for creating new escrows with milestones
 */
import { useState } from 'react';
import { useLocation } from 'wouter';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
    ArrowLeft,
    ArrowRight,
    Check,
    Plus,
    Trash2,
    Loader2,
    Briefcase,
    Users,
    ListChecks,
    CreditCard,
} from 'lucide-react';

interface Milestone {
    title: string;
    description: string;
    amount: string;
    order: number;
}

interface EscrowFormData {
    title: string;
    description: string;
    escrow_type: string;
    total_amount: string;
    currency: string;
    seller_email: string;
    inspection_days: number;
    auto_release_days: number;
    milestones: Milestone[];
}

const steps = [
    { id: 1, name: 'Basic Info', icon: Briefcase },
    { id: 2, name: 'Parties', icon: Users },
    { id: 3, name: 'Milestones', icon: ListChecks },
    { id: 4, name: 'Review', icon: CreditCard },
];

const escrowTypes = [
    { value: 'product', label: 'Product Purchase' },
    { value: 'service', label: 'Service Agreement' },
    { value: 'milestone', label: 'Milestone-Based Project' },
    { value: 'domain', label: 'Domain/Asset Transfer' },
];

const currencies = [
    { value: 'KES', label: 'Kenyan Shilling (KES)' },
    { value: 'USD', label: 'US Dollar (USD)' },
    { value: 'EUR', label: 'Euro (EUR)' },
];

export default function CreateEscrow() {
    const { user } = useAuth();
    const [, setLocation] = useLocation();
    const [currentStep, setCurrentStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [formData, setFormData] = useState<EscrowFormData>({
        title: '',
        description: '',
        escrow_type: 'service',
        total_amount: '',
        currency: 'KES',
        seller_email: '',
        inspection_days: 3,
        auto_release_days: 14,
        milestones: [{ title: '', description: '', amount: '', order: 1 }],
    });

    // Plan & Fee Logic
    const plan = user?.effective_plan;
    const feePercent = plan?.fee_percent ? parseFloat(plan.fee_percent) : 2.5;
    const maxLimit = plan?.max_transaction_limit ? parseFloat(plan.max_transaction_limit) : Infinity;

    const calculateFee = () => {
        const amount = parseFloat(formData.total_amount) || 0;
        return (amount * feePercent) / 100;
    };

    const updateField = (field: keyof EscrowFormData, value: any) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const addMilestone = () => {
        setFormData((prev) => ({
            ...prev,
            milestones: [
                ...prev.milestones,
                { title: '', description: '', amount: '', order: prev.milestones.length + 1 },
            ],
        }));
    };

    const removeMilestone = (index: number) => {
        if (formData.milestones.length > 1) {
            setFormData((prev) => ({
                ...prev,
                milestones: prev.milestones
                    .filter((_, i) => i !== index)
                    .map((m, i) => ({ ...m, order: i + 1 })),
            }));
        }
    };

    const updateMilestone = (index: number, field: keyof Milestone, value: string) => {
        setFormData((prev) => ({
            ...prev,
            milestones: prev.milestones.map((m, i) =>
                i === index ? { ...m, [field]: value } : m
            ),
        }));
    };

    const calculateMilestoneTotal = () => {
        return formData.milestones.reduce(
            (sum, m) => sum + (parseFloat(m.amount) || 0),
            0
        );
    };

    const validateStep = (step: number): boolean => {
        const amount = parseFloat(formData.total_amount) || 0;

        switch (step) {
            case 1:
                const basicValid = !!formData.title && !!formData.escrow_type && !!formData.total_amount;
                // Enforce Plan Limit
                if (maxLimit !== Infinity && amount > maxLimit) {
                    return false;
                }
                return basicValid;
            case 2:
                return !!formData.seller_email;
            case 3:
                const total = calculateMilestoneTotal();
                return formData.milestones.every((m) => m.title && m.amount) &&
                    Math.abs(total - amount) < 0.01;
            default:
                return true;
        }
    };

    const handleNext = () => {
        if (validateStep(currentStep)) {
            setCurrentStep((prev) => Math.min(prev + 1, 4));
        }
    };

    const handleBack = () => {
        setCurrentStep((prev) => Math.max(prev - 1, 1));
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError('');

        try {
            const payload = {
                title: formData.title,
                description: formData.description,
                escrow_type: formData.escrow_type,
                total_amount: parseFloat(formData.total_amount),
                currency: formData.currency,
                seller_email: formData.seller_email,
                inspection_period_days: formData.inspection_days,
                auto_release_days: formData.auto_release_days,
                milestones: formData.milestones.map((m) => ({
                    title: m.title,
                    description: m.description,
                    amount: parseFloat(m.amount),
                    order: m.order,
                })),
            };

            const result = await api.escrow.create(payload);
            setLocation(`/escrows/${result.id}`);
        } catch (err: any) {
            setError(err.message || 'Failed to create escrow');
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-KE', {
            style: 'currency',
            currency: formData.currency,
            minimumFractionDigits: 0,
        }).format(amount);
    };

    return (
        <DashboardLayout>
            <div className="max-w-3xl mx-auto space-y-8">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold">Create New Escrow</h1>
                    <p className="text-gray-400 mt-1">
                        Set up a secure transaction with milestone-based payments
                    </p>
                </div>

                {/* Progress Steps */}
                <div className="flex items-center justify-between">
                    {steps.map((step, index) => {
                        const isActive = currentStep === step.id;
                        const isCompleted = currentStep > step.id;
                        const Icon = step.icon;

                        return (
                            <div key={step.id} className="flex items-center">
                                <div
                                    className={`flex items-center justify-center w-10 h-10 rounded-full transition-all ${isCompleted
                                        ? 'bg-green-500'
                                        : isActive
                                            ? 'bg-blue-500'
                                            : 'bg-white/10'
                                        }`}
                                >
                                    {isCompleted ? (
                                        <Check className="w-5 h-5 text-white" />
                                    ) : (
                                        <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                                    )}
                                </div>
                                <span
                                    className={`ml-2 text-sm hidden sm:block ${isActive ? 'text-white font-medium' : 'text-gray-400'
                                        }`}
                                >
                                    {step.name}
                                </span>
                                {index < steps.length - 1 && (
                                    <div
                                        className={`w-8 sm:w-16 h-0.5 mx-2 ${isCompleted ? 'bg-green-500' : 'bg-white/10'
                                            }`}
                                    />
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Form Card */}
                <Card className="glass-card border-white/10">
                    <CardContent className="pt-6">
                        {error && (
                            <Alert variant="destructive" className="mb-6 bg-red-500/10 border-red-500/20">
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        {/* Step 1: Basic Info */}
                        {currentStep === 1 && (
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <Label htmlFor="title">Escrow Title *</Label>
                                    <Input
                                        id="title"
                                        placeholder="e.g., Website Development Project"
                                        value={formData.title}
                                        onChange={(e) => updateField('title', e.target.value)}
                                        className="bg-white/5 border-white/10"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="description">Description</Label>
                                    <Textarea
                                        id="description"
                                        placeholder="Describe the transaction details..."
                                        value={formData.description}
                                        onChange={(e) => updateField('description', e.target.value)}
                                        className="bg-white/5 border-white/10 min-h-[100px]"
                                    />
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Escrow Type *</Label>
                                        <Select
                                            value={formData.escrow_type}
                                            onValueChange={(v) => updateField('escrow_type', v)}
                                        >
                                            <SelectTrigger className="bg-white/5 border-white/10">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {escrowTypes.map((type) => (
                                                    <SelectItem key={type.value} value={type.value}>
                                                        {type.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Currency</Label>
                                        <Select
                                            value={formData.currency}
                                            onValueChange={(v) => updateField('currency', v)}
                                        >
                                            <SelectTrigger className="bg-white/5 border-white/10">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {currencies.map((c) => (
                                                    <SelectItem key={c.value} value={c.value}>
                                                        {c.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <Label htmlFor="amount">Total Amount *</Label>
                                        {maxLimit !== Infinity && (
                                            <span className="text-xs text-gray-400">
                                                Plan Limit: {formatCurrency(maxLimit)}
                                            </span>
                                        )}
                                    </div>
                                    <Input
                                        id="amount"
                                        type="number"
                                        placeholder="0.00"
                                        value={formData.total_amount}
                                        onChange={(e) => updateField('total_amount', e.target.value)}
                                        className={`bg-white/5 border-white/10 ${parseFloat(formData.total_amount) > maxLimit ? 'border-red-500' : ''
                                            }`}
                                    />
                                    {parseFloat(formData.total_amount) > maxLimit && (
                                        <p className="text-xs text-red-400">
                                            Amount exceeds your {plan?.name || 'current'} plan limit.
                                        </p>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Step 2: Parties */}
                        {currentStep === 2 && (
                            <div className="space-y-6">
                                <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                                    <p className="text-sm text-blue-400">
                                        <strong>You are the Buyer.</strong> You will fund the escrow and release
                                        payments when milestones are completed.
                                    </p>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="seller_email">Seller's Email *</Label>
                                    <Input
                                        id="seller_email"
                                        type="email"
                                        placeholder="seller@example.com"
                                        value={formData.seller_email}
                                        onChange={(e) => updateField('seller_email', e.target.value)}
                                        className="bg-white/5 border-white/10"
                                    />
                                    <p className="text-xs text-gray-400">
                                        An invitation will be sent to this email address
                                    </p>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="inspection_days">Inspection Period (days)</Label>
                                        <Input
                                            id="inspection_days"
                                            type="number"
                                            min="1"
                                            max="30"
                                            value={formData.inspection_days}
                                            onChange={(e) => updateField('inspection_days', parseInt(e.target.value))}
                                            className="bg-white/5 border-white/10"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="auto_release_days">Auto-release After (days)</Label>
                                        <div className="flex items-center gap-2">
                                            <Input
                                                id="auto_release_days"
                                                type="number"
                                                min="1"
                                                max="60"
                                                value={formData.auto_release_days}
                                                onChange={(e) => updateField('auto_release_days', parseInt(e.target.value))}
                                                className="bg-white/5 border-white/10"
                                            />
                                            {plan?.sla_hours && (
                                                <div className="text-xs bg-white/10 px-2 py-1 rounded whitespace-nowrap">
                                                    SLA: {plan.sla_hours}h
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Step 3: Milestones */}
                        {currentStep === 3 && (
                            <div className="space-y-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="font-medium">Payment Milestones</h3>
                                        <p className="text-sm text-gray-400">
                                            Split the total amount into milestones
                                        </p>
                                    </div>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={addMilestone}
                                        className="border-white/10"
                                    >
                                        <Plus className="w-4 h-4 mr-1" />
                                        Add
                                    </Button>
                                </div>

                                <div className="space-y-4">
                                    {formData.milestones.map((milestone, index) => (
                                        <div
                                            key={index}
                                            className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-4"
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm text-gray-400">
                                                    Milestone {index + 1}
                                                </span>
                                                {formData.milestones.length > 1 && (
                                                    <Button
                                                        type="button"
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => removeMilestone(index)}
                                                        className="text-red-400 hover:text-red-300"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                )}
                                            </div>

                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                <div className="md:col-span-2 space-y-2">
                                                    <Label>Title *</Label>
                                                    <Input
                                                        placeholder="Milestone title"
                                                        value={milestone.title}
                                                        onChange={(e) =>
                                                            updateMilestone(index, 'title', e.target.value)
                                                        }
                                                        className="bg-white/5 border-white/10"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <Label>Amount *</Label>
                                                    <Input
                                                        type="number"
                                                        placeholder="0.00"
                                                        value={milestone.amount}
                                                        onChange={(e) =>
                                                            updateMilestone(index, 'amount', e.target.value)
                                                        }
                                                        className="bg-white/5 border-white/10"
                                                    />
                                                </div>
                                            </div>

                                            <div className="space-y-2">
                                                <Label>Description</Label>
                                                <Input
                                                    placeholder="What will be delivered"
                                                    value={milestone.description}
                                                    onChange={(e) =>
                                                        updateMilestone(index, 'description', e.target.value)
                                                    }
                                                    className="bg-white/5 border-white/10"
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {/* Total validation */}
                                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-400">Milestone Total:</span>
                                        <span
                                            className={`font-bold ${Math.abs(
                                                calculateMilestoneTotal() -
                                                (parseFloat(formData.total_amount) || 0)
                                            ) < 0.01
                                                ? 'text-green-400'
                                                : 'text-red-400'
                                                }`}
                                        >
                                            {formatCurrency(calculateMilestoneTotal())}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center mt-2">
                                        <span className="text-gray-400">Escrow Total:</span>
                                        <span className="font-bold">
                                            {formatCurrency(parseFloat(formData.total_amount) || 0)}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Step 4: Review */}
                        {currentStep === 4 && (
                            <div className="space-y-6">
                                <h3 className="font-medium text-lg">Review Your Escrow</h3>

                                <div className="space-y-4">
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                        <h4 className="text-sm text-gray-400 mb-2">Transaction Details</h4>
                                        <p className="font-medium">{formData.title}</p>
                                        <p className="text-sm text-gray-400 mt-1">{formData.description}</p>
                                        <div className="flex items-center gap-4 mt-3">
                                            <span className="text-2xl font-bold text-green-400">
                                                {formatCurrency(parseFloat(formData.total_amount) || 0)}
                                            </span>
                                            <span className="text-sm text-gray-400 capitalize">
                                                {formData.escrow_type.replace('_', ' ')} Escrow
                                            </span>
                                        </div>
                                    </div>

                                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                        <h4 className="text-sm text-gray-400 mb-2">Seller</h4>
                                        <p className="font-medium">{formData.seller_email}</p>
                                        <p className="text-sm text-gray-400 mt-1">
                                            {formData.inspection_days} day inspection • {formData.auto_release_days} day auto-release
                                        </p>
                                    </div>

                                    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                        <h4 className="text-sm text-gray-400 mb-2">
                                            Milestones ({formData.milestones.length})
                                        </h4>
                                        <div className="space-y-2">
                                            {formData.milestones.map((m, i) => (
                                                <div key={i} className="flex justify-between">
                                                    <span>{m.title}</span>
                                                    <span className="font-medium">
                                                        {formatCurrency(parseFloat(m.amount) || 0)}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-sm text-blue-400 font-medium">Estimated Platform Fee ({feePercent}%)</span>
                                            <span className="text-sm font-bold text-blue-400">
                                                {formatCurrency(calculateFee())}
                                            </span>
                                        </div>
                                        <p className="text-xs text-blue-300/70">
                                            Charged upon successful completion. {plan?.name ? `Applied via ${plan.name} Plan.` : ''}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Navigation */}
                        <div className="flex justify-between mt-8 pt-6 border-t border-white/10">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={handleBack}
                                disabled={currentStep === 1}
                                className="border-white/10"
                            >
                                <ArrowLeft className="w-4 h-4 mr-2" />
                                Back
                            </Button>

                            {currentStep < 4 ? (
                                <Button
                                    type="button"
                                    onClick={handleNext}
                                    disabled={!validateStep(currentStep)}
                                    className="bg-blue-500 hover:bg-blue-600"
                                >
                                    Next
                                    <ArrowRight className="w-4 h-4 ml-2" />
                                </Button>
                            ) : (
                                <Button
                                    type="button"
                                    onClick={handleSubmit}
                                    disabled={loading}
                                    className="bg-green-500 hover:bg-green-600"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Creating...
                                        </>
                                    ) : (
                                        <>
                                            <Check className="w-4 h-4 mr-2" />
                                            Create Escrow
                                        </>
                                    )}
                                </Button>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
