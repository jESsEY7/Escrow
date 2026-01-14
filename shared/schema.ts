import { pgTable, text, serial, integer, boolean, timestamp, decimal, uuid, pgEnum, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema, createSelectSchema } from "drizzle-zod";
import { z } from "zod";
import { relations } from "drizzle-orm";

// Enums
export const userRoleEnum = pgEnum("user_role", ["buyer", "seller", "admin", "arbitrator"]);
export const userStatusEnum = pgEnum("user_status", ["active", "suspended", "pending_verification", "deactivated"]);
export const escrowStatusEnum = pgEnum("escrow_status", ["pending", "funded", "in_progress", "in_dispute", "completed", "cancelled", "refunded"]);
export const transactionStatusEnum = pgEnum("transaction_status", ["pending", "completed", "failed", "reversed"]);
export const disputeStatusEnum = pgEnum("dispute_status", ["open", "under_review", "resolved", "escalated"]);
export const verificationStatusEnum = pgEnum("verification_status", ["pending", "approved", "rejected"]);

// Users Table
export const users = pgTable("users", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text("email").notNull().unique(),
  passwordHash: text("password_hash").notNull(),
  role: userRoleEnum("role").notNull().default("buyer"),
  status: userStatusEnum("status").notNull().default("pending_verification"),
  identityData: jsonb("identity_data"), // KYC data (encrypted)
  contactData: jsonb("contact_data"),
  twoFactorSecret: text("two_factor_secret"),
  twoFactorEnabled: boolean("two_factor_enabled").default(false),
  lastLoginAt: timestamp("last_login_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

// Escrow Accounts Table
export const escrowAccounts = pgTable("escrow_accounts", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  buyerId: text("buyer_id").notNull().references(() => users.id),
  sellerId: text("seller_id").notNull().references(() => users.id),
  status: escrowStatusEnum("status").notNull().default("pending"),
  linkedTransactionId: text("linked_transaction_id"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Assets Table (what's being held in escrow)
export const assets = pgTable("assets", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  escrowAccountId: text("escrow_account_id").notNull().references(() => escrowAccounts.id),
  assetId: text("asset_id").notNull(), // external asset identifier
  amount: decimal("amount", { precision: 20, scale: 2 }).notNull(),
  currency: text("currency").notNull().default("USD"),
  initiatedAt: timestamp("initiated_at").defaultNow().notNull(),
  status: text("status").notNull().default("held"),
  metadata: jsonb("metadata"), // additional asset details
  type: text("type").notNull(), // e.g., "fiat", "crypto", "property", "domain"
});

// Transactions Table
export const transactions = pgTable("transactions", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  escrowAccountId: text("escrow_account_id").notNull().references(() => escrowAccounts.id),
  assetId: text("asset_id").references(() => assets.id),
  type: text("type").notNull(), // "deposit", "release", "refund"
  amount: decimal("amount", { precision: 20, scale: 2 }).notNull(),
  currency: text("currency").notNull().default("USD"),
  status: transactionStatusEnum("status").notNull().default("pending"),
  paymentMethod: text("payment_method"),
  externalTransactionId: text("external_transaction_id"),
  initiatedBy: text("initiated_by").notNull().references(() => users.id),
  completedAt: timestamp("completed_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Disputes Table
export const disputes = pgTable("disputes", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  escrowAccountId: text("escrow_account_id").notNull().references(() => escrowAccounts.id),
  reason: text("reason").notNull(),
  status: disputeStatusEnum("status").notNull().default("open"),
  raisedBy: text("raised_by").notNull().references(() => users.id),
  resolutionNotes: text("resolution_notes"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  resolvedAt: timestamp("resolved_at"),
});

// Verification Records (KYC/AML)
export const verificationRecords = pgTable("verification_records", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  escrowAccountId: text("escrow_account_id").notNull().references(() => escrowAccounts.id),
  submittedBy: text("submitted_by").notNull().references(() => users.id),
  documentType: text("document_type").notNull(),
  result: verificationStatusEnum("result").notNull().default("pending"),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
});

// Payouts Table
export const payouts = pgTable("payouts", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  escrowAccountId: text("escrow_account_id").notNull().references(() => escrowAccounts.id),
  recipientId: text("recipient_id").notNull().references(() => users.id),
  amount: decimal("amount", { precision: 20, scale: 2 }).notNull(),
  method: text("method").notNull(),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
});

// Audit Logs Table
export const auditLogs = pgTable("audit_logs", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  action: text("action").notNull(),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
  snapshot: text("snapshot"),
  entity: text("entity").notNull(),
  actorId: text("actor_id").references(() => users.id),
});

// Contacts Table (for marketing/support)
export const contacts = pgTable("contacts", {
  id: serial("id").primaryKey(),
  firstName: text("first_name").notNull(),
  lastName: text("last_name").notNull(),
  email: text("email").notNull(),
  transactionType: text("transaction_type"),
  transactionValue: text("transaction_value"),
  message: text("message"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Relations
export const usersRelations = relations(users, ({ many }) => ({
  escrowAccountsAsBuyer: many(escrowAccounts, { relationName: "buyer" }),
  escrowAccountsAsSeller: many(escrowAccounts, { relationName: "seller" }),
  transactions: many(transactions),
  disputes: many(disputes),
}));

export const escrowAccountsRelations = relations(escrowAccounts, ({ one, many }) => ({
  buyer: one(users, { fields: [escrowAccounts.buyerId], references: [users.id], relationName: "buyer" }),
  seller: one(users, { fields: [escrowAccounts.sellerId], references: [users.id], relationName: "seller" }),
  assets: many(assets),
  transactions: many(transactions),
  disputes: many(disputes),
}));

// Zod Schemas for Validation
export const insertUserSchema = createInsertSchema(users, {
  email: z.string().email("Invalid email address"),
  passwordHash: z.string().min(8, "Password must be at least 8 characters"),
  role: z.enum(["buyer", "seller", "admin", "arbitrator"]).optional(),
}).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
  lastLoginAt: true,
});

export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
  twoFactorCode: z.string().optional(),
});

export const insertEscrowAccountSchema = createInsertSchema(escrowAccounts).omit({
  id: true,
  createdAt: true,
});

export const insertAssetSchema = createInsertSchema(assets, {
  amount: z.string().regex(/^\d+(\.\d{1,2})?$/, "Invalid amount format"),
}).omit({
  id: true,
  initiatedAt: true,
});

export const insertTransactionSchema = createInsertSchema(transactions, {
  amount: z.string().regex(/^\d+(\.\d{1,2})?$/, "Invalid amount format"),
}).omit({
  id: true,
  createdAt: true,
  completedAt: true,
});

export const insertDisputeSchema = createInsertSchema(disputes).omit({
  id: true,
  createdAt: true,
  resolvedAt: true,
});

export const insertContactSchema = createInsertSchema(contacts).omit({
  id: true,
  createdAt: true,
});

// Export Types
export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;
export type LoginCredentials = z.infer<typeof loginSchema>;

export type EscrowAccount = typeof escrowAccounts.$inferSelect;
export type InsertEscrowAccount = z.infer<typeof insertEscrowAccountSchema>;

export type Asset = typeof assets.$inferSelect;
export type InsertAsset = z.infer<typeof insertAssetSchema>;

export type Transaction = typeof transactions.$inferSelect;
export type InsertTransaction = z.infer<typeof insertTransactionSchema>;

export type Dispute = typeof disputes.$inferSelect;
export type InsertDispute = z.infer<typeof insertDisputeSchema>;

export type Contact = typeof contacts.$inferSelect;
export type InsertContact = z.infer<typeof insertContactSchema>;
