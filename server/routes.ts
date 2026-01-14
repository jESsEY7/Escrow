import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertContactSchema } from "@shared/schema";
import { ZodError } from "zod";
import { registerAuthRoutes } from "./routes/auth.routes";
import { registerEscrowRoutes } from "./routes/escrow.routes";
import { registerDisputeRoutes } from "./routes/dispute.routes";
import { generalLimiter } from "./middleware/security.middleware";

export async function registerRoutes(app: Express): Promise<Server> {
  // Register authentication routes
  registerAuthRoutes(app);
  
  // Register escrow routes
  registerEscrowRoutes(app);
  
  // Register dispute routes
  registerDisputeRoutes(app);

  // Contact form submission endpoint (public)
  app.post("/api/contact", generalLimiter, async (req, res) => {
    try {
      const validatedData = insertContactSchema.parse(req.body);
      const contact = await storage.createContact(validatedData);
      res.json({ success: true, contact });
    } catch (error) {
      if (error instanceof ZodError) {
        res.status(400).json({ 
          message: "Validation error", 
          errors: error.errors 
        });
      } else {
        res.status(500).json({ 
          message: "Failed to submit contact form" 
        });
      }
    }
  });

  // Get all contacts (for admin purposes)
  app.get("/api/contacts", async (req, res) => {
    try {
      const contacts = await storage.getContacts();
      res.json(contacts);
    } catch (error) {
      res.status(500).json({ 
        message: "Failed to retrieve contacts" 
      });
    }
  });

  // Health check endpoint
  app.get("/api/health", (req, res) => {
    res.json({ 
      status: "healthy", 
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || "development",
    });
  });

  const httpServer = createServer(app);
  return httpServer;
}
