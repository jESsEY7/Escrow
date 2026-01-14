import { db } from "../db";
import { auditLogs } from "@shared/schema";

export type AuditAction = 
  | "user.register"
  | "user.login"
  | "user.logout"
  | "user.update"
  | "escrow.create"
  | "escrow.fund"
  | "escrow.release"
  | "escrow.refund"
  | "escrow.cancel"
  | "dispute.create"
  | "dispute.resolve"
  | "transaction.create"
  | "transaction.complete"
  | "verification.submit"
  | "verification.approve"
  | "verification.reject";

export interface AuditLogEntry {
  action: AuditAction;
  entity: string;
  actorId?: string;
  snapshot?: any;
}

/**
 * Service for audit logging - critical for financial compliance
 */
export class AuditService {
  /**
   * Log an action to the audit trail
   */
  async log(entry: AuditLogEntry): Promise<void> {
    try {
      await db.insert(auditLogs).values({
        action: entry.action,
        entity: entry.entity,
        actorId: entry.actorId,
        snapshot: entry.snapshot ? JSON.stringify(entry.snapshot) : undefined,
      });

      // Also log to console for real-time monitoring
      console.log(`[AUDIT] ${entry.action} on ${entry.entity} by ${entry.actorId || 'system'}`);
    } catch (error) {
      // Critical: audit logging failures should be escalated
      console.error("❌ CRITICAL: Audit log failed:", error);
      // In production, this should trigger alerts
    }
  }

  /**
   * Log multiple actions in a transaction
   */
  async logBatch(entries: AuditLogEntry[]): Promise<void> {
    try {
      const values = entries.map(entry => ({
        action: entry.action,
        entity: entry.entity,
        actorId: entry.actorId,
        snapshot: entry.snapshot ? JSON.stringify(entry.snapshot) : undefined,
      }));

      await db.insert(auditLogs).values(values);

      console.log(`[AUDIT] Logged ${entries.length} actions`);
    } catch (error) {
      console.error("❌ CRITICAL: Batch audit log failed:", error);
    }
  }

  /**
   * Query audit logs for a specific entity
   */
  async getLogsForEntity(entity: string, limit = 100) {
    return db.query.auditLogs.findMany({
      where: (logs, { eq }) => eq(logs.entity, entity),
      orderBy: (logs, { desc }) => [desc(logs.timestamp)],
      limit,
    });
  }

  /**
   * Query audit logs for a specific actor
   */
  async getLogsForActor(actorId: string, limit = 100) {
    return db.query.auditLogs.findMany({
      where: (logs, { eq }) => eq(logs.actorId, actorId),
      orderBy: (logs, { desc }) => [desc(logs.timestamp)],
      limit,
    });
  }
}

export const auditService = new AuditService();
