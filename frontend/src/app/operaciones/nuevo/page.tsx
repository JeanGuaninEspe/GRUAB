"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

export default function NuevoOperacionesRedirectPage() {
  const router = useRouter();

  React.useEffect(() => {
    router.replace("/operaciones/nuevo/ambulancia");
  }, [router]);

  return null;
}
