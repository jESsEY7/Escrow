import type { Express } from "express";
import type { AuthRequest } from "../middleware/auth.middleware";
import { authenticate, requireRole, requireVerified } from "../middleware/auth.middleware";
import { db } from "../db";
import { disputes, escrowAccounts } from "@shared/schema";
import { insertDisputeSchema } from "@shared/schema";
import { auditService } from "../services/audit.service";
import { eq, or } from "drizzle-orm";
import { ZodError } from "zod";

export function registerDisputeRoutes(app: Express) {
  /**
   * Create a dispute
   */
  app.post("/api/disputes", authenticate, requireVerified, async (req: AuthRequest, res) => {
    try {
      const validatedData = insertDisputeSchema.parse({
        ...req.body,
        raisedBy: req.user!.userId,
      });

      // Verify escrow account exists and user is involved
      const escrowAccount = await db.query.escrowAccounts.findFirst({
        where: eq(escrowAccounts.id, validatedData.escrowAccountId),
      });

      if (!escrowAccount) {
        return res.status(404).json({ message: "Escrow account not found" });
      }

      const isInvolved = 
        escrowAccount.buyerId === req.user!.userId ||
        escrowAccount.sellerId === req.user!.userId;

      if (!isInvolved) {
        return res.status(403).json({ 
          message: "Only parties involved in the escrow can create disputes" 
        });
      }

      // Create dispute
      const [newDispute] = await db.insert(disputes)
        .values(validatedData)
        .returning();

      // Update escrow status to in_dispute
      await db.update(escrowAccounts)
        .set({ status: "in_dispute" })
        .where(eq(escrowAccounts.id, validatedData.escrowAccountId));

      // Audit log
      await auditService.log({
        action: "dispute.create",
        entity: `dispute:${newDispute.id}`,
        actorId: req.user!.userId,
        snapshot: newDispute,
      });

      res.status(201).json({
        success: true,
        dispute: newDispute,
      });
    } catch (error) {
      if (error instanceof ZodError) {
        return res.status(400).json({ message: "Validation error", errors: error.errors });
      }
      console.error("Create dispute error:", error);
      res.status(500).json({ message: "Failed to create dispute" });
    }
  });

  /**
   * Get dispute by ID
   */
  app.get("/api/disputes/:id", authenticate, async (req: AuthRequest, res) => {
    try {
      const dispute = await db.query.disputes.findFirst({
        where: eq(disputes.id, req.params.id),
        with: {
          escrowAccount: {
            with: {
              buyer: true,
              seller: true,
            },
          },
        },
      });

      if (!dispute) {
        return res.status(404).json({ message: "Dispute not found" });
      }

      // Authorization check
      const isAuthorized = 
        dispute.escrowAccount.buyerId === req.user!.userId ||
        dispute.escrowAccount.sellerId === req.user!.userId ||
        req.user!.role === "admin" ||
        req.user!.role === "arbitrator";

      if (!isAuthorized) {
        return res.status(403).json({ message: "Unauthorized access" });
      }

      res.json({ dispute });
    } catch (error) {
      console.error("Get dispute error:", error);
      res.status(500).json({ message: "Failed to retrieve dispute" });
    }
  });

  /**
   * Get all disputes for current user
   */
  app.get("/api/disputes", authenticate, async (req: AuthRequest, res) => {
    try {
      const userId = req.user!.userId;

      // Get all escrow accounts user is involved in
      const userEscrowAccounts = await db.query.escrowAccounts.findMany({
        where: or(
          eq(escrowAccounts.buyerId, userId),
          eq(escrowAccounts.sellerId, userId)
        ),
      });

      const escrowIds = userEscrowAccounts.map(account => account.id);

      // Get disputes for those escrow accounts
      const userDisputes = await db.query.disputes.findMany({
        where: (d, { inArray }) => inArray(d.escrowAccountId, escrowIds),
        with: {
          escrowAccount: {
            with: {
              buyer: true,
              seller: true,
            },
          },
        },
        orderBy: (d, { desc }) => [desc(d.createdAt)],
      });

      res.json({ disputes: userDisputes });
    } catch (error) {
      console.error("Get disputes error:", error);
      res.status(500).json({ message: "Failed to retrieve disputes" });
    }
  });

  /**
   * Resolve dispute (admin/arbitrator only)
   */
  app.patch("/api/disputes/:id/resolve", authenticate, requireRole("admin", "arbitrator"), async (req: AuthRequest, res) => {
    try {
      const { resolutionNotes } = req.body;

      if (!resolutionNotes) {
        return res.status(400).json({ message: "Resolution notes are required" });
      }

      const dispute = await db.query.disputes.findFirst({
        where: eq(disputes.id, req.params.id),
      });

      if (!dispute) {
        return res.status(404).json({ message: "Dispute not found" });
      }

      if (dispute.status === "resolved") {
        return res.status(400).json({ message: "Dispute already resolved" });
      }

      // Update dispute
      const [updatedDispute] = await db.update(disputes)
        .set({
          status: "resolved",
          resolutionNotes,
          resolvedAt: new Date(),
        })
        .where(eq(disputes.id, req.params.id))
        .returning();

      // Audit log
      await auditService.log({
        action: "dispute.resolve",
        entity: `dispute:${req.params.id}`,
        actorId: req.user!.userId,
        snapshot: { resolutionNotes },
      });

      res.json({
        success: true,
        dispute: updatedDispute,
      });
    } catch (error) {
      console.error("Resolve dispute error:", error);
      res.status(500).json({ message: "Failed to resolve dispute" });
    }
  });

  /**
   * Get all disputes (admin/arbitrator only)
   */
  app.get("/api/admin/disputes", authenticate, requireRole("admin", "arbitrator"), async (req: AuthRequest, res) => {
    try {
      const allDisputes = await db.query.disputes.findMany({
        with: {
          escrowAccount: {
            with: {
              buyer: true,
              seller: true,
            },
          },
        },
        orderBy: (d, { desc }) => [desc(d.createdAt)],
      });

      res.json({ disputes: allDisputes });
    } catch (error) {
      console.error("Admin get disputes error:", error);
      res.status(500).json({ message: "Failed to retrieve disputes" });
    }
  });
}
