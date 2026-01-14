/**
 * M-Pesa Payment Modal Component
 * Handles STK Push payment flow
 */
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
    Loader2,
    Phone,
    CheckCircle2,
    XCircle,
    AlertTriangle,
    Smartphone,
} from 'lucide-react';

interface MpesaPaymentModalProps {
    isOpen: boolean;
    onClose: () => void;
    escrowId: string;
    amount: number;
    currency: string;
    onSuccess?: () => void;
}

type PaymentStatus = 'idle' | 'initiating' | 'waiting' | 'success' | 'failed';

export function MpesaPaymentModal({
    isOpen,
    onClose,
    escrowId,
    amount,
    currency,
    onSuccess,
}: MpesaPaymentModalProps) {
    const [phoneNumber, setPhoneNumber] = useState('');
    const [status, setStatus] = useState<PaymentStatus>('idle');
    const [checkoutRequestId, setCheckoutRequestId] = useState('');
    const [error, setError] = useState('');
    const [pollCount, setPollCount] = useState(0);

    // Format phone number for display
    const formatPhoneDisplay = (phone: string) => {
        const clean = phone.replace(/\D/g, '');
        if (clean.startsWith('254')) {
            return `+${clean}`;
        }
        if (clean.startsWith('0')) {
            return `+254${clean.slice(1)}`;
        }
        if (clean.startsWith('7') || clean.startsWith('1')) {
            return `+254${clean}`;
        }
        return phone;
    };

    // Format currency
    const formatCurrency = (amt: number) => {
        return new Intl.NumberFormat('en-KE', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
        }).format(amt);
    };

    // Poll for payment status
    useEffect(() => {
        let interval: NodeJS.Timeout;

        if (status === 'waiting' && checkoutRequestId) {
            interval = setInterval(async () => {
                try {
                    const result = await api.mpesa.status(checkoutRequestId);

                    if (result.status === 'completed') {
                        setStatus('success');
                        clearInterval(interval);
                    } else if (result.status === 'failed') {
                        setStatus('failed');
                        setError(result.message || 'Payment was not completed');
                        clearInterval(interval);
                    }

                    setPollCount((prev) => prev + 1);

                    // Stop polling after 2 minutes
                    if (pollCount >= 24) {
                        clearInterval(interval);
                        setStatus('failed');
                        setError('Payment timed out. Please try again.');
                    }
                } catch (err) {
                    console.error('Status check failed:', err);
                }
            }, 5000); // Poll every 5 seconds
        }

        return () => clearInterval(interval);
    }, [status, checkoutRequestId, pollCount]);

    const handleInitiatePayment = async () => {
        if (!phoneNumber) {
            setError('Please enter your M-Pesa phone number');
            return;
        }

        setStatus('initiating');
        setError('');

        try {
            const result = await api.mpesa.initiate(escrowId, phoneNumber, amount);

            if (result.success) {
                setCheckoutRequestId(result.checkout_request_id);
                setStatus('waiting');
                setPollCount(0);
            } else {
                setStatus('failed');
                setError(result.message || 'Failed to initiate payment');
            }
        } catch (err: any) {
            setStatus('failed');
            setError(err.message || 'Failed to initiate payment');
        }
    };

    const handleClose = () => {
        if (status !== 'initiating' && status !== 'waiting') {
            setStatus('idle');
            setError('');
            setPollCount(0);
            setCheckoutRequestId('');
            onClose();
        }
    };

    const handleSuccessClose = () => {
        onSuccess?.();
        handleClose();
    };

    const renderContent = () => {
        switch (status) {
            case 'idle':
                return (
                    <div className="space-y-6">
                        <div className="text-center p-6 rounded-xl bg-green-500/10 border border-green-500/20">
                            <p className="text-3xl font-bold text-green-400">
                                {formatCurrency(amount)}
                            </p>
                            <p className="text-sm text-gray-400 mt-1">Amount to pay</p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="phone">M-Pesa Phone Number</Label>
                            <div className="relative">
                                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                <Input
                                    id="phone"
                                    type="tel"
                                    placeholder="0712 345 678"
                                    value={phoneNumber}
                                    onChange={(e) => setPhoneNumber(e.target.value)}
                                    className="pl-10 bg-white/5 border-white/10"
                                />
                            </div>
                            <p className="text-xs text-gray-400">
                                {phoneNumber && `Will send STK to ${formatPhoneDisplay(phoneNumber)}`}
                            </p>
                        </div>

                        {error && (
                            <Alert variant="destructive" className="bg-red-500/10 border-red-500/20">
                                <AlertTriangle className="h-4 w-4" />
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        <Button
                            onClick={handleInitiatePayment}
                            className="w-full bg-green-500 hover:bg-green-600"
                        >
                            Pay with M-Pesa
                        </Button>
                    </div>
                );

            case 'initiating':
                return (
                    <div className="text-center py-8 space-y-4">
                        <Loader2 className="w-12 h-12 mx-auto text-green-400 animate-spin" />
                        <p className="font-medium">Initiating payment...</p>
                        <p className="text-sm text-gray-400">
                            Please wait while we send the STK push to your phone
                        </p>
                    </div>
                );

            case 'waiting':
                return (
                    <div className="text-center py-8 space-y-6">
                        <div className="relative">
                            <div className="w-20 h-20 mx-auto rounded-full bg-green-500/20 flex items-center justify-center animate-pulse">
                                <Smartphone className="w-10 h-10 text-green-400" />
                            </div>
                            <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center">
                                <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />
                            </div>
                        </div>

                        <div>
                            <p className="font-medium text-lg">Check your phone</p>
                            <p className="text-sm text-gray-400 mt-1">
                                Enter your M-Pesa PIN on the popup to complete payment
                            </p>
                        </div>

                        <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                            <p className="text-sm text-yellow-400">
                                If you don't see the prompt, dial *334# on your phone
                            </p>
                        </div>

                        <p className="text-xs text-gray-500">
                            Waiting for confirmation... ({Math.floor(pollCount * 5 / 60)}:{String((pollCount * 5) % 60).padStart(2, '0')})
                        </p>
                    </div>
                );

            case 'success':
                return (
                    <div className="text-center py-8 space-y-6">
                        <div className="w-20 h-20 mx-auto rounded-full bg-green-500/20 flex items-center justify-center">
                            <CheckCircle2 className="w-10 h-10 text-green-400" />
                        </div>

                        <div>
                            <p className="font-medium text-lg text-green-400">Payment Successful!</p>
                            <p className="text-sm text-gray-400 mt-1">
                                {formatCurrency(amount)} has been received
                            </p>
                        </div>

                        <Button onClick={handleSuccessClose} className="w-full">
                            Continue
                        </Button>
                    </div>
                );

            case 'failed':
                return (
                    <div className="text-center py-8 space-y-6">
                        <div className="w-20 h-20 mx-auto rounded-full bg-red-500/20 flex items-center justify-center">
                            <XCircle className="w-10 h-10 text-red-400" />
                        </div>

                        <div>
                            <p className="font-medium text-lg text-red-400">Payment Failed</p>
                            <p className="text-sm text-gray-400 mt-1">{error}</p>
                        </div>

                        <div className="flex gap-3">
                            <Button variant="outline" onClick={handleClose} className="flex-1">
                                Cancel
                            </Button>
                            <Button
                                onClick={() => setStatus('idle')}
                                className="flex-1 bg-green-500 hover:bg-green-600"
                            >
                                Try Again
                            </Button>
                        </div>
                    </div>
                );
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="glass-card border-white/10 sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                            <Phone className="w-4 h-4 text-green-400" />
                        </div>
                        M-Pesa Payment
                    </DialogTitle>
                    <DialogDescription>
                        Secure mobile payment via Safaricom M-Pesa
                    </DialogDescription>
                </DialogHeader>

                {renderContent()}
            </DialogContent>
        </Dialog>
    );
}
