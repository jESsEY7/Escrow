import type { Express } from "express";
import type { AuthRequest } from "../middleware/auth.middleware";
import { authenticate, requireRole, requireVerified } from "../middleware/auth.middleware";
import { escrowLimiter } from "../middleware/security.middleware";
import { db } from "../db";
import { escrowAccounts, assets, transactions, users } from "@shared/schema";
import { insertEscrowAccountSchema, insertAssetSchema, insertTransactionSchema } from "@shared/schema";
import { auditService } from "../services/audit.service";
import { eq, and, or } from "drizzle-orm";
import { ZodError } from "zod";

export function registerEscrowRoutes(app: Express) {
  /**
   * Create new escrow account
   */
  app.post("/api/escrow/accounts", authenticate, requireVerified, escrowLimiter, async (req: AuthRequest, res) => {
    try {
      const validatedData = insertEscrowAccountSchema.parse(req.body);
      
      // Verify both buyer and seller exist
      const [buyer, seller] = await Promise.all([
        db.query.users.findFirst({ where: eq(users.id, validatedData.buyerId) }),
        db.query.users.findFirst({ where: eq(users.id, validatedData.sellerId) }),
      ]);

      if (!buyer || !seller) {
        return res.status(404).json({ message: "Buyer or seller not found" });
      }

      // Ensure both are verified
      if (buyer.status !== "active" || seller.status !== "active") {
        return res.status(403).json({ 
          message: "Both buyer and seller must have active accounts" 
        });
      }

      // Create escrow account
      const [newEscrowAccount] = await db.insert(escrowAccounts)
        .values(validatedData)
        .returning();

      // Audit log
      await auditService.log({
        action: "escrow.create",
        entity: `escrow:${newEscrowAccount.id}`,
        actorId: req.user!.userId,
        snapshot: newEscrowAccount,
      });

      res.status(201).json({
        success: true,
        escrowAccount: newEscrowAccount,
      });
    } catch (error) {
      if (error instanceof ZodError) {
        return res.status(400).json({ message: "Validation error", errors: error.errors });
      }
      console.error("Create escrow error:", error);
      res.status(500).json({ message: "Failed to create escrow account" });
    }
  });

  /**
   * Get escrow account by ID
   */
  app.get("/api/escrow/accounts/:id", authenticate, async (req: AuthRequest, res) => {
    try {
      const escrowAccount = await db.query.escrowAccounts.findFirst({
        where: eq(escrowAccounts.id, req.params.id),
        with: {
          buyer: true,
          seller: true,
          assets: true,
          transactions: true,
          disputes: true,
        },
      });

      if (!escrowAccount) {
        return res.status(404).json({ message: "Escrow account not found" });
      }

      // Authorization: only buyer, seller, or admin can view
      const isAuthorized = 
        escrowAccount.buyerId === req.user!.userId ||
        escrowAccount.sellerId === req.user!.userId ||
        req.user!.role === "admin" ||
        req.user!.role === "arbitrator";

      if (!isAuthorized) {
        return res.status(403).json({ message: "Unauthorized access" });
      }

      res.json({ escrowAccount });
    } catch (error) {
      console.error("Get escrow error:", error);
      res.status(500).json({ message: "Failed to retrieve escrow account" });
    }
  });

  /**
   * Get all escrow accounts for current user
   */
  app.get("/api/escrow/accounts", authenticate, async (req: AuthRequest, res) => {
    try {
      const userId = req.user!.userId;

      const userEscrowAccounts = await db.query.escrowAccounts.findMany({
        where: or(
          eq(escrowAccounts.buyerId, userId),
          eq(escrowAccounts.sellerId, userId)
        ),
        with: {
          buyer: true,
          seller: true,
          assets: true,
        },
        orderBy: (accounts, { desc }) => [desc(accounts.createdAt)],
      });

      res.json({ escrowAccounts: userEscrowAccounts });
    } catch (error) {
      console.error("Get escrow accounts error:", error);
      res.status(500).json({ message: "Failed to retrieve escrow accounts" });
    }
  });

  /**
   * Add asset to escrow account
   */
  app.post("/api/escrow/accounts/:id/assets", authenticate, requireVerified, escrowLimiter, async (req: AuthRequest, res) => {
    try {
      const escrowAccount = await db.query.escrowAccounts.findFirst({
        where: eq(escrowAccounts.id, req.params.id),
      });

      if (!escrowAccount) {
        return res.status(404).json({ message: "Escrow account not found" });
      }

      // Only buyer can add assets
      if (escrowAccount.buyerId !== req.user!.userId) {
        return res.status(403).json({ message: "Only the buyer can add assets" });
      }

      const validatedData = insertAssetSchema.parse({
        ...req.body,
        escrowAccountId: req.params.id,
      });

      const [newAsset] = await db.insert(assets)
        .values(validatedData)
        .returning();

      // Update escrow status to funded
      await db.update(escrowAccounts)
        .set({ status: "funded" })
        .where(eq(escrowAccounts.id, req.params.id));

      // Audit log
      await auditService.log({
        action: "escrow.fund",
        entity: `escrow:${req.params.id}`,
        actorId: req.user!.userId,
        snapshot: newAsset,
      });

      res.status(201).json({ success: true, asset: newAsset });
    } catch (error) {
      if (error instanceof ZodError) {
        return res.status(400).json({ message: "Validation error", errors: error.errors });
      }
      console.error("Add asset error:", error);
      res.status(500).json({ message: "Failed to add asset" });
    }
  });

  /**
   * Release funds (complete escrow)
   */
  app.post("/api/escrow/accounts/:id/release", authenticate, requireVerified, escrowLimiter, async (req: AuthRequest, res) => {
    try {
      const escrowAccount = await db.query.escrowAccounts.findFirst({
        where: eq(escrowAccounts.id, req.params.id),
        with: { assets: true },
      });

      if (!escrowAccount) {
        return res.status(404).json({ message: "Escrow account not found" });
      }

      // Only buyer can release funds
      if (escrowAccount.buyerId !== req.user!.userId) {
        return res.status(403).json({ message: "Only the buyer can release funds" });
      }

      // Check escrow status
      if (escrowAccount.status !== "funded" && escrowAccount.status !== "in_progress") {
        return res.status(400).json({ 
          message: "Escrow must be funded or in progress to release",
          currentStatus: escrowAccount.status,
        });
      }

      // Create release transaction
      const totalAmount = escrowAccount.assets.reduce(
        (sum, asset) => sum + parseFloat(asset.amount),
        0
      );

      const [transaction] = await db.insert(transactions).values({
        escrowAccountId: req.params.id,
        type: "release",
        amount: totalAmount.toString(),
        currency: escrowAccount.assets[0]?.currency || "USD",
        status: "completed",
        initiatedBy: req.user!.userId,
        completedAt: new Date(),
      }).returning();

      // Update escrow status
      await db.update(escrowAccounts)
        .set({ status: "completed" })
        .where(eq(escrowAccounts.id, req.params.id));

      // Audit log
      await auditService.log({
        action: "escrow.release",
        entity: `escrow:${req.params.id}`,
        actorId: req.user!.userId,
        snapshot: { transactionId: transaction.id, amount: totalAmount },
      });

      res.json({ 
        success: true, 
        message: "Funds released successfully",
        transaction,
      });
    } catch (error) {
      console.error("Release funds error:", error);
      res.status(500).json({ message: "Failed to release funds" });
    }
  });

  /**
   * Refund escrow (cancel transaction)
   */
  app.post("/api/escrow/accounts/:id/refund", authenticate, requireVerified, escrowLimiter, async (req: AuthRequest, res) => {
    try {
      const escrowAccount = await db.query.escrowAccounts.findFirst({
        where: eq(escrowAccounts.id, req.params.id),
        with: { assets: true },
      });

      if (!escrowAccount) {
        return res.status(404).json({ message: "Escrow account not found" });
      }

      // Seller or admin can initiate refund
      const canRefund = 
        escrowAccount.sellerId === req.user!.userId ||
        req.user!.role === "admin" ||
        req.user!.role === "arbitrator";

      if (!canRefund) {
        return res.status(403).json({ message: "Unauthorized to refund" });
      }

      // Create refund transaction
      const totalAmount = escrowAccount.assets.reduce(
        (sum, asset) => sum + parseFloat(asset.amount),
        0
      );

      const [transaction] = await db.insert(transactions).values({
        escrowAccountId: req.params.id,
        type: "refund",
        amount: totalAmount.toString(),
        currency: escrowAccount.assets[0]?.currency || "USD",
        status: "completed",
        initiatedBy: req.user!.userId,
        completedAt: new Date(),
      }).returning();

      // Update escrow status
      await db.update(escrowAccounts)
        .set({ status: "refunded" })
        .where(eq(escrowAccounts.id, req.params.id));

      // Audit log
      await auditService.log({
        action: "escrow.refund",
        entity: `escrow:${req.params.id}`,
        actorId: req.user!.userId,
        snapshot: { transactionId: transaction.id, amount: totalAmount },
      });

      res.json({ 
        success: true, 
        message: "Refund processed successfully",
        transaction,
      });
    } catch (error) {
      console.error("Refund error:", error);
      res.status(500).json({ message: "Failed to process refund" });
    }
  });

  /**
   * Get all escrow accounts (admin only)
   */
  app.get("/api/admin/escrow/accounts", authenticate, requireRole("admin"), async (req: AuthRequest, res) => {
    try {
      const allAccounts = await db.query.escrowAccounts.findMany({
        with: {
          buyer: true,
          seller: true,
          assets: true,
          transactions: true,
        },
        orderBy: (accounts, { desc }) => [desc(accounts.createdAt)],
      });

      res.json({ escrowAccounts: allAccounts });
    } catch (error) {
      console.error("Admin get escrow accounts error:", error);
      res.status(500).json({ message: "Failed to retrieve escrow accounts" });
    }
  });
}
