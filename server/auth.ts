import { scrypt, randomBytes, timingSafeEqual } from "crypto";
import { promisify } from "util";
import jwt from "jsonwebtoken";
import type { User } from "@shared/schema";

const scryptAsync = promisify(scrypt);

const JWT_SECRET = process.env.JWT_SECRET || (() => {
  console.warn("⚠️  JWT_SECRET not set, using default (NOT FOR PRODUCTION!)");
  return "dev-secret-change-in-production";
})();

const JWT_EXPIRES_IN = "24h";
const REFRESH_TOKEN_EXPIRES_IN = "7d";

export interface JWTPayload {
  userId: string;
  email: string;
  role: string;
}

/**
 * Hash a password using scrypt with salt
 */
export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16).toString("hex");
  const derivedKey = (await scryptAsync(password, salt, 64)) as Buffer;
  return `${salt}:${derivedKey.toString("hex")}`;
}

/**
 * Verify a password against its hash
 */
export async function verifyPassword(
  password: string,
  hashedPassword: string
): Promise<boolean> {
  try {
    const [salt, key] = hashedPassword.split(":");
    const keyBuffer = Buffer.from(key, "hex");
    const derivedKey = (await scryptAsync(password, salt, 64)) as Buffer;
    return timingSafeEqual(keyBuffer, derivedKey);
  } catch (error) {
    return false;
  }
}

/**
 * Generate JWT access token
 */
export function generateAccessToken(user: Pick<User, "id" | "email" | "role">): string {
  const payload: JWTPayload = {
    userId: user.id,
    email: user.email,
    role: user.role,
  };
  
  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: JWT_EXPIRES_IN,
    issuer: "escrow-platform",
    audience: "escrow-api",
  });
}

/**
 * Generate refresh token
 */
export function generateRefreshToken(userId: string): string {
  return jwt.sign(
    { userId, type: "refresh" },
    JWT_SECRET,
    {
      expiresIn: REFRESH_TOKEN_EXPIRES_IN,
      issuer: "escrow-platform",
    }
  );
}

/**
 * Verify and decode JWT token
 */
export function verifyToken(token: string): JWTPayload {
  try {
    const decoded = jwt.verify(token, JWT_SECRET, {
      issuer: "escrow-platform",
      audience: "escrow-api",
    }) as JWTPayload;
    return decoded;
  } catch (error) {
    throw new Error("Invalid or expired token");
  }
}

/**
 * Generate a secure random token for email verification, password reset, etc.
 */
export function generateSecureToken(): string {
  return randomBytes(32).toString("hex");
}

/**
 * Sanitize user object for API response (remove sensitive data)
 */
export function sanitizeUser(user: User) {
  const { passwordHash, twoFactorSecret, ...safeUser } = user;
  return safeUser;
}
