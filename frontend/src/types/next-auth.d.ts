import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    user: {
      name?: string | null;
      email?: string | null;
      image?: string | null;
      isEmailVerified?: boolean;
      role?: string;
    };
  }

  interface User {
    accessToken?: string;
    refreshToken?: string;
    isEmailVerified?: boolean;
    role?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    isEmailVerified?: boolean;
    role?: string;
  }
}
