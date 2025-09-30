interface NotificationResult {
  success: boolean;
  error?: string;
}

export async function sendSlack(message: string): Promise<NotificationResult> {
  const webhookUrl = process.env.SLACK_WEBHOOK_URL;
  
  if (!webhookUrl) {
    return { success: false, error: "SLACK_WEBHOOK_URL not configured" };
  }
  
  try {
    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: message,
        username: "Weather Vessel",
        icon_emoji: ":ship:",
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Slack API error: ${response.status}`);
    }
    
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : "Unknown error" 
    };
  }
}

export async function sendEmail(
  subject: string,
  content: string,
  recipients: string[]
): Promise<NotificationResult> {
  const apiKey = process.env.RESEND_API_KEY;
  const sender = process.env.REPORT_SENDER;
  
  if (!apiKey || !sender) {
    return { success: false, error: "Email configuration missing" };
  }
  
  try {
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: sender,
        to: recipients,
        subject,
        html: content.replace(/\n/g, "<br>"),
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Resend API error: ${error.message || response.statusText}`);
    }
    
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : "Unknown error" 
    };
  }
}
