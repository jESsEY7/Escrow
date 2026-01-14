import { useTheme } from "@/contexts/ThemeContext";
import { Button } from "@/components/ui/button";
import { Moon, Sun, Monitor } from "lucide-react";

export function ThemeSwitcher() {
    const { theme, setTheme } = useTheme();

    return (
        <div className="flex gap-2 p-1 bg-white/5 rounded-lg border border-white/10">
            <Button
                variant={theme === 'nova' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setTheme('nova')}
                className="gap-2"
            >
                <Monitor className="w-4 h-4" />
                Nova
            </Button>
            <Button
                variant={theme === 'maia' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setTheme('maia')}
                className="gap-2"
            >
                <Sun className="w-4 h-4" />
                Maia
            </Button>
            <Button
                variant={theme === 'lyra' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setTheme('lyra')}
                className="gap-2"
            >
                <Moon className="w-4 h-4" />
                Lyra
            </Button>
        </div>
    );
}
