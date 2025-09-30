import cron from "node-cron";
import fs from "fs";
import path from "path";

const REPORT_ENDPOINT = process.env.REPORT_ENDPOINT || "http://localhost:3000/api/report";
const REPORT_TIMEZONE = process.env.REPORT_TIMEZONE || "Asia/Dubai";
const REPORT_LOCK_PATH = process.env.REPORT_LOCK_PATH || ".report.lock";

interface ReportResult {
  ok: boolean;
  sent: {
    slack: boolean;
    email: boolean;
  };
  slot: string;
  generatedAt: string;
  message?: string;
}

async function sendReport(slot: "am" | "pm"): Promise<void> {
  const lockFile = path.resolve(REPORT_LOCK_PATH);
  
  // Check if lock file exists and is recent (within 1 hour)
  if (fs.existsSync(lockFile)) {
    const stats = fs.statSync(lockFile);
    const now = Date.now();
    const lockAge = now - stats.mtime.getTime();
    
    if (lockAge < 60 * 60 * 1000) { // 1 hour
      console.log(`[scheduler] Report already sent recently for ${slot} slot, skipping...`);
      return;
    }
  }

  try {
    console.log(`[scheduler] Sending ${slot} report...`);
    
    const response = await fetch(`${REPORT_ENDPOINT}?slot=${slot}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: ReportResult = await response.json();
    
    if (result.ok) {
      console.log(`[scheduler] ${slot.toUpperCase()} report sent successfully:`, {
        slack: result.sent.slack,
        email: result.sent.email,
        generatedAt: result.generatedAt,
      });
      
      // Create lock file
      fs.writeFileSync(lockFile, JSON.stringify({
        slot,
        sentAt: new Date().toISOString(),
        result,
      }));
    } else {
      console.error(`[scheduler] Failed to send ${slot} report:`, result);
    }
    
  } catch (error) {
    console.error(`[scheduler] Error sending ${slot} report:`, error);
  }
}

// Schedule reports for Asia/Dubai timezone
// 06:00 Asia/Dubai = 02:00 UTC
// 17:00 Asia/Dubai = 13:00 UTC
cron.schedule("0 2 * * *", () => {
  console.log("[scheduler] Triggering AM report (06:00 Asia/Dubai)");
  sendReport("am");
}, {
  timezone: "UTC",
});

cron.schedule("0 13 * * *", () => {
  console.log("[scheduler] Triggering PM report (17:00 Asia/Dubai)");
  sendReport("pm");
}, {
  timezone: "UTC",
});

console.log("[scheduler] Weather Vessel scheduler started");
console.log("[scheduler] AM reports scheduled for 02:00 UTC (06:00 Asia/Dubai)");
console.log("[scheduler] PM reports scheduled for 13:00 UTC (17:00 Asia/Dubai)");
console.log("[scheduler] Press Ctrl+C to stop");

// Keep the process running
process.on("SIGINT", () => {
  console.log("\n[scheduler] Shutting down...");
  process.exit(0);
});
