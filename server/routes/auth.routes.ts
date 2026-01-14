import type { Express } from "express";
import type { AuthRequest } from "../middleware/auth.middleware";
import { db } from "../db";
import { users } from "@shared/schema";
import { insertUserSchema, loginSchema } from "@shared/schema";
import { hashPassword, verifyPassword, generateAccessToken, generateRefreshToken, sanitizeUser } from "../auth";
import { auditService } from "../services/audit.service";
import { authLimiter } from "../middleware/security.middleware";
import { eq } from "drizzle-orm";
import { ZodError } from "zod";

export function registerAuthRoutes(app: Express) {
  /**
   * Register a new user
   */
  app.post("/api/auth/register", authLimiter, async (req, res) => {
    try {
      // Validate input
      const validatedData = insertUserSchema.parse(req.body);
      
      // Check if user already exists
      const existingUser = await db.query.users.findFirst({
        where: eq(users.email, validatedData.email),
      });

      if (existingUser) {
        return res.status(409).json({ 
          message: "User with this email already exists" 
        });
      }

      // Hash password
      const passwordHash = await hashPassword(validatedData.passwordHash);

      // Create user
      const [newUser] = await db.insert(users).values({
        ...validatedData,
        passwordHash,
        status: "pending_verification",
      }).returning();

      // Log audit trail
      await auditService.log({
        action: "user.register",
        entity: `user:${newUser.id}`,
        actorId: newUser.id,
        snapshot: { email: newUser.email, role: newUser.role },
      });

      // Generate tokens
      const accessToken = generateAccessToken(newUser);
      const refreshToken = generateRefreshToken(newUser.id);

      res.status(201).json({
        success: true,
        user: sanitizeUser(newUser),
        accessToken,
        refreshToken,
      });
    } catch (error) {
      if (error instanceof ZodError) {
        return res.status(400).json({
          message: "Validation error",
          errors: error.errors,
        });
      }
      console.error("Registration error:", error);
      res.status(500).json({ message: "Failed to register user" });
    }
  });

  /**
   * Login
   */
  app.post("/api/auth/login", authLimiter, async (req, res) => {
    try {
      const validatedData = loginSchema.parse(req.body);

      // Find user
      const user = await db.query.users.findFirst({
        where: eq(users.email, validatedData.email),
      });

      if (!user) {
        return res.status(401).json({ message: "Invalid credentials" });
      }

      // Verify password
      const isValidPassword = await verifyPassword(
        validatedData.password,
        user.passwordHash
      );

      if (!isValidPassword) {
        return res.status(401).json({ message: "Invalid credentials" });
      }

      // Check if account is active
      if (user.status === "suspended" || user.status === "deactivated") {
        return res.status(403).json({ 
          message: "Account is not active",
          status: user.status,
        });
      }

      // Update last login
      await db.update(users)
        .set({ lastLoginAt: new Date() })
        .where(eq(users.id, user.id));

      // Log audit trail
      await auditService.log({
        action: "user.login",
        entity: `user:${user.id}`,
        actorId: user.id,
      });

      // Generate tokens
      const accessToken = generateAccessToken(user);
      const refreshToken = generateRefreshToken(user.id);

      res.json({
        success: true,
        user: sanitizeUser(user),
        accessToken,
        refreshToken,
      });
    } catch (error) {
      if (error instanceof ZodError) {
        return res.status(400).json({
          message: "Validation error",
          errors: error.errors,
        });
      }
      console.error("Login error:", error);
      res.status(500).json({ message: "Failed to login" });
    }
  });

  /**
   * Get current user
   */
  app.get("/api/auth/me", async (req: AuthRequest, res) => {
    try {
      const authHeader = req.headers.authorization;
      if (!authHeader?.startsWith("Bearer ")) {
        return res.status(401).json({ message: "Authentication required" });
      }

      const token = authHeader.substring(7);
      const { verifyToken } = await import("../auth");
      const payload = verifyToken(token);

      const user = await db.query.users.findFirst({
        where: eq(users.id, payload.userId),
      });

      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }

      res.json({ user: sanitizeUser(user) });
    } catch (error) {
      res.status(401).json({ message: "Invalid or expired token" });
    }
  });

  /**
   * Logout (client-side token removal, server-side audit log)
   */
  app.post("/api/auth/logout", async (req: AuthRequest, res) => {
    try {
      if (req.user) {
        await auditService.log({
          action: "user.logout",
          entity: `user:${req.user.userId}`,
          actorId: req.user.userId,
        });
      }

      res.json({ success: true, message: "Logged out successfully" });
    } catch (error) {
      res.status(500).json({ message: "Failed to logout" });
    }
  });
}
