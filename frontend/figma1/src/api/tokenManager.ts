/**
 * Token Manager - Manages access token in memory only
 * 
 * SECURITY:
 * - Access token is stored ONLY in memory (not localStorage/sessionStorage)
 * - Refresh token is stored in HttpOnly cookie by server
 * - Frontend NEVER reads or writes refresh token
 */

class TokenManager {
  private accessToken: string | null = null;
  private refreshPromise: Promise<string | null> | null = null;

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Set access token (called after successful login or refresh)
   */
  setAccessToken(token: string): void {
    this.accessToken = token;
  }

  /**
   * Clear access token (called on logout)
   */
  clearAccessToken(): void {
    this.accessToken = null;
  }

  /**
   * Check if user is authenticated (has valid access token)
   */
  isAuthenticated(): boolean {
    return this.accessToken !== null;
  }

  /**
   * Get or create refresh promise
   * This ensures only ONE refresh request is in flight at a time
   */
  getRefreshPromise(): Promise<string | null> | null {
    return this.refreshPromise;
  }

  /**
   * Set refresh promise (called when refresh starts)
   */
  setRefreshPromise(promise: Promise<string | null>): void {
    this.refreshPromise = promise;
  }

  /**
   * Clear refresh promise (called when refresh completes)
   */
  clearRefreshPromise(): void {
    this.refreshPromise = null;
  }
}

// Singleton instance
export const tokenManager = new TokenManager();
