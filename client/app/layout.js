import "./globals.css";
import AuthProvider from "@/components/AuthProvider";
import Nav from "@/components/Nav";

export const metadata = {
  title: "Electricity Usage Tracker",
  description: "Track meter readings, usage and bills.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Nav />
          <main>{children}</main>
          <footer className="footer">UWERA ANNET · 223012758</footer>
        </AuthProvider>
      </body>
    </html>
  );
}
