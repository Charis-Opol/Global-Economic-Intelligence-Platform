import { LogOut, Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/use-auth";
import { useTheme } from "@/hooks/use-theme";

export function SettingsPage() {
  const { username, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="max-w-xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>Signed in via the backend's simple JWT auth (Day 2, Step 7).</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground">Username</Label>
            <p className="text-sm font-medium">{username}</p>
          </div>
          <Separator />
          <Button variant="destructive" onClick={logout} className="w-full sm:w-auto">
            <LogOut className="h-4 w-4" />
            Log out
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Persisted locally in this browser.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={toggleTheme} className="w-full sm:w-auto">
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            Switch to {theme === "dark" ? "light" : "dark"} mode
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Environment</CardTitle>
          <CardDescription>Where this frontend is pointed.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">API base URL</span>
            <span className="font-mono">{import.meta.env.VITE_API_BASE_URL}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Superset domain</span>
            <span className="font-mono">{import.meta.env.VITE_SUPERSET_DOMAIN}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
