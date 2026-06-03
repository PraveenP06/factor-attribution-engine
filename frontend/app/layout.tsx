import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import "./globals.css";

const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Praveen Patibandla",
  description: "Software engineer & quant researcher",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${mono.variable} h-full`}>
      <body className="min-h-full bg-[#0f1117] text-slate-200 font-mono antialiased">
        {children}
      </body>
    </html>
  );
}
