export function couponExpired(expiresAt: string) {
  return new Date(expiresAt).getTime() <= Date.now();
}

export function couponExhausted(redemptionCount: number, limit: number | null) {
  return limit !== null && redemptionCount >= limit;
}

export function formatCouponDate(expiresAt: string) {
  return new Date(expiresAt).toLocaleDateString("ar-LY", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "Africa/Tripoli",
  });
}

export function couponExpiryIso(dateValue: string) {
  return new Date(`${dateValue}T23:59:59+02:00`).toISOString();
}
