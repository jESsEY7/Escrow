import 'dotenv/config';
import express, { type Request, Response, NextFunction } from "express";
import cors from "cors";
import { registerRoutes } from "./routes";
import { setupVite, serveStatic, log } from "./vite";
import { testConnection } from "./db";
import { 
  securityHeaders, 
  sanitizeInput, 
  corsOptions, 
  requestLogger,
  validateContentType,
  sanitizeError,
} from "./middleware/security.middleware";

const app = express();

// Security middleware (apply before other middleware)
app.use(securityHeaders);
app.use(cors(corsOptions));
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: false, limit: "10mb" }));
app.use(sanitizeInput);
app.use(requestLogger);
app.use(validateContentType);

// Request logging middleware
app.use((req, res, next) => {
  const start = Date.now();
  const path = req.path;
  let capturedJsonResponse: Record<string, any> | undefined = undefined;

  const originalResJson = res.json;
  res.json = function (bodyJson, ...args) {
    capturedJsonResponse = bodyJson;
    return originalResJson.apply(res, [bodyJson, ...args]);
  };

  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path.startsWith("/api")) {
      let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
      if (capturedJsonResponse) {
        logLine += ` :: ${JSON.stringify(capturedJsonResponse)}`;
      }

      if (logLine.length > 80) {
        logLine = logLine.slice(0, 79) + "…";
      }

      log(logLine);
    }
  });

  next();
});

(async () => {
  // Test database connection
  log("Testing database connection...");
  const dbConnected = await testConnection();
  
  if (!dbConnected) {
    log("⚠️  Database connection failed - some features may not work");
  }

  const server = await registerRoutes(app);

  // Global error handler
  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const sanitized = sanitizeError(err);

    log(`Error: ${status} - ${err.message}`);
    
    res.status(status).json(sanitized);
  });

  // importantly only setup vite in development and after
  // setting up all the other routes so the catch-all route
  // doesn't interfere with the other routes
  if (app.get("env") === "development") {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }

  // ALWAYS serve the app on port 5000
  // this serves both the API and the client.
  const port = 5000;
  server.listen(port, () => {
    log(`🚀 Server running on port ${port}`);
    log(`📝 Environment: ${process.env.NODE_ENV || 'development'}`);
    log(`🔒 Security features enabled`);
    log(`📊 Database: ${dbConnected ? 'Connected' : 'Disconnected'}`);
  });
})();
