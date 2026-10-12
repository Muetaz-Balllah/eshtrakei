export function passwordIsStrong(value: string) {
  return value.length >= 8 && value.length <= 128 && /\p{L}/u.test(value) && /\d/.test(value);
}
