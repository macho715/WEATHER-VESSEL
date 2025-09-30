interface LastReport {
  slot: 'am' | 'pm';
  generatedAt: string;
  sent: {
    slack: boolean;
    email: boolean;
  };
}

let lastReport: LastReport | null = null;

export function getLastReport(): LastReport | null {
  return lastReport;
}

export function setLastReport(report: LastReport): void {
  lastReport = report;
}

export function clearLastReport(): void {
  lastReport = null;
}
