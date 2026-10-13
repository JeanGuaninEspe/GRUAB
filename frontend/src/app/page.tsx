"use client";

import * as React from "react";
import { LoginView } from "@/components/auth/login-view";
import { useAuth } from "@/context/auth-context";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  return <LoginView />;
}
