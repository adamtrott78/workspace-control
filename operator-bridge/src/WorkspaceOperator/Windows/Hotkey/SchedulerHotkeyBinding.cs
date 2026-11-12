namespace WorkspaceControl.OperatorBridge.Windows.Hotkey;

public readonly record struct SchedulerHotkeyBinding(
    uint Modifiers,
    uint VirtualKey,
    string DisplayName)
{
    public const uint ModAlt = 0x0001;
    public const uint ModControl = 0x0002;
    public const uint ModShift = 0x0004;
    public const uint ModWin = 0x0008;

    public static SchedulerHotkeyBinding Default =>
        new(ModControl, 0x20, "Ctrl+Space");

    public static SchedulerHotkeyBinding Parse(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return Default;
        }

        uint modifiers = 0;
        string? keyToken = null;

        foreach (var rawToken in value.Split(
                     '+',
                     StringSplitOptions.RemoveEmptyEntries |
                     StringSplitOptions.TrimEntries))
        {
            var token = rawToken.ToUpperInvariant();
            switch (token)
            {
                case "CTRL":
                case "CONTROL":
                    modifiers |= ModControl;
                    break;
                case "ALT":
                    modifiers |= ModAlt;
                    break;
                case "SHIFT":
                    modifiers |= ModShift;
                    break;
                case "WIN":
                case "WINDOWS":
                    modifiers |= ModWin;
                    break;
                default:
                    if (keyToken is not null)
                    {
                        throw new ArgumentException(
                            "Scheduler hotkey must contain exactly one non-modifier key.");
                    }
                    keyToken = token;
                    break;
            }
        }

        if (modifiers == 0 || keyToken is null)
        {
            throw new ArgumentException(
                "Scheduler hotkey requires at least one modifier and one key.");
        }

        var (virtualKey, displayKey) = ParseKey(keyToken);
        var displayParts = new List<string>();
        if ((modifiers & ModControl) != 0) displayParts.Add("Ctrl");
        if ((modifiers & ModAlt) != 0) displayParts.Add("Alt");
        if ((modifiers & ModShift) != 0) displayParts.Add("Shift");
        if ((modifiers & ModWin) != 0) displayParts.Add("Win");
        displayParts.Add(displayKey);

        return new SchedulerHotkeyBinding(
            modifiers,
            virtualKey,
            string.Join("+", displayParts));
    }

    private static (uint VirtualKey, string DisplayKey) ParseKey(string token)
    {
        if (token.Length == 1)
        {
            var ch = token[0];
            if ((ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9'))
            {
                return ((uint)ch, token);
            }
        }

        if (token == "SPACE")
        {
            return (0x20, "Space");
        }

        if (token.StartsWith('F') &&
            int.TryParse(token[1..], out var functionKey) &&
            functionKey is >= 1 and <= 24)
        {
            return ((uint)(0x70 + functionKey - 1), $"F{functionKey}");
        }

        throw new ArgumentException(
            $"Unsupported scheduler hotkey key '{token}'.");
    }
}
