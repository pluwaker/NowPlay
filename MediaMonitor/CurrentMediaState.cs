using System;

namespace NowMediaMonitor
{
    public class CurrentMediaState
    {
        public string Artist { get; set; } = "Не воспроизводится";
        public string Title { get; set; } = "Нет данных";

        public double Position { get; set; } = 0;
        public double Duration { get; set; } = 0;

        public bool IsPlaying { get; set; } = false;

        public int CoverVersion { get; set; } = 1;
        public string CoverPath { get; set; } = "cover.png";
        public string SourceId { get; set; } = "";

        public string Status => Artist == "Не воспроизводится" ? "inactive" : "active";

        public void Print()
        {
            Console.WriteLine($"🎵 {Artist} — {Title}");
            Console.WriteLine($"⏱ {Position:F1}/{Duration:F1}");
            Console.WriteLine($"▶ {(IsPlaying ? "Playing" : "Paused")}");
            Console.WriteLine($"🖼 Cover v{CoverVersion} → {CoverPath}");
            Console.WriteLine();
        }
    }
}
