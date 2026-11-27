using System.Drawing;
using System.Runtime.InteropServices;

namespace WorkspaceControl.OperatorBridge.Windows;

public static class WorkloadTrayIconFactory
{
    public static Icon Create(WorkloadStatusPresentation presentation)
    {
        ArgumentNullException.ThrowIfNull(presentation);

        using var bitmap = new Bitmap(32, 32);
        using var graphics = Graphics.FromImage(bitmap);
        graphics.Clear(Color.Transparent);
        graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;

        using var background = new SolidBrush(SystemColors.Highlight);
        using var foreground = new SolidBrush(SystemColors.HighlightText);
        graphics.FillEllipse(background, 1, 1, 30, 30);

        var fontSize = presentation.IconText.Length switch
        {
            <= 1 => 18f,
            2 => 14f,
            _ => 9f
        };
        var fontFamily =
            SystemFonts.MessageBoxFont?.FontFamily ??
            FontFamily.GenericSansSerif;
        using var font = new Font(
            fontFamily,
            fontSize,
            FontStyle.Bold,
            GraphicsUnit.Pixel);

        var measured = graphics.MeasureString(presentation.IconText, font);
        graphics.DrawString(
            presentation.IconText,
            font,
            foreground,
            (32f - measured.Width) / 2f,
            (32f - measured.Height) / 2f);

        var handle = bitmap.GetHicon();
        try
        {
            using var temporary = Icon.FromHandle(handle);
            return (Icon)temporary.Clone();
        }
        finally
        {
            DestroyIcon(handle);
        }
    }

    [DllImport("user32.dll")]
    private static extern bool DestroyIcon(nint hIcon);
}
