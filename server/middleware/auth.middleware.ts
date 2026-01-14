import type { Request, Response, NextFunction } from "express";
import { verifyToken, type JWTPayload } from "../auth";
import { db } from "../db";
import { users } from "@shared/schema";
import { eq } from "drizzle-orm";

export interface AuthRequest extends Request {
  user?: JWTPayload & { status: string };
}

/**
 * Middleware to authenticate requests using JWT
 */
export async function authenticate(
  req: AuthRequest,
  res: Response,
  next: NextFunction
) {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res.status(401).json({ message: "Authentication required" });
    }

    const token = authHeader.substring(7);
    const payload = verifyToken(token);

    // Verify user still exists and is active
    const [user] = await db
      .select()
      .from(users)
      .where(eq(users.id, payload.userId))
      .limit(1);

    if (!user) {
      return res.status(401).json({ message: "User not found" });
    }

    if (user.status === "suspended" || user.status === "deactivated") {
      return res.status(403).json({ message: "Account is not active" });
    }

    req.user = { ...payload, status: user.status };
    next();
  } catch (error) {
    return res.status(401).json({ message: "Invalid or expired token" });
  }
}

/**
 * Middleware to check if user has specific role
 */
export function requireRole(...roles: string[]) {
  return (req: AuthRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ message: "Authentication required" });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ 
        message: "Insufficient permissions",
        required: roles,
        current: req.user.role,
      });
    }

    next();
  };
}

/**
 * Middleware to verify user is verified (not pending)
 */
export function requireVerified(
  req: AuthRequest,
  res: Response,
  next: NextFunction
) {
  if (!req.user) {
    return res.status(401).json({ message: "Authentication required" });
  }

  if (req.user.status === "pending_verification") {
    return res.status(403).json({ 
      message: "Account verification required",
      status: req.user.status,
    });
  }

  next();
}
