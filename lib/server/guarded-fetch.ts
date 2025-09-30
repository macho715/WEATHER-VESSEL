export class GuardedFetchError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = "GuardedFetchError";
  }
}

interface GuardedFetchOptions {
  key: string;
  timeoutMs: number;
  retries: number;
  backoffMs: number;
  backoffFactor: number;
  circuitBreakerThreshold: number;
  circuitBreakerCooldownMs: number;
}

const circuitBreakerState = new Map<string, {
  failures: number;
  lastFailure: number;
  state: 'closed' | 'open' | 'half-open';
}>();

export async function guardedFetch(
  url: string,
  options: GuardedFetchOptions
): Promise<Response> {
  const { key, timeoutMs, retries, backoffMs, backoffFactor, circuitBreakerThreshold, circuitBreakerCooldownMs } = options;
  
  const breaker = circuitBreakerState.get(key) || { failures: 0, lastFailure: 0, state: 'closed' as const };
  
  // Check circuit breaker
  if (breaker.state === 'open') {
    if (Date.now() - breaker.lastFailure < circuitBreakerCooldownMs) {
      throw new GuardedFetchError(`Circuit breaker open for ${key}`);
    }
    breaker.state = 'half-open';
  }
  
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      
      const response = await fetch(url, {
        signal: controller.signal,
      });
      
      clearTimeout(timeout);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Reset circuit breaker on success
      breaker.failures = 0;
      breaker.state = 'closed';
      circuitBreakerState.set(key, breaker);
      
      return response;
      
    } catch (error) {
      lastError = error as Error;
      breaker.failures++;
      breaker.lastFailure = Date.now();
      
      if (breaker.failures >= circuitBreakerThreshold) {
        breaker.state = 'open';
      }
      
      circuitBreakerState.set(key, breaker);
      
      if (attempt < retries) {
        const delay = backoffMs * Math.pow(backoffFactor, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw new GuardedFetchError(
    `Failed to fetch ${url} after ${retries + 1} attempts`,
    lastError
  );
}
