"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { temToken } from "@/lib/auth";

export function useExigeLogin() {
  const router = useRouter();
  useEffect(() => {
    if (!temToken()) router.push("/login");
  }, [router]);
}
