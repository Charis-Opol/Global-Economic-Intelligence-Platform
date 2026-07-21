/** Decodes a JWT payload for display only (e.g. showing the username) -
 * never used to trust the token's contents. The backend is the only thing
 * that verifies a JWT's signature and expiry. */
export function decodeJwtPayload(token: string): { sub?: string; exp?: number } | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = payload.padEnd(payload.length + ((4 - (payload.length % 4)) % 4), "=");
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

export function isJwtExpired(token: string): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload?.exp) return true;
  return Date.now() >= payload.exp * 1000;
}
