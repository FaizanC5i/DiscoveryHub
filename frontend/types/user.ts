/** The signed-in user, as the backend returns it from /api/auth/me. Never contains a password. */
export interface User {
  id: number;
  name: string;
  email: string;
}
