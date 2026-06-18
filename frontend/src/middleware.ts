import { withAuth } from "next-auth/middleware";

export default withAuth({
  callbacks: {
    authorized: ({ token }) => !!token,
  },
  pages: {
    signIn: "/login",
  },
});

export const config = {
  matcher: [
    "/((?!login|signup|verify-email|accept-invite|api/auth|_next/static|_next/image|favicon.ico).*)",
  ],
};
